"""Loopback streamable-HTTP test: real server subprocess + SDK client."""

import asyncio
import socket
import subprocess
import sys
import time

import pytest

from sard_mcp import store
from sard_mcp.normalize import normalize_search

PORT = 8766


def _free(port: int) -> bool:
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


@pytest.fixture()
def home(tmp_path, monkeypatch):
    monkeypatch.setenv("SARD_HOME", str(tmp_path))
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    conn = store.open_db(tmp_path / "sard.db")
    with conn:
        store.upsert_document(conn, {
            "doc_id": "D.pdf", "filename": "D.pdf", "title": "Demo", "publisher": None,
            "checksum": "x", "pdf_pages": 1, "source_url": None,
            "source_url_status": "unresolved", "geography": None,
            "geography_provenance": "test", "topics": None, "imported_at": "t",
        })
        store.upsert_page(conn, {
            "doc_id": "D.pdf", "pdf_page": 1, "engine": "pdfium", "raw_text": "r",
            "raw_chars": 1, "alt_chars": 1, "arabic_ratio": 1.0, "repl_count": 0,
            "printed_label": None, "status": "approved", "exclude_reason": "",
        })
        text = "القهوة العربية رمز الكرم"
        store.upsert_passage(conn, {
            "pid": "D.pdf:p001:00", "doc_id": "D.pdf", "pdf_page": 1, "ordinal": 0,
            "text_raw": text, "text_search": normalize_search(text), "text_reviewed": None,
            "derivation": "extracted", "content_hash": store.content_hash("extracted", text),
            "tokens": 5, "region": None, "topic": "hospitality", "lang": "ar",
        })
    conn.close()
    return tmp_path


async def _roundtrip():
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with streamable_http_client(f"http://127.0.0.1:{PORT}/mcp") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            result = await session.call_tool("search_saudi_culture", {"query": "القهوة"})
            texts = [b.text for b in result.content if getattr(b, "text", None)]
            return names, "\n".join(texts)


def test_streamable_http_roundtrip(home):
    import os

    if not _free(PORT):
        pytest.skip(f"port {PORT} busy")
    from sard_mcp.config import PROJECT_ROOT

    (home / "empty.env").write_text("# no key\n", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-c", "from sard_mcp.server import main; main()",
         "--http", "--port", str(PORT)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        cwd=str(PROJECT_ROOT),
        env={"PATH": os.environ["PATH"], "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
              "SARD_HOME": str(home), "PYTHONUTF8": "1",
              "SARD_ENV_FILE": str(home / "empty.env")},
    )
    try:
        deadline = time.time() + 60
        names = texts = None
        last_err = None
        while time.time() < deadline:
            if proc.poll() is not None:
                pytest.fail(f"server exited: {proc.stderr.read()[-2000:]}")
            try:
                names, texts = asyncio.run(_roundtrip())
                break
            except Exception as exc:  # noqa: BLE001 - retry until serving
                last_err = exc
                time.sleep(1)
        assert names == {"search_saudi_culture", "get_source_passage", "get_corpus_coverage"}, last_err
        assert "D.pdf:p001:00" in texts
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.kill()
