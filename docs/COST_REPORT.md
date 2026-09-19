# Cost report (19 Sep 2026, corpus rev r2)

Model: `openai/text-embedding-3-small` via OpenRouter embeddings endpoint.
Measured price $0.02/M tokens (4-token probe cost $0.00000008).

## Ledger (all-time, after the r2 update)

| Item | App ledger | Provider key |
|---|---|---|
| Committed spend | $0.189813 | $0.189813 (matches) |
| Reserved (in-flight) | $0.000000 | — |
| Tokens embedded | 9,490,646 | — |
| Key limit / remaining | — | $4.00 / $3.8102 |

Caps (unchanged, still enforced): first indexing ≤ $1.00 estimated;
cumulative app cap $3.00, preserving $1.00 of the $4.00 provider key limit
(the provider limit is the hard backstop; the key expires 2026-10-18).
No recharge was or will be made automatically. Remaining headroom under
the app cap: ~$2.81.

## Where the money went

- r1 demo subset: 21 passages, 2,633 tokens, $0.000053.
- r1 expansion: 648 new passages, 189,774 tokens, $0.003795.
- r2 OCR pass 1 (ara-only, superseded): 9,231 passages, 3,183,910 tokens, $0.063678.
- r2 OCR pass 2 (ara+eng, superseded): 8,786 passages, 3,171,666 tokens, $0.063433.
- r2 final (ara+eng + fragment filter): 8,026 passages, 2,941,141 tokens, $0.058823.
- Eval/verification queries: the remainder (~1,500 tokens, each embedded once, then cached).

Superseded passes are preserved in `usage_log` (append-only); the live
index holds exactly one vector per passage (9,434 vectors, 0 orphans).
Repeat imports embed 0 new passages ($0.00).

## Cache behaviour (verified)

- Passage vectors keyed by (passage, model, params, content hash):
  expansion re-import hit 16/16 cached demo passages (zero re-embed cost).
- Query vectors cached by (model, query): 32 queries cached; repeated eval
  runs cost $0 and return in ~20 ms.
- Every batch reserves worst-case cost (estimate × 1.5) before the request
  and commits provider-reported cost after; failures release the reserve.
  `usage_log` in the db records estimate vs reported per batch.

## Forward estimates (at $0.02/M, from inventory token sampling)

- Remaining quality-passing extraction pages (~1,790: Atlal/
  bagAntiquities/bagHeritage-Commission/enternace rest): on the order of
  $0.01–0.03 at current densities. Gate with `dry-run` before any batch.
- Regional booklets + any further scanned books: local OCR is now a
  proven path (r2: 4,560 pages, $0 OCR cost, ~$0.02/M-token embedding).
  Unindexed scanned pages embed at ~800 tokens/page → budget ~$0.016 per
  1,000 pages plus queries.
