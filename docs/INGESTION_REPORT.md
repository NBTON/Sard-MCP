# Ingestion report (19 Sep 2026, corpus rev r3)

Index: `%LOCALAPPDATA%\SardMCP\sard.db`. Pre-update backup:
`%LOCALAPPDATA%\SardMCP\backups\sard_r2_20260919-210118.db` (9,434 passages,
verified count-identical; the r1 backup is also kept). The r1+r2 sections
below are preserved unchanged.

## Rev r3 incremental update (indexed 2026-09-19T21:12 local)

Scope: the 12 remaining unindexed PDFs (1,978 pages): 3 Atlal journals +
2 sector books via text extraction, 7 regional booklets via the local-OCR
fallback (extended to font-corrupt pages, `cli.resolve_pages`). The 20
r1+r2 documents are byte-identical (passage-hash match) and untouched:
9,434 passages, 9,434 vectors, 6 reviewed pages, 49 cached queries all
preserved. The unimported rest of enternace-to-west-old.pdf (5 passages)
and the Riyadh exclusion set (9 passages) are unchanged.

Text group (no `--ocr`): the Atlal journals need pypdf on every page
(PDFium reverses their Arabic word order; verified on renders,
`quality-sample/r3`, `docs/EXTRACTION_NOTES.md`). `extract_page` now
prefers pypdf for the three Atlal files; all other docs keep the
script-ratio rule. Filename note: `atlal21.pdf` holds Atlal vol. 31
(cover + 136 running heads); the name is kept as an exact locator.

Result: 1,774 approved pages -> 4,964 passages, 4,964 vectors. Totals:
32 documents, 6,113 approved pages, 14,398 passages, 14,398 vectors,
0 passages without vectors.

| Document | Pages appr/excl/total | Passages | Notes |
|---|---|---:|---|
| Atlal-30-web-pdf.pdf | 347/29/376 | 1,045 | vol. 30 (1442H/2020AD); EN Part One + AR Part Two |
| atlal21.pdf | 354/29/383 | 1,156 | content is Atlal vol. 31 (1444H/2022AD) |
| atlal32.pdf | 498/32/530 | 1,578 | vol. 32 (1444H/2022AD) |
| bagAntiquities.pdf | 130/22/152 | 209 | Antiquities Sector; AR then EN sections |
| bagHeritage-Commission.pdf | 195/13/208 | 316 | Heritage Commission survey |
| al-baha.pdf | 19/8/27 | 61 | OCR; Al-Baha heritage sites |
| Hail.pdf | 21/7/28 | 73 | OCR; Hail heritage sites |
| Tabuk.pdf | 33/17/50 | 57 | OCR; Tabuk heritage sites |
| handi.pdf | 26/5/31 | 70 | OCR; handicrafts nationwide |
| major-arch.pdf | 47/9/56 | 174 | OCR; major archaeological sites |
| untangable.pdf | 56/28/84 | 123 | OCR; intangible heritage elements |
| urban-major.pdf | 48/5/53 | 102 | OCR; major urban-heritage sites |

Exclusion reasons (204 total, per-page detail in `pages.exclude_reason`):
text `blank_or_no_text` 72 (blank/plate pages, spot-verified) +
`too_short` 53 (covers, dividers, photo footers); OCR
`ocr_low_confidence` 72 + `ocr_too_short` 6 + `ocr_blank_or_no_text`
1. Zero OCR engine errors across 323 pages. Five low-confidence
exclusions are real content whose spread layout depresses PSM-6
confidence (al-baha p4, Hail p6/p22, Tabuk p40/p44-partial); the 60-gate
is kept because the 50-59 band also holds garbage pages (no clean
threshold; evidence in `quality-sample/r3/booklet_excluded_ocr.txt`).
al-baha p4's text (Heritage Commission intro) duplicates approved pages
in sibling booklets. Booklet spreads interleave the two sides
line-by-line in OCR text: retrieval-OK, display quotes need care.

Bibliographic metadata for all 12 was verified against rendered covers
and title pages (`data/doc_meta.json`, per-field provenance).
Per-publication source URLs remain unresolved for all 12 (as for r1+r2);
nothing was invented.

Duplicate check: normalized-text hashes of all 323 booklet OCR pages ->
zero cross-document duplicates (no renamed copies). Idempotency:
re-running both r3 imports embeds 0 new passages ($0.00) and changes no
counts (`import_r3_text_repeat.log`, `import_r3_ocr_repeat.log`).
Stage-3 verify re-ran both imports again (21:42): cached 4,304 + 660,
embedded 0 ($0.00), counts unchanged at 14,398 passages / 14,398 vectors
with identical per-doc counts (`idempotency_r3_20260919.json`); only
`indexed_at` advanced.

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
