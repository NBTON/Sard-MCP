"""End-to-end MCP stdio protocol test: real subprocess, raw JSON-RPC.

Uses an isolated SARD_HOME fixture db (keyword mode, no key, no network).
Validates the wire contract real clients see: initialize, tools/list,
tools/call for all three tools, bounded errors, and clean stdout.
"""

import json
import subprocess
import sys

import pytest

from sard_mcp import store
from sard_mcp.normalize import normalize_search


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
        store.set_meta(conn, "corpus_revision", "r1")
    conn.close()
    return tmp_path


def run_stdio(home, requests):
    """Persistent pipes like a real client (one-shot stdin races EOF)."""
    import os

    from sard_mcp.config import PROJECT_ROOT

    (home / "empty.env").write_text("# no key here\n", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-c", "from sard_mcp.server import main; main()"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", bufsize=1, cwd=str(PROJECT_ROOT),
        env={"PATH": os.environ["PATH"], "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
              "SARD_HOME": str(home), "PYTHONUTF8": "1",
              "SARD_ENV_FILE": str(home / "empty.env")},
    )
    out_lines = []
    try:
        for req in requests:
            proc.stdin.write(json.dumps(req, ensure_ascii=False) + "\n")
            proc.stdin.flush()
            if "id" in req:
                out_lines.append(proc.stdout.readline())
    finally:
        proc.stdin.close()
        proc.wait(timeout=60)
    return proc, out_lines, proc.stderr.read()


def test_stdio_protocol(home):
    reqs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                    "clientInfo": {"name": "t", "version": "0"}}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "search_saudi_culture", "arguments": {"query": "القهوة"}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call",
         "params": {"name": "get_source_passage", "arguments": {"pid": "D.pdf:p001:00"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
         "params": {"name": "get_source_passage", "arguments": {"pid": "nope"}}},
        {"jsonrpc": "2.0", "id": 6, "method": "tools/call",
         "params": {"name": "get_corpus_coverage", "arguments": {}}},
    ]
    proc, lines, stderr = run_stdio(home, reqs)
    assert proc.returncode == 0, stderr[-2000:]
    assert len(lines) == 6, f"expected 6 responses, got {len(lines)}"
    resps = {}
    for ln in lines:  # every stdout line must be protocol JSON (no pollution)
        assert ln.strip(), "blank stdout line from server"
        msg = json.loads(ln)
        resps[msg.get("id")] = msg

    assert "serverInfo" in resps[1]["result"]
    tools = {t["name"] for t in resps[2]["result"]["tools"]}
    assert tools == {"search_saudi_culture", "get_source_passage", "get_corpus_coverage"}

    def text_of(resp):
        return "\n".join(b.get("text", "") for b in resp["result"]["content"])

    assert "D.pdf:p001:00" in text_of(resps[3])
    assert "keyword_only" in text_of(resps[3])  # no key in this env
    assert "D.pdf" in text_of(resps[4]) and "القهوة" in text_of(resps[4])
    assert "unknown passage id" in text_of(resps[5])
    assert "D.pdf" in text_of(resps[6])
    assert "sk-or-" not in stderr and "sk-or-" not in "".join(lines)
