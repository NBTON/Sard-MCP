# Extraction notes (measured 18–19 Sep 2026; OCR section added for r2, Atlal rule for r3)

## r3: Atlal engine override + OCR for font-corrupt pages

Atlal journals (all 3 vols) use a font/encoding where PDFium emits
Arabic words in reverse order while pypdf preserves correct order and
completeness (91–104% of PDFium chars, no truncation; verified on
renders `quality-sample/r3`: Atlal-30 p94, atlal32 p132, mixed caption
pages p188/p191, English two-column p282 with correct column order).
`extract_page` therefore prefers pypdf for the three Atlal files
(`PYPDF_ONLY_DOCS`, regression-tested); every other doc keeps the
script-ratio rule. Residual pypdf quirks on Atlal pages: bidi
number-plate shuffles on mixed header lines and occasional mid-line
fragment splits — retrieval-OK, display quotes need care (same bar as
r1 raw passages).

The 7 regional booklets have a corrupt text layer (3–14% U+FFFD, same
font family as Riyadh), so `resolve_pages` now also sends
`high_replacement_ratio` pages to the local-OCR fallback (previously
blank/short only). The r2 gate (conf ≥ 60) is unchanged: booklet prose
passes at 70–86, photo/cover garbage fails at ~35–45, and five real
content pages lost to spread-layout confidence depression (55–59) stay
excluded because the same band holds garbage pages (no clean threshold;
evidence in `quality-sample/r3/booklet_excluded_ocr.txt`). Booklet
spreads interleave both sides line-by-line in PSM-6 OCR text.

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
