# Evaluation report (19 Sep 2026, index r3, 14,398 passages)

## Rev r3 runs (new; r1/r2 results preserved below)

- Seed fixtures (`evals/seed_cases.json`): **6/8** supporting-passage
  hit@5 (was 7/8 on r2). Trace:
  `%LOCALAPPDATA%\SardMCP\eval_seed_cases_20260919-213352.json`.
  New miss SEED-08 (English Qasr al-Hukm/Safat/Thumairi): the anchor
  (Riyadh p21) sits at ranks 8–9; rank 1 is urban-major p48 (Safat
  square/clock — directly answers part of the query) with other
  urban-heritage rivals. Same drift class as the known SEED-05 miss
  (still out of the top 10; rank 1 bagar p106, Arabian coffee and
  hospitality, directly answers it). Evidence intact: Riyadh p21 holds
  9 passages / 9 vectors, bagar p98 2/2.
- Held-out benchmark (`evals/heldout_cases.json`): **10/12 = 83.3%**
  hit@5 (was 11/12 on r1 and r2). Trace:
  `%LOCALAPPDATA%\SardMCP\eval_heldout_cases_20260919-213357.json`.
  New miss HELD-08 (Arabic query → English Al-Wajh Castle page): the
  anchor (bageng p11) sits at ranks 6–7 under the lang=en filter; the
  top 5 are Atlal English archaeology pages (rank 1: Sahal Matar and
  al-Mabiyat forts — same castle topic). The English pool grew sharply
  in r3 (Atlal Part One + bag English sections). The pre-existing
  HELD-10 glossary gap is unchanged. The ranker was deliberately not
  retuned — same policy as r2; chasing one held-out case would overfit
  the frozen benchmark.
- Trap handling (manual judgment, all retrieved evidence sensible):
  SEED freshness/scope/missing-detail traps still surface their anchors
  (Riyadh p21 ranks 1–2 for the hours query; FOOD-84 anchor rank 1–2
  for the recipe/exclusivity queries). The SEED-12 geography anchor
  was already out of the top 5 at r2 (no r3 change). HELD traps
  retrieve correctly-attributed evidence.
- New-corpus verification (16 live MCP-protocol queries over stdio,
  AR+EN, ≥1 per Atlal vol + per heritage vol + per booklet, trace
  `%LOCALAPPDATA%\SardMCP\verify_r3_20260919-213254.json`):
  **13/16** exact-page hit@5, all hybrid; every query has a
  same-document hit at ranks 1–2 except HAIL (target Hail p10 hits
  rank 4 for the short query "جبة محطة قوافل تجارية"). The three
  non-exact cases are rank drift with correct evidence: ATL31
  same-article pages p183/184 rank 1–2 (expected p191, same
  السليل ووادي الدواسر survey article); BAGANT
  same-section adjacent pages p43/p41 rank 1/4 (expected p42);
  HAIL same-topic rock-art pages. `get_source_passage` round-trip ok
  (599 chars + citation metadata); coverage 32 docs / 6,113 approved
  pages / 14,398 vectors.
- Tests: `pytest -q` (with `PYTHONUTF8=1` on this machine's cp1252
  console): **45 passed** — 34 carried over, 7 from r2, 4 new r3
  (Atlal engine rule, OCR fallback for font-corrupt pages, and
  related regressions).
- Idempotency: repeating both r3 imports embeds 0 new passages
  ($0.00; cached 4,304 + 660, all OCR cache hits); passage/vector
  counts unchanged at 14,398 with identical per-doc counts.

## Rev r2 runs (preserved; r1 results below)

- Seed fixtures (`evals/seed_cases.json`): **7/8** supporting-passage
  hit@5 (was 8/8 on r1). Trace:
  `%LOCALAPPDATA%\SardMCP\eval_seed_cases_20260919-193543.json`.
  The miss (SEED-05, English coffee/hospitality/livelihoods) is rank
  drift under 14× corpus growth, not lost evidence: ranks 1–2 are
  same-document coffee passages (UNESCO registration, serving customs)
  and ranks 5–9 add new-corpus coffee passages (Najdi dallahs, Jouf
  hospitality); the exact anchor page (bagar p98) fell out of the top 10.
  The ranker was deliberately not retuned for one seed case.
- Held-out benchmark (`evals/heldout_cases.json`): **11/12 = 91.7%**
  hit@5, identical to r1 — no regression. Trace:
  `%LOCALAPPDATA%\SardMCP\eval_heldout_cases_20260919-193546.json`.
  The single miss is the same pre-existing HELD-10 glossary gap
  (جوجل↔Google), still deliberately unfixed to keep the benchmark clean.
- New-corpus verification (11 live MCP-protocol queries over stdio,
  trace `%LOCALAPPDATA%\SardMCP\verify_r2.json`): Arabic questions hit
  rank 1 on exact target pages (Najran inscriptions p30, Makkah tiers
  p50, Jouf p11); English questions hit rank 1 (Darb Zubaidah p104,
  surface/typology p30 — after the `ara+eng` fix), rank 2 (Dumat
  al-Jandal), rank 4 (Farasan, above which sit correct r1 English
  Farasan passages). One English query (Ukhdood) lands at rank 7:
  cross-language ranking limitation, documented in LIMITATIONS.
- Tests: `pytest -q` (with `PYTHONUTF8=1` on this machine's cp1252
  console): **41 passed** — 34 carried over plus 7 new (OCR gate,
  derivation tagging, cache behaviour, parallel-render regression,
  schema migration, hit-derivation surfacing).

## Rev r1 results (preserved)

669 passages.

### Retrieval (r1)

- Seed fixtures (`evals/seed_cases.json`, development, NOT held out):
  **8/8** supporting-passage hit@5. Traces: `%LOCALAPPDATA%\SardMCP\eval_seed_cases_*.json`.
- Held-out benchmark (`evals/heldout_cases.json`, 12 supported + 8 traps,
  4 documents, AR+EN, authored after extraction from non-anchor passages,
  run once after tuning freeze): **11/12 = 91.7%** hit@5, meeting the ≥85%
  target. Trace: `%LOCALAPPDATA%\SardMCP\eval_heldout_cases_20260918-232135.json`.
  - The single miss (HELD-10, Arabic query → English Google-training page)
    is a probable glossary gap (no جوجل↔Google alias). Deliberately NOT
    fixed after the held-out run, to keep the benchmark clean. Listed in
    `docs/LIMITATIONS.md` as future work.
- Trap handling (manual judgment, all retrieved evidence sensible):
  freshness/scope/quote traps surface the relevant anchor passages so an
  agent can state the boundary; the geography trap surfaces the Near East
  title page (rank 3); regional traps retrieve the correctly-attributed pages.

### Latency (r1; 20 held-out queries, this machine)

| Mode | p50 | p95 | Notes |
|---|---|---|---|
| keyword-only (no key) | 6 ms | 6 ms | target <2 s ✓ |
| hybrid, warm (cached query vectors) | 20 ms | 20 ms | target <5 s ✓ |
| hybrid, cold (uncached embedding call) | ~1.2 s | ~2.2 s | provider-dependent |
| provider outlier (observed once, SEED-03) | — | 43 s | single slow call; cache absorbs repeats |

Cold-start and remote-provider timing are reported separately per the brief.
No failures or timeouts observed across ~60 paid calls.

### Tests (r1)

`uv run pytest -q`: 34 passed — normalization, chunking, storage/ledger,
search (filters, dedup, errors), engine-choice regression on rendered pages,
alias/hint behaviour, and live MCP protocol round-trips over stdio and
loopback HTTP (real subprocesses, fixture db, no network).
