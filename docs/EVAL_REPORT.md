# Evaluation report (19 Sep 2026, index r2, 9,434 passages)

## Rev r2 runs (new; r1 results preserved below)

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
