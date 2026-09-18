"""SQLite storage: catalog, pages, passages, FTS5 index, vectors, budget log.

All imports run inside explicit transactions so a failed import leaves the
last working index usable. Embeddings are keyed by (passage, model, params)
with a content hash, so unchanged passages are never re-embedded.
"""

from __future__ import annotations

import hashlib
import sqlite3
import time
from pathlib import Path

import numpy as np

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS documents(
  doc_id TEXT PRIMARY KEY, filename TEXT NOT NULL, title TEXT, publisher TEXT,
  checksum TEXT, pdf_pages INTEGER, source_url TEXT, source_url_status TEXT,
  geography TEXT, geography_provenance TEXT, topics TEXT, imported_at TEXT);
CREATE TABLE IF NOT EXISTS pages(
  doc_id TEXT, pdf_page INTEGER, engine TEXT, raw_text TEXT, raw_chars INTEGER,
  alt_chars INTEGER, arabic_ratio REAL, repl_count INTEGER,
  printed_label TEXT, status TEXT DEFAULT 'pending', exclude_reason TEXT,
  PRIMARY KEY(doc_id, pdf_page));
CREATE TABLE IF NOT EXISTS passages(
  pid TEXT PRIMARY KEY, doc_id TEXT NOT NULL, pdf_page INTEGER NOT NULL,
  ordinal INTEGER NOT NULL, text_raw TEXT NOT NULL, text_search TEXT NOT NULL,
  text_reviewed TEXT, derivation TEXT NOT NULL DEFAULT 'extracted',
  content_hash TEXT NOT NULL, tokens INTEGER NOT NULL,
  region TEXT, topic TEXT, lang TEXT);
CREATE VIRTUAL TABLE IF NOT EXISTS passages_fts USING fts5(
  pid UNINDEXED, text_search, tokenize='unicode61 remove_diacritics 1');
CREATE TABLE IF NOT EXISTS embeddings(
  pid TEXT, model TEXT, dims INTEGER, params TEXT, content_hash TEXT,
  vector BLOB, created_at TEXT, PRIMARY KEY(pid, model, params));
CREATE TABLE IF NOT EXISTS query_cache(
  qhash TEXT PRIMARY KEY, model TEXT, query TEXT, vector BLOB, created_at TEXT);
CREATE TABLE IF NOT EXISTS usage_log(
  id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, kind TEXT,
  tokens_est INTEGER, tokens_reported INTEGER,
  cost_est_usd REAL, cost_reported_usd REAL, note TEXT);
