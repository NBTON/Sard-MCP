"""OCR fallback: gate decisions, derivation tagging, disk cache (no binaries)."""

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from sard_mcp import cli, ocr, store

SRC = Path(r"C:\Users\nawaf\OneDrive - KFUPM\Culture")


def test_gate_ocr_thresholds():
    good = {"text": "x" * 200, "mean_conf": 87.0, "words": 40}
    assert cli.gate_ocr(good) == ("approved", "")
    assert cli.gate_ocr({"error": "ocr_timeout"})[0] == "excluded"
    assert cli.gate_ocr({"text": "   ", "mean_conf": 90.0, "words": 0})[1] == "ocr_blank_or_no_text"
    assert cli.gate_ocr({"text": "x" * 10, "mean_conf": 90.0, "words": 3})[1] == "ocr_too_short"
    assert cli.gate_ocr({"text": "x" * 200, "mean_conf": 90.0, "words": 2})[1] == "ocr_too_few_words"
    assert cli.gate_ocr({"text": "x" * 200, "mean_conf": 35.0, "words": 100})[1] == "ocr_low_confidence"


def test_build_passages_ocr_derivation():
    info = {"text": "نص تجريبي للتعرف الضوئي على الحروف", "arabic_ratio": 1.0}
    out = cli.build_passages("d.pdf", 3, info, {}, None, ocr=True)
    assert out and all(p["derivation"] == "ocr" for p in out)
    assert out[0]["content_hash"] == store.content_hash("ocr", out[0]["text_raw"])
    plain = cli.build_passages("d.pdf", 3, info, {}, None)
    assert plain[0]["derivation"] == "extracted"
    assert plain[0]["content_hash"] != out[0]["content_hash"]


def test_clean_ocr_text_drops_isolated_fragments():
    dirty = "النقوش والكتابات a الأثرية ee التي تعود"
    assert ocr.clean_ocr_text(dirty) == "النقوش والكتابات  الأثرية  التي تعود"
    # Clustered fragments go even when adjacent to each other.
    assert ocr.clean_ocr_text("البلاط pee ge وتأزمت") == "البلاط   وتأزمت"
    # Long-Latin neighbours protect bibliographies and foreign terms.
    assert ocr.clean_ocr_text("G. Mursi and M. Kamal") == "G. Mursi and M. Kamal"
    assert ocr.clean_ocr_text("يشار إليها باسم (SURFACE)") == "يشار إليها باسم (SURFACE)"
    assert ocr.clean_ocr_text("Alois Musil Arabia") == "Alois Musil Arabia"
    # Digits and years are never fragments.
    assert ocr.clean_ocr_text("سنة 1417هـ ص 87") == "سنة 1417هـ ص 87"


def test_ocr_cache_roundtrip(tmp_path):
    from pathlib import Path

    pdf = Path("Some-Book.pdf")
    cache = tmp_path / "ocr"
    cache.mkdir()
    assert ocr.read_cache(cache, pdf, "abc123", 7) is None
    txt, meta = ocr.cache_paths(cache, pdf, "abc123", 7)
    txt.write_text("نص", encoding="utf-8")
    meta.write_text(json.dumps({"mean_conf": 80.0, "words": 10, "langs": ocr.OCR_LANGS, "clean": 1}),
                    encoding="utf-8")
    hit = ocr.read_cache(cache, pdf, "abc123", 7)
    assert hit["text"] == "نص" and hit["mean_conf"] == 80.0 and hit["cached"] is True
    # Different checksum must not hit (changed source re-OCRs).
    assert ocr.read_cache(cache, pdf, "zzz999", 7) is None
    # ocr_page serves the cache without invoking any binary.
    served = ocr.ocr_page(pdf, 6, "abc123", cache)
    assert served["text"] == "نص" and served["cached"] is True


@pytest.mark.skipif(not (SRC / "Makkah-Biladuna.pdf").exists(), reason="source PDFs not mounted")
def test_parallel_renders_same_pdf(tmp_path):
    """Concurrent renders of one PDF must all succeed (needs render lock)."""
    pdf = SRC / "Makkah-Biladuna.pdf"
    dests = [tmp_path / f"p{i}.png" for i in range(8)]

    def render(i):
        ocr._render_for_ocr(pdf, i, dests[i])
        return dests[i].stat().st_size

    with ThreadPoolExecutor(max_workers=4) as pool:
        sizes = list(pool.map(render, range(8)))
    assert all(s > 0 for s in sizes)


def _fake_settings(home):
    from sard_mcp.config import Settings
    return Settings(home=home, db_path=home / "t.db", source_dir=SRC)


@pytest.mark.skipif(not (SRC / "al-baha.pdf").exists(), reason="source PDFs not mounted")
def test_resolve_pages_ocrs_replacement_corrupt(tmp_path, monkeypatch):
    """Font-corrupt (high-replacement) pages get the OCR fallback, not silent exclusion."""
    from sard_mcp import extract as X
    settings = _fake_settings(tmp_path)
    pdf = SRC / "al-baha.pdf"
    info = X.extract_page(pdf, 3)  # PDF p4: dense content, ~6% U+FFFD
    assert cli.gate_page(info, False)[1] == "high_replacement_ratio"
    good = {4: {"text": "نص تجريبي " * 30, "mean_conf": 80.0, "words": 60}}
    monkeypatch.setattr(ocr, "ocr_doc_pages", lambda *a, **k: good)
    resolved = cli.resolve_pages(settings, pdf, [4], True, False, 1)
    assert resolved[4]["status"] == "approved"
    assert resolved[4]["info"]["engine"] == ocr.ENGINE_LABEL
    bad = {4: {"text": "x" * 200, "mean_conf": 35.0, "words": 100}}
    monkeypatch.setattr(ocr, "ocr_doc_pages", lambda *a, **k: bad)
    resolved = cli.resolve_pages(settings, pdf, [4], True, False, 1)
    assert (resolved[4]["status"], resolved[4]["reason"]) == ("excluded", "ocr_low_confidence")
    # Without --ocr the corrupt page stays excluded with the text-gate reason.
    resolved = cli.resolve_pages(settings, pdf, [4], False, False, 1)
    assert (resolved[4]["status"], resolved[4]["reason"]) == ("excluded", "high_replacement_ratio")


def test_pages_migration_and_nullable_conf(tmp_path):
    import sqlite3

    db = tmp_path / "old.db"
    conn = sqlite3.connect(str(db))
    conn.executescript(store.SCHEMA.replace(", ocr_conf REAL", ""))
    conn.commit()
    conn.close()
    conn = store.open_db(db)  # must add the missing column
    cols = [r[1] for r in conn.execute("PRAGMA table_info(pages)").fetchall()]
    assert "ocr_conf" in cols
    page = {"doc_id": "d", "pdf_page": 1, "engine": "pdfium", "raw_text": "t",
            "raw_chars": 1, "alt_chars": 0, "arabic_ratio": 1.0, "repl_count": 0,
            "printed_label": None, "status": "approved", "exclude_reason": ""}
    with conn:
        store.upsert_page(conn, page)  # no ocr_conf key: stays NULL
        store.upsert_page(conn, {**page, "pdf_page": 2, "ocr_conf": 81.5})
    assert conn.execute("SELECT ocr_conf FROM pages WHERE pdf_page=1").fetchone()[0] is None
    assert conn.execute("SELECT ocr_conf FROM pages WHERE pdf_page=2").fetchone()[0] == 81.5
    conn.close()
