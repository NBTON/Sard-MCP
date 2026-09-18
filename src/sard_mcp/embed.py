"""OpenRouter embeddings with content-hash cache and hard budget caps.

Paid work in this build is embeddings only. Every batch reserves its
worst-case estimated cost before the request and commits the
provider-reported cost after; the key never appears in logs or errors.
Requests run sequentially with bounded retries (deliberately modest
concurrency: correctness and spend control beat throughput here).
"""

from __future__ import annotations

import hashlib
import sqlite3
import time

import httpx
import numpy as np

from . import store
from .chunk import count_tokens
from .config import Settings

PARAMS = "default"
RESERVE_MARGIN = 1.5
RETRIES = 3


class BudgetExceeded(RuntimeError):
    pass


class ProviderError(RuntimeError):
    pass


def estimate_cost_usd(tokens: int, settings: Settings) -> float:
    return tokens / 1_000_000 * settings.price_per_mtok_usd


def _headers(settings: Settings) -> dict:
    key = settings.api_key
    if not key:
        raise ProviderError("OPENROUTER_API_KEY is not set (local .env).")
    return {
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "X-Title": "Sard-MCP",
    }


def embed_texts(settings: Settings, texts: list[str]) -> tuple[list[list[float]], int | None, float | None]:
    """Call the embeddings endpoint. Returns (vectors, prompt_tokens, cost_usd)."""
    last_err: Exception | None = None
    for attempt in range(RETRIES):
        try:
            with httpx.Client(timeout=60.0) as client:
                resp = client.post(
                    f"{settings.openrouter_base}/embeddings",
                    headers=_headers(settings),
                    json={"model": settings.embedding_model, "input": texts},
                )
            if resp.status_code == 200:
                body = resp.json()
                usage = body.get("usage") or {}
                return (
                    [item["embedding"] for item in body["data"]],
                    usage.get("prompt_tokens"),
                    usage.get("cost"),
                )
            last_err = ProviderError(f"HTTP {resp.status_code}: {resp.text[:300]}")
        except ProviderError as exc:
            raise exc
        except Exception as exc:  # noqa: BLE001 - retry then report
            last_err = exc
        time.sleep(2**attempt)
    raise ProviderError(f"embedding request failed after {RETRIES} tries: {last_err}")


def check_budget(conn: sqlite3.Connection, settings: Settings, extra_usd: float = 0.0) -> dict:
    totals = store.spend_totals(conn)
    if totals["committed_usd"] + totals["reserved_usd"] + extra_usd > settings.cumulative_budget_usd:
        raise BudgetExceeded(
            f"cap ${settings.cumulative_budget_usd:.2f} would be exceeded "
            f"(committed ${totals['committed_usd']:.4f}, reserved ${totals['reserved_usd']:.4f})."
        )
    return totals


def ensure_passage_embeddings(
    settings: Settings, conn: sqlite3.Connection, items: list[dict],
    batch_tokens: int = 150_000, max_batch_items: int = 100,
) -> dict:
    """Embed uncached passages. items: [{pid, text, content_hash}]."""
    todo = []
    for item in items:
        cached = store.get_embedding(conn, item["pid"], settings.embedding_model, PARAMS)
        if cached and cached["content_hash"] == item["content_hash"]:
            continue
        todo.append(item)
    stats = {"cached": len(items) - len(todo), "embedded": 0, "tokens_reported": 0, "cost_reported": 0.0}
    if not todo:
        return stats

    batches: list[list[dict]] = []
    cur, cur_tokens = [], 0
    for item in todo:
        tokens = count_tokens(item["text"])
        if cur and (len(cur) >= max_batch_items or cur_tokens + tokens > batch_tokens):
            batches.append(cur)
            cur, cur_tokens = [], 0
        cur.append(item)
        cur_tokens += tokens
    if cur:
        batches.append(cur)

    for batch in batches:
        est_tokens = sum(count_tokens(item["text"]) for item in batch)
        reserve = estimate_cost_usd(est_tokens, settings) * RESERVE_MARGIN
        check_budget(conn, settings, reserve)
        with conn:
            store.log_usage(conn, "reserve", tokens_est=est_tokens, cost_est_usd=reserve,
                            note=f"embed {len(batch)} passages")
        try:
            vectors, rep_tokens, rep_cost = embed_texts(settings, [i["text"] for i in batch])
        except Exception:
            with conn:
                store.log_usage(conn, "release", cost_est_usd=reserve, note="embed failed")
            raise
        if len(vectors) != len(batch):
            with conn:
                store.log_usage(conn, "release", cost_est_usd=reserve, note="short response")
            raise ProviderError(f"expected {len(batch)} vectors, got {len(vectors)}")
        est_cost = estimate_cost_usd(rep_tokens or est_tokens, settings)
        with conn:
            for item, vec in zip(batch, vectors):
                arr = np.asarray(vec, dtype=np.float32)
                store.store_embedding(conn, item["pid"], settings.embedding_model,
                                      arr.shape[0], PARAMS, item["content_hash"], arr)
            store.log_usage(conn, "release", cost_est_usd=reserve, note="embed done")
            store.log_usage(conn, "commit", tokens_est=est_tokens, tokens_reported=rep_tokens,
                            cost_est_usd=est_cost, cost_reported_usd=rep_cost,
                            note=f"embed {len(batch)} passages")
        stats["embedded"] += len(batch)
        stats["tokens_reported"] += rep_tokens or 0
        stats["cost_reported"] += rep_cost or 0.0
    return stats


def embed_query(settings: Settings, conn: sqlite3.Connection, query: str) -> np.ndarray | None:
    """Embed one query with cache; None when no key (keyword-only mode)."""
    qhash = hashlib.sha256(f"{settings.embedding_model}\n{query}".encode("utf-8")).hexdigest()[:32]
    cached = store.get_query_vector(conn, qhash, settings.embedding_model)
    if cached is not None:
        return cached
    if not settings.api_key:
        return None
    est_tokens = count_tokens(query)
    reserve = estimate_cost_usd(est_tokens, settings) * RESERVE_MARGIN
    check_budget(conn, settings, reserve)
    with conn:
        store.log_usage(conn, "reserve", tokens_est=est_tokens, cost_est_usd=reserve, note="query")
    try:
        vectors, rep_tokens, rep_cost = embed_texts(settings, [query])
    except Exception:
        with conn:
            store.log_usage(conn, "release", cost_est_usd=reserve, note="query failed")
        raise
    vec = np.asarray(vectors[0], dtype=np.float32)
    est_cost = estimate_cost_usd(rep_tokens or est_tokens, settings)
    with conn:
        store.store_query_vector(conn, qhash, settings.embedding_model, query, vec)
        store.log_usage(conn, "release", cost_est_usd=reserve, note="query done")
        store.log_usage(conn, "commit", tokens_est=est_tokens, tokens_reported=rep_tokens,
                        cost_est_usd=est_cost, cost_reported_usd=rep_cost, note="query")
    return vec
