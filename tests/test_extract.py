"""Engine-choice regression on visually verified pages (needs source PDFs)."""

from pathlib import Path

import pytest

from sard_mcp import extract as X

SRC = Path(r"C:\Users\nawaf\OneDrive - KFUPM\Culture")
pytestmark = pytest.mark.skipif(not SRC.exists(), reason="source PDFs not mounted")

CASES = [
    ("bagengUrban-Heritage-1-1.pdf", 47, "pypdf"),   # Latin; pdfium reverses it
    ("bag-Intangible-Heritage.pdf", 86, "pdfium"),   # Arabic; pypdf drops endings
    ("bagarUrban-and-Handicrafts.pdf", 97, "pdfium"),
    ("Riyadh.pdf", 21, "pdfium"),
    ("enternace-to-west-old.pdf", 2, "pdfium"),
    ("Atlal-30-web-pdf.pdf", 94, "pypdf"),           # Atlal Arabic; pdfium reverses it
    ("atlal21.pdf", 5, "pypdf"),                     # (content is Atlal vol. 31)
    ("atlal32.pdf", 132, "pypdf"),
]


@pytest.mark.parametrize("filename,page,want", CASES)
def test_engine_choice(filename, page, want):
    info = X.extract_page(SRC / filename, page - 1)
    assert info["engine"] == want
    assert len(info["text"]) > 100
