# Extraction notes (measured 18–19 Sep 2026)

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
