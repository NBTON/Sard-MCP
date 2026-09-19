"""Hybrid retrieval: FTS5 keyword + cached-vector cosine, fused with RRF.

Search returns potential evidence, never certified claims. Rank scores are
exposed only as opaque ordering (no similarity-as-certainty). Provider
outages, missing credentials and budget caps degrade to a labelled
keyword-only mode instead of fabricated success.
"""

from __future__ import annotations

import sqlite3

import numpy as np

from . import embed, store
from .config import Settings
from .models import COLLECTION_PROVENANCE, COLLECTION_URL, CoverageInput, PassageInput, SearchInput
from .normalize import english_source_hint, normalize_search, strip_stopwords

MAX_HIT_CHARS = 1500
RRF_K = 60
FTS_POOL = 100
VEC_POOL = 300

_ALIASES: dict[str, list[str]] | None = None


def _aliases() -> dict[str, list[str]]:
    """Curated EN<->AR glossary, normalized at load (data/aliases.json)."""
    global _ALIASES
    if _ALIASES is None:
        import json

        from .config import PROJECT_ROOT

        raw = json.loads((PROJECT_ROOT / "data" / "aliases.json").read_text(encoding="utf-8"))
        _ALIASES = {normalize_search(k): [normalize_search(v) for v in vals]
                    for k, vals in raw.items() if not k.startswith("_")}
    return _ALIASES


def expand_query(query_norm: str) -> tuple[list[str], dict[str, list[str]]]:
    """Return (extra FTS terms, applied map) for whole-term/phrase matches."""
    tokens = set(query_norm.split())
    extra, applied = [], {}
    for key, vals in _aliases().items():
        if (key in tokens) if " " not in key else (key in query_norm):
            applied[key] = vals
            extra.extend(vals)
    return extra, applied


class NotFoundError(ValueError):
    pass


def _display(row: dict) -> tuple[str, str]:
    if row.get("text_reviewed"):
        return row["text_reviewed"], "reviewed_transcription"
    return row["text_raw"], row.get("derivation") or "extracted"


def _filters_met(row: dict, params: SearchInput) -> bool:
    if params.doc_ids and row["doc_id"] not in params.doc_ids:
        return False
    if params.region and (row.get("region") or "").lower() != params.region.lower():
        return False
    if params.topic and (row.get("topic") or "").lower() != params.topic.lower():
        return False
    if params.lang and (row.get("lang") or "") != params.lang:
        return False
    return True


def _hit(conn: sqlite3.Connection, pid: str, settings: Settings, alt: list[str] | None = None) -> dict:
    row = store.passage_by_id(conn, pid)
    assert row is not None
    text, derivation = _display(row)
    truncated = len(text) > MAX_HIT_CHARS
    return {
        "pid": pid,
        "doc_id": row["doc_id"],
        "title": row["title"],
        "filename": row["filename"],
        "publisher": row["publisher"],
        "pdf_page": row["pdf_page"],
        "printed_label": row["printed_label"],
        "region": row["region"],
        "topic": row["topic"],
        "lang": row["lang"],
        "source_url": row["source_url"],
        "source_url_status": row["source_url_status"],
        "collection_url": COLLECTION_URL,
        "collection_provenance": COLLECTION_PROVENANCE,
        "derivation": derivation,
        "text": text[:MAX_HIT_CHARS],
        "text_truncated": truncated,
        "alternate_provenance": alt or [],
        "corpus_revision": settings.corpus_revision,
    }


