"""Sard MCP server: stdio by default, loopback streamable-HTTP with --http.

Diagnostics go to stderr / file only; stdout carries the MCP protocol.
HTTP mode binds 127.0.0.1 and is a local bridge endpoint, not a deployment.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys

from mcp.server.mcpserver import MCPServer
from pydantic import ValidationError

from . import search as S
from . import store
from .config import load_settings
from .models import CoverageInput, PassageInput, SearchInput

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="sard: %(message)s")
log = logging.getLogger("sard")

server = MCPServer("sard")


def _respond(title: str, payload: dict) -> str:
    lines = [title]
    for warning in payload.get("warnings", []) or []:
        lines.append(f"Warning: {warning}")
    for hit in payload.get("results", []) or []:
        label = hit.get("printed_label")
        page = f"PDF p{hit.get('pdf_page')}" + (f" / printed {label}" if label else "")
        lines.append(f"- {hit.get('title') or hit.get('filename')} ({page}) [{hit.get('pid')}]")
    lines.append(f"mode={payload.get('retrieval_mode', '-')}")
    lines.append("```json")
    lines.append(json.dumps(payload, ensure_ascii=False, indent=1))
    lines.append("```")
    return "\n".join(lines)


def _error(message: str) -> str:
    return _respond("Sard error", {"error": message})


@server.tool(description="Search Saudi cultural publications for evidence passages.")
def search_saudi_culture(
    query: str,
    region: str | None = None,
    topic: str | None = None,
    lang: str | None = None,
    doc_ids: list[str] | None = None,
    top_k: int = 5,
) -> str:
    try:
        params = SearchInput(query=query, region=region, topic=topic, lang=lang, doc_ids=doc_ids, top_k=top_k)
    except ValidationError as exc:
        return _error(f"invalid input: {exc.errors(include_url=False)}")
    settings = load_settings()
    try:
        with store.open_db(settings.db_path) as conn:
            payload = S.search(params, settings, conn)
    except Exception as exc:  # noqa: BLE001 - bounded error, details to stderr
        log.exception("search failed")
        return _error(f"search failed: {type(exc).__name__}: {exc}")
    return _respond(f"Sard evidence for: {params.query}", payload)


@server.tool(description="Fetch one passage by id with citation metadata and context.")
def get_source_passage(pid: str, context_chars: int = 600) -> str:
    try:
        params = PassageInput(pid=pid, context_chars=context_chars)
    except ValidationError as exc:
        return _error(f"invalid input: {exc.errors(include_url=False)}")
    settings = load_settings()
    try:
        with store.open_db(settings.db_path) as conn:
            payload = S.get_passage(params, settings, conn)
    except S.NotFoundError as exc:
        return _error(str(exc))
    except Exception as exc:  # noqa: BLE001
        log.exception("get_source_passage failed")
        return _error(f"fetch failed: {type(exc).__name__}: {exc}")
    title = f"{payload.get('title') or payload.get('filename')} (PDF p{payload.get('pdf_page')})"
    return _respond(title, payload)


@server.tool(description="Corpus coverage: imported docs, page counts, gaps, index status.")
def get_corpus_coverage(region: str | None = None, topic: str | None = None) -> str:
    try:
        params = CoverageInput(region=region, topic=topic)
    except ValidationError as exc:
        return _error(f"invalid input: {exc.errors(include_url=False)}")
    settings = load_settings()
    try:
        with store.open_db(settings.db_path) as conn:
            payload = S.get_coverage(params, settings, conn)
    except Exception as exc:  # noqa: BLE001
        log.exception("get_corpus_coverage failed")
        return _error(f"coverage failed: {type(exc).__name__}: {exc}")
    return _respond("Sard corpus coverage", payload)


def main() -> None:
    parser = argparse.ArgumentParser(description="Sard MCP server")
    parser.add_argument("--http", action="store_true", help="loopback streamable-HTTP instead of stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if args.http:
        log.info("serving streamable-http on %s:%s (loopback only)", args.host, args.port)
        server.run(transport="streamable-http", host=args.host, port=args.port)
    else:
        server.run(transport="stdio")


if __name__ == "__main__":
    main()
