# Ingestion report (19 Sep 2026, corpus rev r1)

Indexed at 2026-09-18T22:53:39 (local). Index: `%LOCALAPPDATA%\SardMCP\sard.db`.

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