def search(params: SearchInput, settings: Settings, conn: sqlite3.Connection) -> dict:
    warnings: list[str] = []
    if params.lang is None and english_source_hint(params.query):
        params = params.model_copy(update={"lang": "en"})
        warnings.append("language_hint: query names the English source; filtering to lang=en.")
    query_norm = normalize_search(params.query)

    # Keyword candidates (stopwords stripped: they only match same-language
    # distractors and bury cross-language vector winners in RRF ties).
    # Curated EN<->AR aliases bridge proper nouns across scripts.
    extra_terms, expansions = expand_query(query_norm)
    fts_q = (strip_stopwords(query_norm) + " " + " ".join(extra_terms)).strip()
    fts = store.fts_search(conn, store.escape_fts(fts_q), FTS_POOL)
    fts_rank = {h["pid"]: i for i, h in enumerate(fts)}

    # Vector candidates (cached; degrades cleanly).
    vec_rank: dict[str, int] = {}
    mode = "hybrid"
    if not settings.api_key:
        mode = "keyword_only"
        warnings.append("keyword_only: OPENROUTER_API_KEY is not set; vector search disabled.")
    else:
        try:
            qvec = embed.embed_query(settings, conn, params.query)
            pids, mat = store.vectors_for_model(conn, settings.embedding_model)
            if qvec is None or len(pids) == 0:
                mode = "keyword_only"
                warnings.append("keyword_only: no query vector or no indexed vectors.")
            else:
                sims = mat @ (qvec / (np.linalg.norm(qvec) or 1.0))
                order = np.argsort(-sims, kind="stable")[:VEC_POOL]
                vec_rank = {pids[i]: r for r, i in enumerate(order.tolist())}
        except (embed.BudgetExceeded, embed.ProviderError) as exc:
            mode = "keyword_only"
            warnings.append(f"keyword_only: vector search unavailable ({exc})")

    # Fuse with RRF, then apply filters. The FTS term is weighted by its
    # bm25 magnitude relative to the best hit: pure rank ordinals would let a
    # weak rank-3 lexical match (generic terms) outscore a strong rank-1
    # match on rare discriminative terms.
    scores: dict[str, float] = {}
    best_bm25 = min((h["rank"] for h in fts), default=0.0)
    for h in fts:
        pid, r = h["pid"], fts_rank[h["pid"]]
        strength = (h["rank"] / best_bm25) if best_bm25 else 1.0
        scores[pid] = scores.get(pid, 0.0) + strength / (RRF_K + r)
    for pid, r in vec_rank.items():
        scores[pid] = scores.get(pid, 0.0) + 1.0 / (RRF_K + r)
    ranked = sorted(scores, key=lambda p: scores[p], reverse=True)

    # Filters + dedup by content hash.
    seen_hash: dict[str, str] = {}
    alts: dict[str, list[str]] = {}
    candidates: list[str] = []
    for pid in ranked:
        row = store.passage_by_id(conn, pid)
        if row is None or not _filters_met(row, params):
            continue
        h = row["content_hash"]
        if h in seen_hash:
            first = seen_hash[h]
            alts.setdefault(first, []).append(f"{row['doc_id']} p{row['pdf_page']}")
            continue
        seen_hash[h] = pid
        candidates.append(pid)

    # Diversity: max 2 hits per document first, then fill.
    picked, per_doc = [], {}
    for pid in candidates:
        doc = store.passage_by_id(conn, pid)["doc_id"]
        if per_doc.get(doc, 0) >= 2:
            continue
        picked.append(pid)
        per_doc[doc] = per_doc.get(doc, 0) + 1
        if len(picked) >= params.top_k:
            break
    if len(picked) < params.top_k:
        for pid in candidates:
            if pid not in picked:
                picked.append(pid)
            if len(picked) >= params.top_k:
                break

    if not picked:
        warnings.append("no_match: no passages matched this query/filters in the indexed corpus.")
    if any(store.passage_by_id(conn, p) and len((_display(store.passage_by_id(conn, p)))[0]) > MAX_HIT_CHARS for p in picked):
        warnings.append("truncated: a hit exceeds display budget; use get_source_passage for full text.")
    return {
        "results": [_hit(conn, pid, settings, alts.get(pid)) for pid in picked],
        "warnings": warnings,
        "expansions": expansions,
        "corpus_revision": settings.corpus_revision,
        "retrieval_mode": mode,
    }


