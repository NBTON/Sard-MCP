# Ingestion report (19 Sep 2026, corpus rev r2)

Index: `%LOCALAPPDATA%\SardMCP\sard.db`. Pre-update backup:
`%LOCALAPPDATA%\SardMCP\backups\sard_r1_20260919-165103.db` (669 passages,
verified count-identical). The r1 section below is preserved unchanged.

## Rev r2 incremental update (indexed 2026-09-19T19:30:40 local)

Scope: 15 newly added regional PDFs (4,560 pages), imported with the
existing pipeline plus a local-OCR fallback (`--ocr`). The 5 r1 documents
are byte-identical (checksums match) and untouched: 669 passages, 669
vectors, 6 reviewed pages all preserved. No previously excluded document
was expanded; the 12 older unindexed files (Atlal ×3, bagAntiquities,
bagHeritage-Commission, al-baha, Hail, Tabuk, handi, major-arch,
untangable, urban-major) remain out of the index, as does the unimported
rest of enternace-to-west-old.pdf.

All 15 new PDFs are scanned images with zero extractable text (4,560/4,560
pages blank under pdfium/pypdf), so the standard gate would exclude
everything. Local Tesseract OCR (v5.4.0, `ara+eng`, tessdata_best, PSM 6,
`~300 DPI renders, isolated 1–3 letter Latin-fragment filter) supplied the
text; every OCR page records engine `ocr-tesseract-ara-eng`, derivation
`ocr`, and mean word confidence in the db. OCR cache (4,560 pages) lives
under `%LOCALAPPDATA%\SardMCP\ocr`, keyed by file checksum + page.

Result: 3,913 approved pages → 8,765 passages, 8,765 vectors. Totals: 20
documents, 4,339 approved pages, 9,434 passages, 9,434 vectors, 0 passages
without vectors.

| Document | Pages appr/excl/total | Passages | Notes |
|---|---|---:|---|
| Makkah-Biladuna.pdf | 258/50/308 | 658 | Sharifs history; photo plates excluded |
| Madinah-Biladuna.pdf | 124/25/149 | 260 | mosques/wells survey |
| Madinah-Antiquities.pdf | 255/91/346 | 466 | verse pages excluded (two-column layout, conf ~45) |
| Qassim-Buraidah.pdf | 160/19/179 | 349 | incl. master-plan map pages excluded |
| Qassim-Unaizah.pdf | 191/67/258 | 507 | many photo pages |
| Eastern-Ahsa-History.pdf | 724/22/746 | 1,490 | cleanest print; 97% approved |
| Eastern-Qatif.pdf | 220/34/254 | 578 | |
| Eastern-Khobar.pdf | 103/34/137 | 214 | |
| Asir-Abha.pdf | 133/44/177 | 326 | |
| Asir-Namas.pdf | 179/36/215 | 389 | color edition; photos excluded |
| Jazan-Mikhlaf-Sulaimani.pdf | 1,134/95/1,229 | 2,549 | vol. 1 of the Mikhlaf history |
| Jazan-Farasan.pdf | 74/26/100 | 161 | photo cover excluded |
| Najran-Biladuna.pdf | 114/50/164 | 242 | photo plates excluded (verified on renders) |
| Jouf-Biladuna.pdf | 98/24/122 | 228 | |
| Saudi-Antiquities-Studies.pdf | 146/30/176 | 348 | color plates excluded; EN terms searchable |

Exclusion reasons (647 total, per-page detail in `pages.exclude_reason`):
`ocr_low_confidence` 448 (photo/artwork/verse pages, spot-verified),
`ocr_blank_or_no_text` 120, `ocr_too_short` 59, `ocr_too_few_words` 20.
Zero OCR engine errors across 4,560 pages.

Bibliographic metadata for all 15 was verified against rendered title
pages, not assumed (`data/doc_meta.json`, per-field provenance). One
correction to the supplied list: Saudi-Antiquities-Studies is authored by
Dr. Muhammad Ahmad Badin with Abd al-Rahman Bakr Kabawi, published by the
National Festival for Heritage and Culture (1416H) — not the Antiquities
Agency. Per-publication source URLs remain unresolved for all 15 (as for
r1); nothing was invented.

Duplicate check: normalized-text hashes of all 4,560 OCR pages — zero
cross-document duplicates (no renamed copies). Idempotency: re-running the
same import embeds 0 new passages (all cached) and changes no counts
(verified on the final index: `import_r2c_repeat.log`, cached 8,765 /
embedded 0 / $0.00; passage and vector counts unchanged).

## Rev r1 (preserved)

Indexed at 2026-09-18T22:53:39 (local).

## What is indexed

669 passages, 669 vectors (model `openai/text-embedding-3-small`, 1536 dims):

| Document | Pages appr/excl/total | Passages | Notes |
|---|---|---:|---|
| bag-Intangible-Heritage.pdf | 160/10/170 | 258 | incl. reviewed FOOD-84 (p86) |
| bagarUrban-and-Handicrafts.pdf | 184/10/194 | 292 | incl. reviewed MAJLIS-95, COFFEE-MIZMAR-96 |
| bagengUrban-Heritage-1-1.pdf | 80/12/92 | 105 | incl. reviewed URBAN-45; printed labels parsed from headers |
| Riyadh.pdf | 1/40/41 | 9 | reviewed RIYADH-40 (p21) only; rest excluded (below) |
| enternace-to-west-old.pdf | 1/-/299 | 5 | reviewed visible-text p2 only; rest not imported |

Reviewed transcriptions (`data/reviewed_passages.json`, method + reviewer
recorded, raw kept alongside): 6 pages, 21 chunks. All other passages are
raw extraction + normalized search text.

## Exclusion reasons (per-page, in `pages.exclude_reason`)

- `blank_or_no_text` / `too_short` (<50 chars): covers, photo pages, section
  dividers. Spot-checked: bageng p46 is a 41-char photo page (correct).
- `high_replacement_ratio` (>2% U+FFFD): 37 Riyadh pages. Diagnosed on
  renders (p11, p21): the book's font/layout yields interleaved fragments
  and dropped glyphs in all three engines; pypdf additionally truncates.
  Kept excluded until OCR/transcription repair.

## Full-corpus inventory (`sard-import inventory`, all 17 files, 2,774 pages)

- Would auto-pass today: ~2,218 pages — Atlal journals (348+354+499),
  bagAntiquities (130), bagHeritage-Commission (195), enternace rest (268),
  plus the four indexed docs.
- Replacement-corrupt (same font issue as Riyadh): regional booklets
  al-baha (24), Hail (26), Tabuk (40), handi (28), major-arch (52),
  untangable (63), urban-major (51) — need OCR/transcription before indexing.
- Blank/short: ~235 cover/photo/divider pages.

## Findings that changed the design

- Engine rule is script-dependent and validated per page (see
  `docs/EXTRACTION_NOTES.md`): Arabic-dominant → PDFium, Latin-dominant →
  pypdf. A ratio bug that forced PDFium everywhere was caught by the
  known-page regression test.
- The "Arabic" sector books are bilingual: English sections (e.g. coffee,
  Bisht, Google training) index as `lang=en` passages. The demo corpus is
  genuinely cross-language.
- bageng pagination runs RTL (PDF p2 = printed 90). Printed labels are read
  from each page header, never computed from an offset (validated 3/3).
- enternace p2 contains a non-rendered print-instruction text layer;
  the reviewed transcription keeps visible text only.