"""


def open_db(path: Path) -> sqlite3.Connection:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.executescript(SCHEMA)
    return conn


def content_hash(*parts: str) -> str:
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:32]


def get_meta(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else None


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute("INSERT OR REPLACE INTO meta(key, value) VALUES(?, ?)", (key, value))


def upsert_document(conn: sqlite3.Connection, doc: dict) -> None:
    conn.execute(
        """INSERT INTO documents(doc_id, filename, title, publisher, checksum, pdf_pages,
             source_url, source_url_status, geography, geography_provenance, topics, imported_at)
           VALUES(:doc_id, :filename, :title, :publisher, :checksum, :pdf_pages,
             :source_url, :source_url_status, :geography, :geography_provenance, :topics, :imported_at)
           ON CONFLICT(doc_id) DO UPDATE SET filename=excluded.filename, title=excluded.title,
             publisher=excluded.publisher, checksum=excluded.checksum, pdf_pages=excluded.pdf_pages,
             source_url=excluded.source_url, source_url_status=excluded.source_url_status,
             geography=excluded.geography, geography_provenance=excluded.geography_provenance,
             topics=excluded.topics, imported_at=excluded.imported_at""",
        doc,
    )


def upsert_page(conn: sqlite3.Connection, page: dict) -> None:
    conn.execute(
        """INSERT INTO pages(doc_id, pdf_page, engine, raw_text, raw_chars, alt_chars, arabic_ratio,
             repl_count, printed_label, status, exclude_reason)
           VALUES(:doc_id, :pdf_page, :engine, :raw_text, :raw_chars, :alt_chars, :arabic_ratio,
             :repl_count, :printed_label, :status, :exclude_reason)
           ON CONFLICT(doc_id, pdf_page) DO UPDATE SET engine=excluded.engine,
             raw_text=excluded.raw_text, raw_chars=excluded.raw_chars, alt_chars=excluded.alt_chars,
             arabic_ratio=excluded.arabic_ratio, repl_count=excluded.repl_count,
             printed_label=excluded.printed_label, status=excluded.status,
             exclude_reason=excluded.exclude_reason""",
        page,
    )


def page_raw(conn: sqlite3.Connection, doc_id: str, pdf_page: int) -> str | None:
    row = conn.execute(
        "SELECT raw_text FROM pages WHERE doc_id=? AND pdf_page=?", (doc_id, pdf_page)
    ).fetchone()
    return row["raw_text"] if row else None


def upsert_passage(conn: sqlite3.Connection, passage: dict) -> None:
    conn.execute(
        """INSERT INTO passages(pid, doc_id, pdf_page, ordinal, text_raw, text_search,
             text_reviewed, derivation, content_hash, tokens, region, topic, lang)
           VALUES(:pid, :doc_id, :pdf_page, :ordinal, :text_raw, :text_search,
             :text_reviewed, :derivation, :content_hash, :tokens, :region, :topic, :lang)
           ON CONFLICT(pid) DO UPDATE SET doc_id=excluded.doc_id, pdf_page=excluded.pdf_page,
             ordinal=excluded.ordinal, text_raw=excluded.text_raw, text_search=excluded.text_search,
             text_reviewed=excluded.text_reviewed, derivation=excluded.derivation,
             content_hash=excluded.content_hash, tokens=excluded.tokens,
             region=excluded.region, topic=excluded.topic, lang=excluded.lang""",
        passage,
    )
    conn.execute("DELETE FROM passages_fts WHERE pid=?", (passage["pid"],))
    conn.execute(
        "INSERT INTO passages_fts(pid, text_search) VALUES(?, ?)",
        (passage["pid"], passage["text_search"]),
    )


def delete_doc_passages(conn: sqlite3.Connection, doc_id: str) -> int:
    pids = [r["pid"] for r in conn.execute("SELECT pid FROM passages WHERE doc_id=?", (doc_id,))]
    for pid in pids:
        conn.execute("DELETE FROM passages_fts WHERE pid=?", (pid,))
        conn.execute("DELETE FROM embeddings WHERE pid=?", (pid,))
    conn.execute("DELETE FROM passages WHERE doc_id=?", (doc_id,))
    return len(pids)


def passage_by_id(conn: sqlite3.Connection, pid: str) -> dict | None:
    row = conn.execute(
        """SELECT p.*, d.filename, d.title, d.publisher, d.source_url, d.source_url_status,
                  d.geography, d.geography_provenance, pg.printed_label
           FROM passages p JOIN documents d ON p.doc_id = d.doc_id
           LEFT JOIN pages pg ON p.doc_id = pg.doc_id AND p.pdf_page = pg.pdf_page
           WHERE p.pid = ?""",
        (pid,),
    ).fetchone()
    return dict(row) if row else None


def neighbors(conn: sqlite3.Connection, doc_id: str, pdf_page: int, ordinal: int) -> dict:
    rows = conn.execute(
        """SELECT pid, pdf_page, ordinal FROM passages
           WHERE doc_id=? ORDER BY pdf_page, ordinal""",
        (doc_id,),
    ).fetchall()
    prev_id = next_id = None
    for i, r in enumerate(rows):
        if r["pdf_page"] == pdf_page and r["ordinal"] == ordinal:
            if i > 0:
                prev_id = rows[i - 1]["pid"]
            if i + 1 < len(rows):
                next_id = rows[i + 1]["pid"]
            break
    return {"prev": prev_id, "next": next_id}


def escape_fts(query: str) -> str:
    """Quote each term for FTS5; returns '' when no usable term exists."""
    terms = [t.strip('"').replace('"', '""') for t in query.split() if t.strip('"')]
    terms = [t for t in terms if t and len(t) <= 64][:32]
    return " OR ".join(f'"{t}"' for t in terms)


def fts_search(conn: sqlite3.Connection, match_expr: str, limit: int) -> list[dict]:
    if not match_expr:
        return []
    rows = conn.execute(
        """SELECT f.pid, bm25(passages_fts) AS rank FROM passages_fts f
           WHERE passages_fts MATCH ? ORDER BY rank LIMIT ?""",
        (match_expr, limit),
    ).fetchall()
    return [{"pid": r["pid"], "rank": r["rank"]} for r in rows]


def vectors_for_model(conn: sqlite3.Connection, model: str) -> tuple[list[str], np.ndarray]:
    rows = conn.execute(
        "SELECT pid, vector, dims FROM embeddings WHERE model=? ORDER BY pid", (model,)
    ).fetchall()
    if not rows:
        return [], np.zeros((0, 0), dtype=np.float32)
    pids = [r["pid"] for r in rows]
    mat = np.stack([np.frombuffer(r["vector"], dtype=np.float32) for r in rows])
    return pids, mat


def get_embedding(conn: sqlite3.Connection, pid: str, model: str, params: str) -> dict | None:
    row = conn.execute(
        "SELECT content_hash, vector, dims FROM embeddings WHERE pid=? AND model=? AND params=?",
        (pid, model, params),
    ).fetchone()
    return dict(row) if row else None


def store_embedding(
    conn: sqlite3.Connection, pid: str, model: str, dims: int,
    params: str, content_hash: str, vector: np.ndarray,
) -> None:
    conn.execute(
        """INSERT INTO embeddings(pid, model, dims, params, content_hash, vector, created_at)
           VALUES(?, ?, ?, ?, ?, ?, ?) ON CONFLICT(pid, model, params) DO UPDATE SET
           dims=excluded.dims, content_hash=excluded.content_hash,
           vector=excluded.vector, created_at=excluded.created_at""",
        (pid, model, dims, params, content_hash, vector.astype(np.float32).tobytes(),
         time.strftime("%Y-%m-%dT%H:%M:%S")),
    )


def get_query_vector(conn: sqlite3.Connection, qhash: str, model: str) -> np.ndarray | None:
    row = conn.execute(
        "SELECT vector FROM query_cache WHERE qhash=? AND model=?", (qhash, model)
    ).fetchone()
    return np.frombuffer(row["vector"], dtype=np.float32).copy() if row else None


def store_query_vector(conn: sqlite3.Connection, qhash: str, model: str, query: str, vec: np.ndarray) -> None:
    conn.execute(
        "INSERT OR REPLACE INTO query_cache(qhash, model, query, vector, created_at) VALUES(?, ?, ?, ?, ?)",
        (qhash, model, query[:500], vec.astype(np.float32).tobytes(), time.strftime("%Y-%m-%dT%H:%M:%S")),
    )


def log_usage(
    conn: sqlite3.Connection, kind: str, tokens_est: int = 0, tokens_reported: int | None = None,
    cost_est_usd: float = 0.0, cost_reported_usd: float | None = None, note: str = "",
) -> None:
    conn.execute(
        """INSERT INTO usage_log(ts, kind, tokens_est, tokens_reported,
             cost_est_usd, cost_reported_usd, note) VALUES(?, ?, ?, ?, ?, ?, ?)""",
        (time.strftime("%Y-%m-%dT%H:%M:%S"), kind, tokens_est, tokens_reported,
         cost_est_usd, cost_reported_usd, note),
    )


def spend_totals(conn: sqlite3.Connection) -> dict:
    row = conn.execute(
        """SELECT COALESCE(SUM(CASE WHEN kind='commit' THEN COALESCE(cost_reported_usd, cost_est_usd) END), 0) AS committed,
                  COALESCE(SUM(CASE WHEN kind='reserve' THEN cost_est_usd END), 0)
                  - COALESCE(SUM(CASE WHEN kind='release' THEN cost_est_usd END), 0) AS reserved,
                  COALESCE(SUM(CASE WHEN kind='commit' THEN COALESCE(tokens_reported, tokens_est) END), 0) AS tokens
           FROM usage_log"""
    ).fetchone()
    return {"committed_usd": row["committed"], "reserved_usd": row["reserved"], "tokens": row["tokens"]}
