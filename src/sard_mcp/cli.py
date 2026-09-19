"""CLI-only corpus operations: inventory, dry-run, import, budget, titles.

Import/reindex stays out of the agent tools by design. All selection
variants are idempotent: unchanged passages keep their cached vectors.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from . import chunk as C
from . import embed as E
from . import extract as X
from . import ocr as OCR
from . import store
from .config import PROJECT_ROOT, Settings, load_settings
from .normalize import arabic_ratio, normalize_search

DATA_DIR = PROJECT_ROOT / "data"
DEMO_PAGES = [  # (filename, pdf_page) reviewed anchors
    ("bag-Intangible-Heritage.pdf", 86),
    ("bagarUrban-and-Handicrafts.pdf", 97),
    ("bagarUrban-and-Handicrafts.pdf", 98),
    ("bagengUrban-Heritage-1-1.pdf", 47),
    ("Riyadh.pdf", 21),
    ("enternace-to-west-old.pdf", 2),
]

REPL_RATIO_LIMIT = 0.02
MIN_PAGE_CHARS = 50

_BAGENG_LABEL = re.compile(r"Urban Heritage\s*-\s*Urban Heritage Sector\s*(\d{1,3})")


def parsed_label(doc: str, text: str) -> str | None:
    """Printed page label parsed from the page header (bageng book only).

    The header is part of the extracted text on every content page, so this
    is read from the page itself, never a blanket offset. Other books have
    inconsistent/mangled footers: reviewed labels only.
    """
    if doc != "bagengUrban-Heritage-1-1.pdf":
        return None
    match = _BAGENG_LABEL.search(" ".join(text.splitlines()[:3]))
    if match and 1 <= int(match.group(1)) <= 92:
        return match.group(1)
    return None


def load_json(name: str) -> dict | list:
    path = DATA_DIR / name
    if not path.exists():
        print(f"note: {name} missing, using empty defaults", file=sys.stderr)
        return {} if name == "doc_meta.json" else []
    return json.loads(path.read_text(encoding="utf-8"))


def reviewed_index() -> dict[tuple[str, int], dict]:
    return {(r["doc"], r["pdf_page"]): r for r in load_json("reviewed_passages.json")}


def parse_selection(args: argparse.Namespace, source_dir: Path) -> dict[str, set[int] | None]:
    """Return {filename: None(all pages) | set(1-based pages)}."""
    if args.demo:
        sel: dict[str, set[int] | None] = {}
        for doc, page in DEMO_PAGES:
            sel.setdefault(doc, set()).add(page)
        return sel
    if args.docs:
        return {name.strip(): None for name in args.docs.split(",") if name.strip()}
    if args.pages:
        sel = {}
        for chunk_spec in args.pages.split(";"):
            doc, _, rng = chunk_spec.partition(":")
            pages: set[int] = set()
            for part in rng.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-", 1)
                    pages.update(range(int(a), int(b) + 1))
                elif part:
                    pages.add(int(part))
            sel[doc.strip()] = pages
        return sel
    if args.all:
        return {p.name: None for p in sorted(source_dir.glob("*.pdf"))}
    raise SystemExit("choose one of --demo, --docs, --pages, --all")


def gate_page(info: dict, is_reviewed: bool) -> tuple[str, str]:
    """Return (status, reason). Reviewed pages are always approved."""
    if is_reviewed:
        return "approved", "reviewed_transcription"
    text = info["text"]
    if not text.strip():
        return "excluded", "blank_or_no_text"
    chars = len(text)
    if chars < MIN_PAGE_CHARS:
        return "excluded", "too_short"
    if info["repl_count"] / chars > REPL_RATIO_LIMIT:
        return "excluded", "high_replacement_ratio"
    return "approved", ""


def gate_ocr(res: dict) -> tuple[str, str]:
    """Return (status, reason) for a local-OCR page result."""
    if "error" in res:
        return "excluded", res["error"].split(":")[0]
    text = res.get("text", "")
    if not text.strip():
        return "excluded", "ocr_blank_or_no_text"
    if len(text) < MIN_PAGE_CHARS:
        return "excluded", "ocr_too_short"
    if res.get("words", 0) < OCR.MIN_WORDS:
        return "excluded", "ocr_too_few_words"
    if res.get("mean_conf", 0.0) < OCR.MIN_CONF:
        return "excluded", "ocr_low_confidence"
    return "approved", ""


def build_passages(doc_id: str, pdf_page: int, info: dict, meta: dict, rev: dict | None,
                   ocr: bool = False) -> list[dict]:
    lang = "ar" if info["arabic_ratio"] >= 0.5 else "en"
    if rev:
        paras, out = rev["paragraphs"], []
        para_meta = rev.get("para_meta", [])
        ordinal = 0
        for i, para in enumerate(paras):
            pm = para_meta[i] if i < len(para_meta) else {}
            for piece in C.chunk_text(para):
                text = piece["text"]
                out.append({
                    "pid": f"{doc_id}:p{pdf_page:03d}:{ordinal:02d}",
                    "doc_id": doc_id, "pdf_page": pdf_page, "ordinal": ordinal,
                    "text_raw": "", "text_search": normalize_search(text),
                    "text_reviewed": text, "derivation": "reviewed_transcription",
                    "content_hash": store.content_hash("reviewed_transcription", text),
                    "tokens": piece["tokens"],
                    "region": pm.get("region", rev.get("region", meta.get("region"))),
                    "topic": pm.get("topic", rev.get("topic", meta.get("topic"))),
                    "lang": rev.get("lang", lang),
                })
                ordinal += 1
        return out
    derivation = "ocr" if ocr else "extracted"
    return [{
        "pid": f"{doc_id}:p{pdf_page:03d}:{c['ordinal']:02d}",
        "doc_id": doc_id, "pdf_page": pdf_page, "ordinal": c["ordinal"],
        "text_raw": c["text"], "text_search": normalize_search(c["text"]),
        "text_reviewed": None, "derivation": derivation,
        "content_hash": store.content_hash(derivation, c["text"]),
        "tokens": c["tokens"],
        "region": meta.get("region"), "topic": meta.get("topic"), "lang": lang,
    } for c in C.chunk_text(info["text"])]


def cmd_inventory(settings: Settings) -> int:
    out_path = settings.home / "inventory.json"
    report: dict = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "docs": []}
    for pdf in sorted(settings.source_dir.glob("*.pdf")):
        try:
            n = X.page_count(pdf)
        except Exception as exc:  # noqa: BLE001
            report["docs"].append({"file": pdf.name, "error": f"{type(exc).__name__}: {exc}"})
            continue
        entry: dict = {"file": pdf.name, "pdf_pages": n, "pages": []}
        for i in range(n):
            info = X.extract_page(pdf, i)
            entry["pages"].append({
                "pdf_page": i + 1, "engine": info["engine"], "chars": len(info["text"]),
                "alt_chars": info["pypdf_chars"] if info["engine"] == "pdfium" else info["pdfium_chars"],
                "arabic_ratio": info["arabic_ratio"], "repl": info["repl_count"],
                "errors": info["errors"],
            })
        approved = sum(1 for p in entry["pages"] if gate_page(
            {"text": "x" * p["chars"], "repl_count": p["repl"]}, False)[0] == "approved")
        print(f"{pdf.name}: {n} pages, ~{approved} would auto-approve", flush=True)
        report["docs"].append(entry)
    out_path.write_text(json.dumps(report, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out_path}")
    return 0


def resolve_pages(settings: Settings, pdf: Path, wanted: list[int],
                  ocr_enabled: bool, ocr_refresh: bool, ocr_workers: int) -> dict[int, dict]:
    """Extract every wanted page; OCR fallback for blank/short ones (no writes).

    Returns {page: {"info", "rev"-agnostic status/reason, "ocr", "ocr_res"}}.
    OCR runs outside any db transaction; results are cached on disk.
    """
    infos = {p: X.extract_page(pdf, p - 1) for p in wanted}
    ocr_res: dict[int, dict] = {}
    if ocr_enabled:
        need = [p for p in wanted
                if gate_page(infos[p], False)[1] in ("blank_or_no_text", "too_short",
                                                     "high_replacement_ratio")]
        if need:
            ocr_res = OCR.ocr_doc_pages(
                pdf, need, X.sha256_file(pdf), settings.home / "ocr",
                workers=ocr_workers, refresh=ocr_refresh)
    resolved = {}
    for p in wanted:
        info = infos[p]
        status, reason = gate_page(info, False)
        used_ocr = False
        if ocr_enabled and reason in ("blank_or_no_text", "too_short",
                                      "high_replacement_ratio") and p in ocr_res:
            res = ocr_res[p]
            status, reason = gate_ocr(res)
            if status == "approved" or "error" not in res:
                info = {"engine": OCR.ENGINE_LABEL, "text": res.get("text", ""),
                        "arabic_ratio": round(arabic_ratio(res.get("text", "")), 3),
                        "pdfium_chars": 0, "pypdf_chars": 0,
                        "repl_count": 0, "errors": {}}
                used_ocr = True
            else:
                reason = f"ocr_{reason}" if not reason.startswith("ocr") else reason
        resolved[p] = {"info": info, "status": status, "reason": reason,
                       "ocr": used_ocr, "ocr_res": ocr_res.get(p)}
    return resolved


def _selection_stats(settings: Settings, selection: dict, ocr_enabled: bool = False,
                     ocr_refresh: bool = False, ocr_workers: int = 4
                     ) -> tuple[list[dict], int, int]:
    """Dry-run stats: per-page rows, total tokens, total chunks (no writes)."""
    doc_meta = load_json("doc_meta.json")
    rev_idx = reviewed_index()
    rows: list[dict] = []
    tokens = chunks = 0
    for doc, pages in selection.items():
        pdf = settings.source_dir / doc
        if not pdf.exists():
            rows.append({"doc": doc, "error": "missing file"})
            continue
        n_pages = X.page_count(pdf)
        wanted = list(range(1, n_pages + 1)) if pages is None else sorted(pages)
        meta = doc_meta.get(doc, {})
        resolved = resolve_pages(settings, pdf, wanted, ocr_enabled, ocr_refresh, ocr_workers)
        for p in wanted:
            r = resolved[p]
            info = r["info"]
            rev = rev_idx.get((doc, p))
            status, reason = ("approved", "reviewed_transcription") if rev else (r["status"], r["reason"])
            row = {"doc": doc, "pdf_page": p, "engine": info["engine"],
                   "chars": len(info["text"]), "repl": info["repl_count"],
                   "status": status, "reason": reason}
            if r["ocr_res"] and "mean_conf" in r["ocr_res"]:
                row["ocr_conf"] = r["ocr_res"]["mean_conf"]
            if status == "approved":
                passages = build_passages(doc, p, info, meta, rev, ocr=(r["ocr"] and not rev))
                row["chunks"] = len(passages)
                row["tokens"] = sum(c["tokens"] for c in passages)
                tokens += row["tokens"]
                chunks += row["chunks"]
            rows.append(row)
    return rows, tokens, chunks


def cmd_dry_run(settings: Settings, selection: dict, ocr_enabled: bool = False,
                ocr_refresh: bool = False, ocr_workers: int = 4) -> int:
    rows, tokens, chunks = _selection_stats(settings, selection, ocr_enabled, ocr_refresh, ocr_workers)
    approved = sum(1 for r in rows if r.get("status") == "approved")
    excluded = sum(1 for r in rows if r.get("status") == "excluded")
    est = E.estimate_cost_usd(tokens, settings)
    worst = est * E.RESERVE_MARGIN
    print(f"pages approved={approved} excluded={excluded} chunks={chunks} tokens~{tokens} overlap=0")
    if ocr_enabled:
        ocr_n = sum(1 for r in rows if r.get("engine") == OCR.ENGINE_LABEL and r.get("status") == "approved")
        print(f"  (of which OCR-approved: {ocr_n})")
    print(f"estimated cost ${est:.4f} (worst-case reserve ${worst:.4f})")
    print(f"caps: first-index ${settings.first_index_budget_usd:.2f}, cumulative ${settings.cumulative_budget_usd:.2f}")
    for r in rows:
        if r.get("status") != "approved":
            print(f"  EXCLUDE {r.get('doc')} p{r.get('pdf_page')}: {r.get('reason', r.get('error'))}")
    if worst > settings.first_index_budget_usd:
        print("OVER first-index budget: reduce scope or get user direction.")
        return 2
    print("within first-index budget.")
    return 0


def cmd_import(settings: Settings, selection: dict, no_embed: bool, ocr_enabled: bool = False,
               ocr_refresh: bool = False, ocr_workers: int = 4) -> int:
    doc_meta = load_json("doc_meta.json")
    rev_idx = reviewed_index()
    conn = store.open_db(settings.db_path)
    embed_items: list[dict] = []
    with conn:
        store.set_meta(conn, "corpus_revision", settings.corpus_revision)
        store.set_meta(conn, "embed_model", settings.embedding_model)
    for doc, pages in selection.items():
        pdf = settings.source_dir / doc
        if not pdf.exists():
            print(f"SKIP {doc}: missing file", file=sys.stderr)
            continue
        meta = doc_meta.get(doc, {})
        n_pages = X.page_count(pdf)
        checksum = X.sha256_file(pdf)
        wanted = list(range(1, n_pages + 1)) if pages is None else sorted(pages)
        resolved = resolve_pages(settings, pdf, wanted, ocr_enabled, ocr_refresh, ocr_workers)
        with conn:  # one transaction per document
            store.upsert_document(conn, {
                "doc_id": doc, "filename": doc, "title": meta.get("title", Path(doc).stem),
                "publisher": meta.get("publisher"), "checksum": checksum,
                "pdf_pages": n_pages, "source_url": meta.get("source_url"),
                "source_url_status": meta.get("source_url_status", "unresolved"),
                "geography": meta.get("geography"),
                "geography_provenance": meta.get("geography_provenance", "unverified"),
                "topics": meta.get("topics"),
                "imported_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            })
            new_pids: set[str] = set()
            for p in wanted:
                r = resolved[p]
                info = r["info"]
                rev = rev_idx.get((doc, p))
                status, reason = ("approved", "reviewed_transcription") if rev else (r["status"], r["reason"])
                ocr_conf = (r["ocr_res"] or {}).get("mean_conf") if r["ocr"] else None
                store.upsert_page(conn, {
                    "doc_id": doc, "pdf_page": p, "engine": info["engine"],
                    "raw_text": info["text"], "raw_chars": len(info["text"]),
                    "alt_chars": info["pypdf_chars"] if info["engine"] == "pdfium" else info["pdfium_chars"],
                    "arabic_ratio": info["arabic_ratio"], "repl_count": info["repl_count"],
                    "ocr_conf": ocr_conf,
                    "printed_label": (rev or {}).get("printed_label") or parsed_label(doc, info["text"]),
                    "status": status, "exclude_reason": reason,
                })
                if status != "approved":
                    continue
                for passage in build_passages(doc, p, info, meta, rev, ocr=(r["ocr"] and not rev)):
                    store.upsert_passage(conn, passage)
                    new_pids.add(passage["pid"])
                    embed_items.append({
                        "pid": passage["pid"],
                        "text": passage["text_reviewed"] or passage["text_raw"],
                        "content_hash": passage["content_hash"],
                    })
            # Drop stale passages from earlier chunkings of the same pages.
            for (pid,) in conn.execute("SELECT pid FROM passages WHERE doc_id=?", (doc,)).fetchall():
                if pid not in new_pids:
                    want = wanted if isinstance(wanted, range) else set(wanted)
                    pg = int(pid.split(":p")[1].split(":")[0])
                    if pg in (set(want) if not isinstance(want, range) else set(range(1, n_pages + 1))):
                        conn.execute("DELETE FROM passages_fts WHERE pid=?", (pid,))
                        conn.execute("DELETE FROM embeddings WHERE pid=?", (pid,))
                        conn.execute("DELETE FROM passages WHERE pid=?", (pid,))
        print(f"imported {doc}: {len(new_pids)} passages", flush=True)
    with conn:
        store.set_meta(conn, "indexed_at", time.strftime("%Y-%m-%dT%H:%M:%S"))
    if no_embed:
        print("text indexed; embeddings skipped (--no-embed).")
        return 0
    try:
        stats = E.ensure_passage_embeddings(settings, conn, embed_items)
    except E.BudgetExceeded as exc:
        print(f"BUDGET STOP: {exc}", file=sys.stderr)
        return 3
    print(f"embeddings: {stats}")
    return 0


def cmd_budget(settings: Settings) -> int:
    conn = store.open_db(settings.db_path)
    totals = store.spend_totals(conn)
    print(f"key: {'set' if settings.api_key else 'MISSING'} | model={settings.embedding_model}")
    print(f"committed=${totals['committed_usd']:.6f} reserved=${totals['reserved_usd']:.6f} "
          f"tokens={totals['tokens']}")
    print(f"caps: first-index ${settings.first_index_budget_usd:.2f}, "
          f"cumulative ${settings.cumulative_budget_usd:.2f}")
    if settings.api_key:
        import httpx

        try:
            with httpx.Client(timeout=15.0) as client:
                r = client.get(f"{settings.openrouter_base}/auth/key",
                               headers={"Authorization": "Bearer " + settings.api_key})
            body = r.json().get("data", {}) if r.status_code == 200 else {}
            print(f"provider key: limit={body.get('limit')} remaining={body.get('limit_remaining')} "
                  f"usage={body.get('usage')}")
        except Exception as exc:  # noqa: BLE001
            print(f"provider key check failed: {exc}")
    return 0


def cmd_titles(settings: Settings) -> int:
    out_dir = settings.home / "frontmatter"
    for pdf in sorted(settings.source_dir.glob("*.pdf")):
        n = min(3, X.page_count(pdf))
        for i in range(n):
            info = X.extract_page(pdf, i)
            dest = out_dir / f"{pdf.stem}__p{i + 1}.txt"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"[engine={info['engine']}]\n{info['text']}", encoding="utf-8")
        print(f"{pdf.name}: {n} front pages -> {out_dir.name}/", flush=True)
    print(f"wrote {out_dir}")
    return 0


def add_selection(parser: argparse.ArgumentParser) -> None:
    g = parser.add_mutually_exclusive_group(required=True)
    g.add_argument("--demo", action="store_true", help="reviewed anchor pages")
    g.add_argument("--docs", help="comma-separated filenames (whole docs)")
    g.add_argument("--pages", help='"doc.pdf:1-3,5;other.pdf:2"')
    g.add_argument("--all", action="store_true", help="every PDF in source dir")


def add_ocr_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ocr", action="store_true",
                        help="local Tesseract OCR fallback for blank/short pages (cached)")
    parser.add_argument("--ocr-refresh", action="store_true", help="re-OCR, ignoring the cache")
    parser.add_argument("--ocr-workers", type=int, default=4, help="parallel OCR workers")


def main() -> None:
    parser = argparse.ArgumentParser(description="Sard corpus import (CLI-only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("inventory").set_defaults(func=lambda s, a: cmd_inventory(s))
    p = sub.add_parser("dry-run")
    add_selection(p)
    add_ocr_options(p)
    p.set_defaults(func=lambda s, a: cmd_dry_run(
        s, parse_selection(a, s.source_dir), a.ocr, a.ocr_refresh, a.ocr_workers))
    p = sub.add_parser("import")
    add_selection(p)
    add_ocr_options(p)
    p.add_argument("--no-embed", action="store_true")
    p.set_defaults(func=lambda s, a: cmd_import(
        s, parse_selection(a, s.source_dir), a.no_embed, a.ocr, a.ocr_refresh, a.ocr_workers))
    sub.add_parser("budget").set_defaults(func=lambda s, a: cmd_budget(s))
    sub.add_parser("titles").set_defaults(func=lambda s, a: cmd_titles(s))
    args = parser.parse_args()
    settings = load_settings()
    raise SystemExit(args.func(settings, args))


if __name__ == "__main__":
    main()
