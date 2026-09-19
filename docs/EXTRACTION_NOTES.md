# Extraction notes (measured 18–19 Sep 2026; OCR section added for r2)

## Local OCR fallback (r2, scanned regional books)

All 15 new books have no text layer (4,560/4,560 pages blank under both
engines), so text comes from local Tesseract 5.4.0 (`ara+eng`,
tessdata_best, PSM 6, ~300 DPI grayscale renders capped at 3,600 px,
per-page timeout, results cached by checksum+page under
`%LOCALAPPDATA%\SardMCP\ocr`). Paid OCR was explicitly not needed.

Gate (validated on renders, `quality-sample/r2`): mean Tesseract word
confidence ≥ 60, ≥ 5 words, ≥ 50 chars. Measured separation: clean prose
68–91, decorative titles 69–78, photo/artwork garbage ~35, two-column
verse ~45, blank 0 words. `ara`-only OCR mangled embedded Latin terms
(`SURFACE`→`501217405`); `ara+eng` reads them correctly with no Arabic
regression (99% normalized similarity on a control page). The `eng` model
also emits ~100k isolated 1–3 letter fragments corpus-wide (`a`, `ee`,
`oe` — misread diacritics); a post-filter drops short Latin tokens unless
a neighbouring token carries a 4+ letter Latin run, keeping bibliographies
(`G. Mursi`, `Alois Musil`) and terms (`SURFACE`, `TYPOLOGY`) while
removing ~80% of the fragments. Residual 4+ letter misreads persist;
display quotes from OCR pages need the same care as r1 raw passages.

Implementation notes: pypdfium2 document loads are not thread-safe, so
renders are serialized behind a lock while tesseract subprocesses run in
parallel (`--ocr-workers`, `OMP_THREAD_LIMIT=1`); one oversized render
once hung tesseract, hence the pixel cap + timeout. OCR pages store
engine `ocr-tesseract-ara-eng`, derivation `ocr`, and `ocr_conf` per page.

## Dual-engine extraction (r1, preserved)

Engines compared on 7 anchor pages with `scripts/extract_compare.py`
(raw outputs + page renders under `%LOCALAPPDATA%\SardMCP\extract-compare\`;
source PDFs untouched).

## Engine behaviour (verified on renders)

| Page | pdfium | pypdf | pdfplumber |
|---|---|---|---|
| FOOD-84 (ar) | correct order; minor bidi/alef defects | drops word endings (`حائل`→`حا`), inserts chars | full word-order reversal |
| MAJLIS-95 (ar) | correct order; systematic alef/hamza defects | good chars; one bidi number shuffle | full word-order reversal |
| COFFEE-MIZMAR-96 (ar) | correct order; minor defects | (not inspected closely) | (not inspected closely) |
| URBAN-45 (en) | full word-order reversal | near-perfect (`efforts`→`e fforts` twice) | near-perfect (one line-break split) |
| RIYADH-40 (ar spread) | complete but interleaved fragments + many `�` | severe truncation (line fragments cut) | complete but reversed + `�` |
| NEAR-EAST-P2 (ar) | good; also emits non-visible text layer (print instructions) | (counts similar) | (counts similar) |
| NEAR-EAST-P150 | blank, 0 chars everywhere; render confirms visually blank | blank | blank |

## Import rule

- Script-ratio rule per page (order-independent signal): Arabic-dominant →
  PDFium; Latin-dominant → pypdf. pdfplumber kept out (reverses Arabic).
- Never globally reverse strings. Store chosen raw + engine name; keep
  normalized search text separately.
- RIYADH-40: no engine is quotable → reviewed transcription
  (`data/reviewed_passages.json`, method + reviewer recorded).
- NEAR-EAST-P2: extraction contains non-rendered print-instruction text;
  reviewed transcription keeps visible text only.
- URBAN-45/FOOD/MAJLIS/COFFEE: raws are complete; reviewed transcriptions
  added for quotable demo passages, raw kept alongside for audit.
