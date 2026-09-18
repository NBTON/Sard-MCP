# Evaluation report (19 Sep 2026, index r1, 669 passages)

## Retrieval

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

## Latency (20 held-out queries, this machine)

| Mode | p50 | p95 | Notes |
|---|---|---|---|
| keyword-only (no key) | 6 ms | 6 ms | target <2 s ✓ |
| hybrid, warm (cached query vectors) | 20 ms | 20 ms | target <5 s ✓ |
| hybrid, cold (uncached embedding call) | ~1.2 s | ~2.2 s | provider-dependent |
| provider outlier (observed once, SEED-03) | — | 43 s | single slow call; cache absorbs repeats |

Cold-start and remote-provider timing are reported separately per the brief.
No failures or timeouts observed across ~60 paid calls.

## Tests

`uv run pytest -q`: 34 passed — normalization, chunking, storage/ledger,
search (filters, dedup, errors), engine-choice regression on rendered pages,
alias/hint behaviour, and live MCP protocol round-trips over stdio and
loopback HTTP (real subprocesses, fixture db, no network).