def get_passage(params: PassageInput, settings: Settings, conn: sqlite3.Connection) -> dict:
    row = store.passage_by_id(conn, params.pid)
    if row is None:
        raise NotFoundError(f"unknown passage id: {params.pid}")
    text, derivation = _display(row)
    out = _hit(conn, params.pid, settings)
    out["text"] = text
    out["text_truncated"] = False
    out["derivation"] = derivation
    if derivation == "reviewed_transcription":
        out["raw_extraction"] = store.page_raw(conn, row["doc_id"], row["pdf_page"])
    else:
        out["raw_extraction"] = None
    nb = store.neighbors(conn, row["doc_id"], row["pdf_page"], row["ordinal"])
    out["context"] = {}
    for key in ("prev", "next"):
        if nb[key] and params.context_chars > 0:
            nrow = store.passage_by_id(conn, nb[key])
            ntext, _ = _display(nrow)
            out["context"][key] = {"pid": nb[key], "text": ntext[: params.context_chars]}
        else:
            out["context"][key] = None
    return out


def get_coverage(params: CoverageInput, settings: Settings, conn: sqlite3.Connection) -> dict:
    docs = [dict(r) for r in conn.execute("SELECT * FROM documents ORDER BY filename")]
    if params.region:
        docs = [d for d in docs if (d["geography"] or "").lower() == params.region.lower()]
    catalog = []
    for doc in docs:
        pages = [dict(r) for r in conn.execute(
            "SELECT status, COUNT(*) c FROM pages WHERE doc_id=? GROUP BY status", (doc["doc_id"],))]
        by_status = {p["status"]: p["c"] for p in pages}
        n_pass = conn.execute("SELECT COUNT(*) c FROM passages WHERE doc_id=?", (doc["doc_id"],)).fetchone()["c"]
        n_vec = conn.execute(
            "SELECT COUNT(*) c FROM embeddings e JOIN passages p ON e.pid=p.pid WHERE p.doc_id=? AND e.model=?",
            (doc["doc_id"], settings.embedding_model)).fetchone()["c"]
        catalog.append({
            "doc_id": doc["doc_id"], "filename": doc["filename"], "title": doc["title"],
            "publisher": doc["publisher"], "pdf_pages": doc["pdf_pages"],
            "geography": doc["geography"], "topics": doc["topics"],
            "source_url_status": doc["source_url_status"],
            "pages_approved": by_status.get("approved", 0),
            "pages_excluded": by_status.get("excluded", 0),
            "pages_pending": by_status.get("pending", 0),
            "passages": n_pass, "vectors": n_vec,
        })
    excluded = [dict(r) for r in conn.execute(
        "SELECT doc_id, pdf_page, exclude_reason FROM pages WHERE status='excluded' ORDER BY doc_id, pdf_page LIMIT 200")]
    totals = store.spend_totals(conn)
    n_vec_total = conn.execute("SELECT COUNT(*) c FROM embeddings WHERE model=?", (settings.embedding_model,)).fetchone()["c"]
    return {
        "documents": catalog,
        "approved_pages": sum(d["pages_approved"] for d in catalog),
        "excluded_pages": excluded,
        "known_gaps": [
            "Inventory inclusion is not cultural completeness; only approved pages are searchable.",
            "Individual publication URLs are unresolved; only the user-provided collection URL is recorded.",
        ],
        "corpus_revision": settings.corpus_revision,
        "indexed_at": store.get_meta(conn, "indexed_at"),
        "embedding_model": settings.embedding_model,
        "embedding_dims": settings.embedding_dims,
        "vectors_indexed": n_vec_total,
        "search_mode": "hybrid" if (n_vec_total and settings.api_key) else "keyword_only",
        "spend_usd": round(totals["committed_usd"], 6),
    }
