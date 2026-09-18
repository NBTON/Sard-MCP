"""Compare PDF text-extraction engines on Sard anchor pages (read-only).

Reads the source PDFs, extracts the same pages with pypdf, pdfplumber and
PDFium (pypdfium2), renders page images for visual review, and writes all
raw outputs plus a JSON summary to the scratch directory
(%LOCALAPPDATA%\\SardMCP\\extract-compare). Never writes to the source folder.

Usage:  uv run python scripts/extract_compare.py
"""

import hashlib
import json
import os
import sys
import time
from pathlib import Path

SRC = Path(r"C:\Users\nawaf\OneDrive - KFUPM\Culture")
OUT = Path(os.environ.get("LOCALAPPDATA", ".")) / "SardMCP" / "extract-compare"

# (filename, 1-based PDF page, anchor label)
ANCHORS = [
    ("bag-Intangible-Heritage.pdf", 86, "FOOD-84"),
    ("bagarUrban-and-Handicrafts.pdf", 97, "MAJLIS-95"),
    ("bagarUrban-and-Handicrafts.pdf", 98, "COFFEE-MIZMAR-96"),
    ("bagengUrban-Heritage-1-1.pdf", 47, "URBAN-45"),
    ("Riyadh.pdf", 21, "RIYADH-40"),
    ("enternace-to-west-old.pdf", 2, "NEAR-EAST-P2"),
    ("enternace-to-west-old.pdf", 150, "NEAR-EAST-P150"),
]


def sha16(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def extract_pypdf(path: Path, idx0: int) -> str:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    return reader.pages[idx0].extract_text() or ""


def extract_plumber(path: Path, idx0: int) -> str:
    import pdfplumber

    with pdfplumber.open(str(path)) as pdf:
        return pdf.pages[idx0].extract_text() or ""


def extract_pdfium(path: Path, idx0: int) -> str:
    import pypdfium2

    pdf = pypdfium2.PdfDocument(str(path))
    try:
        page = pdf[idx0]
        textpage = page.get_textpage()
        try:
            return textpage.get_text_range() or ""
        finally:
            textpage.close()
    finally:
        pdf.close()


def render_png(path: Path, idx0: int, dest: Path) -> None:
    import pypdfium2

    pdf = pypdfium2.PdfDocument(str(path))
    try:
        bitmap = pdf[idx0].render(scale=2.0)
        bitmap.to_pil().save(str(dest))
    finally:
        pdf.close()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary: dict = {"anchors": []}
    for filename, page1, label in ANCHORS:
        src = SRC / filename
        if not src.exists():
            print(f"SKIP {label}: missing {src}", flush=True)
            continue
        idx0 = page1 - 1
        stem = f"{src.stem}_p{page1:03d}"
        entry: dict = {"file": filename, "pdf_page": page1, "label": label, "engines": {}}
        for name, fn in (
            ("pypdf", extract_pypdf),
            ("pdfplumber", extract_plumber),
            ("pdfium", extract_pdfium),
        ):
            t0 = time.perf_counter()
            try:
                text = fn(src, idx0)
                err = None
            except Exception as exc:  # noqa: BLE001 - comparison must not abort
                text, err = "", f"{type(exc).__name__}: {exc}"
            dt = time.perf_counter() - t0
            dest = OUT / f"{stem}__{name}.txt"
            dest.write_text(text, encoding="utf-8")
            entry["engines"][name] = {
                "chars": len(text),
                "sha16": sha16(text),
                "seconds": round(dt, 3),
                "file": dest.name,
                "error": err,
            }
        png = OUT / f"{stem}.png"
        try:
            render_png(src, idx0, png)
            entry["render"] = png.name
        except Exception as exc:  # noqa: BLE001
            entry["render"] = None
            entry["render_error"] = f"{type(exc).__name__}: {exc}"
        summary["anchors"].append(entry)
        counts = ", ".join(f"{k}={v['chars']}" for k, v in entry["engines"].items())
        print(f"{label} {filename} p{page1}: chars[{counts}] render={entry['render']}", flush=True)
    (OUT / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
