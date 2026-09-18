"""Dual-engine page extraction with script-ratio engine choice (read-only).

Verified behaviour (docs/EXTRACTION_NOTES.md): PDFium preserves Arabic
word order but reverses Latin lines; pypdf handles Latin well but can
truncate some Arabic layouts. The choice signal is the Arabic-letter
ratio, which is order-independent, so the rule cannot be confused by
the reversal it guards against.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from .normalize import arabic_ratio


def pdfium_text(path: Path, idx0: int) -> str:
    import pypdfium2

    pdf = pypdfium2.PdfDocument(str(path))
    try:
        textpage = pdf[idx0].get_textpage()
        try:
            return textpage.get_text_range() or ""
        finally:
            textpage.close()
    finally:
        pdf.close()


def pypdf_text(path: Path, idx0: int) -> str:
    import pypdf

    reader = pypdf.PdfReader(str(path))
    return reader.pages[idx0].extract_text() or ""


def extract_page(path: Path, idx0: int) -> dict:
    """Extract one page (0-based) with both engines and pick by script ratio."""
    errors: dict[str, str] = {}
    try:
        t_pdfium = pdfium_text(path, idx0)
    except Exception as exc:  # noqa: BLE001 - record and continue
        t_pdfium, errors["pdfium"] = "", f"{type(exc).__name__}: {exc}"
    try:
        t_pypdf = pypdf_text(path, idx0)
    except Exception as exc:  # noqa: BLE001
        t_pypdf, errors["pypdf"] = "", f"{type(exc).__name__}: {exc}"

    ratio = arabic_ratio(t_pdfium) if t_pdfium.strip() else arabic_ratio(t_pypdf)
    if t_pdfium.strip() and (ratio >= 0.5 or not t_pypdf.strip()):
        engine, text = "pdfium", t_pdfium
    else:
        engine, text = "pypdf", t_pypdf
    return {
        "engine": engine,
        "text": text,
        "arabic_ratio": round(ratio, 3),
        "pdfium_chars": len(t_pdfium),
        "pypdf_chars": len(t_pypdf),
        "repl_count": text.count("�"),
        "errors": errors,
    }


def page_count(path: Path) -> int:
    import pypdf

    return len(pypdf.PdfReader(str(path)).pages)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def render_page(path: Path, idx0: int, dest: Path, scale: float = 2.0) -> Path:
    import pypdfium2

    dest.parent.mkdir(parents=True, exist_ok=True)
    pdf = pypdfium2.PdfDocument(str(path))
    try:
        pdf[idx0].render(scale=scale).to_pil().save(str(dest))
    finally:
        pdf.close()
    return dest
