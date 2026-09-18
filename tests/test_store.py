"""Storage tests: schema, idempotent upserts, FTS, budget ledger (tmp db)."""

import numpy as np
import pytest

from sard_mcp import store

DOC = {
    "doc_id": "Riyadh.pdf", "filename": "Riyadh.pdf", "title": "t", "publisher": "p",
    "checksum": "abc", "pdf_pages": 41, "source_url": None, "source_url_status": "unresolved",
    "geography": "Saudi Arabia", "geography_provenance": "test", "topics": "x",
    "imported_at": "2026-09-19T00:00:00",
}
PAGE = {
    "doc_id": "Riyadh.pdf", "pdf_page": 21, "engine": "pdfium", "raw_text": "raw page",
    "raw_chars": 8, "alt_chars": 7, "arabic_ratio": 1.0, "repl_count": 0,
    "printed_label": "40", "status": "approved", "exclude_reason": "",
}


def passage(pid="Riyadh.pdf:p021:00", ordinal=0, text="ساعة الصفاة في الرياض"):
    return {
        "pid": pid, "doc_id": "Riyadh.pdf", "pdf_page": 21, "ordinal": ordinal,
        "text_raw": text, "text_search": text, "text_reviewed": None,
        "derivation": "extracted", "content_hash": store.content_hash("extracted", text),
        "tokens": 10, "region": "Riyadh", "topic": "urban heritage", "lang": "ar",
    }


@pytest.fixture()
def conn(tmp_path):
    c = store.open_db(tmp_path / "t.db")
    with c:
        store.upsert_document(c, DOC)
        store.upsert_page(c, PAGE)
    yield c
    c.close()


def test_upsert_passage_idempotent(conn):
    with conn:
        store.upsert_passage(conn, passage())
        store.upsert_passage(conn, passage())
    n = conn.execute("SELECT COUNT(*) c FROM passages").fetchone()["c"]
    assert n == 1
    assert store.passage_by_id(conn, "Riyadh.pdf:p021:00")["printed_label"] == "40"


def test_fts_finds_arabic_term(conn):
    with conn:
        store.upsert_passage(conn, passage())
    hits = store.fts_search(conn, store.escape_fts("الصفاة"), 10)
    assert [h["pid"] for h in hits] == ["Riyadh.pdf:p021:00"]


def test_fts_escape_handles_quotes():
    assert store.escape_fts('a"b') == '"a""b"'  # doubled quote inside quoted term
    assert store.escape_fts("") == ""


def test_embedding_roundtrip_and_vectors(conn):
    vec = np.arange(8, dtype=np.float32)
    with conn:
        store.upsert_passage(conn, passage())
        store.store_embedding(conn, "Riyadh.pdf:p021:00", "m", 8, "default", "h", vec)
    got = store.get_embedding(conn, "Riyadh.pdf:p021:00", "m", "default")
    assert got["content_hash"] == "h" and got["dims"] == 8
    pids, mat = store.vectors_for_model(conn, "m")
    assert pids == ["Riyadh.pdf:p021:00"]
    assert mat.shape == (1, 8)


def test_budget_ledger_reserve_commit(conn):
    with conn:
        store.log_usage(conn, "reserve", cost_est_usd=1.0)
        t = store.spend_totals(conn)
        assert t["reserved_usd"] == pytest.approx(1.0)
        store.log_usage(conn, "release", cost_est_usd=1.0)
        store.log_usage(conn, "commit", cost_est_usd=0.5, cost_reported_usd=0.4)
    t = store.spend_totals(conn)
    assert t["reserved_usd"] == pytest.approx(0.0)
    assert t["committed_usd"] == pytest.approx(0.4)


def test_neighbors(conn):
    with conn:
        store.upsert_passage(conn, passage("Riyadh.pdf:p021:00", 0, "أول"))
        store.upsert_passage(conn, passage("Riyadh.pdf:p021:01", 1, "ثان"))
    assert store.neighbors(conn, "Riyadh.pdf", 21, 0) == {"prev": None, "next": "Riyadh.pdf:p021:01"}
    assert store.neighbors(conn, "Riyadh.pdf", 21, 1) == {"prev": "Riyadh.pdf:p021:00", "next": None}
