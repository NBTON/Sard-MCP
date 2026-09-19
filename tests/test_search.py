"""Search tests on a fixture db: keyword mode, filters, dedup, errors."""

import os

import pytest

from sard_mcp import search as S
from sard_mcp import store
from sard_mcp.config import Settings
from sard_mcp.models import CoverageInput, PassageInput, SearchInput
from sard_mcp.normalize import normalize_search

SETTINGS = Settings(
    home=os.getcwd(), db_path=":memory:", source_dir=".",
    embedding_model="m", embedding_dims=8,
)


def make_db(tmp_path):
    conn = store.open_db(tmp_path / "s.db")
    docs = [
        ("A.pdf", "A"), ("B.pdf", "B"),
    ]
    with conn:
        for doc_id, title in docs:
            store.upsert_document(conn, {
                "doc_id": doc_id, "filename": doc_id, "title": title, "publisher": None,
                "checksum": "x", "pdf_pages": 2, "source_url": None,
                "source_url_status": "unresolved", "geography": None,
                "geography_provenance": "test", "topics": None, "imported_at": "t",
            })
            store.upsert_page(conn, {
                "doc_id": doc_id, "pdf_page": 1, "engine": "pdfium", "raw_text": "r",
                "raw_chars": 1, "alt_chars": 1, "arabic_ratio": 1.0, "repl_count": 0,
                "printed_label": None, "status": "approved", "exclude_reason": "",
            })
        rows = [
            ("A.pdf:p001:00", "A.pdf", "القهوة العربية رمز الكرم", "hospitality", None),
            ("A.pdf:p001:01", "A.pdf", "المجلس مكان الضيوف", "hospitality", None),
            ("B.pdf:p001:00", "B.pdf", "القهوة العربية رمز الكرم", "hospitality", None),  # exact dup
            ("B.pdf:p001:01", "B.pdf", "المزمار في المنطقة الغربية", "performance", "western region"),
        ]
        for pid, doc, text, topic, region in rows:
            store.upsert_passage(conn, {
                "pid": pid, "doc_id": doc, "pdf_page": 1, "ordinal": int(pid[-2:]),
                "text_raw": text, "text_search": normalize_search(text), "text_reviewed": None,
                "derivation": "extracted",
                "content_hash": store.content_hash("extracted", text),
                "tokens": 5, "region": region, "topic": topic, "lang": "ar",
            })
    return conn


@pytest.fixture()
def conn(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    c = make_db(tmp_path)
    yield c
    c.close()


def test_keyword_only_without_key(conn):
    out = S.search(SearchInput(query="القهوة"), SETTINGS, conn)
    assert out["retrieval_mode"] == "keyword_only"
    assert len(out["results"]) == 1  # duplicate folded
    assert out["results"][0]["alternate_provenance"] == ["B.pdf p1"]


def test_no_match_warning(conn):
    out = S.search(SearchInput(query="كلمة غير موجودة إطلاقا"), SETTINGS, conn)
    assert out["results"] == []
    assert any("no_match" in w for w in out["warnings"])


def test_region_filter(conn):
    out = S.search(SearchInput(query="المزمار", region="western region"), SETTINGS, conn)
    assert [h["pid"] for h in out["results"]] == ["B.pdf:p001:01"]
    out = S.search(SearchInput(query="المزمار", region="Riyadh"), SETTINGS, conn)
    assert out["results"] == []


def test_top_k_bounded(conn):
    out = S.search(SearchInput(query="ال", top_k=10), SETTINGS, conn)
    assert len(out["results"]) <= 10


def test_get_passage_and_neighbors(conn):
    got = S.get_passage(PassageInput(pid="A.pdf:p001:00", context_chars=10), SETTINGS, conn)
    assert got["pid"] == "A.pdf:p001:00"
    assert got["context"]["next"]["pid"] == "A.pdf:p001:01"
    with pytest.raises(S.NotFoundError):
        S.get_passage(PassageInput(pid="nope"), SETTINGS, conn)


def test_coverage_counts(conn):
    cov = S.get_coverage(CoverageInput(), SETTINGS, conn)
    assert len(cov["documents"]) == 2
    assert cov["search_mode"] == "keyword_only"
    assert cov["embedding_model"] == "m"


def test_hit_reports_stored_derivation(conn):
    """OCR passages must surface derivation='ocr', not the old default."""
    text = "نقوش منطقة نجران الأثرية"
    with conn:
        store.upsert_passage(conn, {
            "pid": "B.pdf:p002:00", "doc_id": "B.pdf", "pdf_page": 2, "ordinal": 0,
            "text_raw": text, "text_search": normalize_search(text), "text_reviewed": None,
            "derivation": "ocr", "content_hash": store.content_hash("ocr", text),
            "tokens": 5, "region": "Najran", "topic": "archaeology", "lang": "ar",
        })
    out = S.search(SearchInput(query="نقوش نجران"), SETTINGS, conn)
    assert out["results"][0]["derivation"] == "ocr"
    got = S.get_passage(PassageInput(pid="B.pdf:p002:00"), SETTINGS, conn)
    assert got["derivation"] == "ocr"
