# Cost report (19 Sep 2026)

Model: `openai/text-embedding-3-small` via OpenRouter embeddings endpoint.
Measured price $0.02/M tokens (4-token probe cost $0.00000008).

## Ledger (all-time this build)

| Item | App ledger | Provider key |
|---|---|---|
| Committed spend | $0.003871 | $0.00387102 (matches) |
| Reserved (in-flight) | $0.000000 | — |
| Tokens embedded | 193,547 | — |
| Key limit / remaining | — | $4.00 / $3.9961 |

Caps: first indexing ≤ $1.00 estimated (expansion estimate was $0.0038);
cumulative app cap $3.00, preserving $1.00 of the $4.00 provider key limit
(the provider limit is the hard backstop; the key expires 2026-10-18).
No recharge was or will be made automatically.

## Where the money went

- Demo subset: 21 passages, 2,633 tokens, $0.000053.
- Expansion: 648 new passages, 189,774 tokens, $0.003795.
- Eval/demo queries: ~1,100 tokens (each query embedded once, then cached).

## Cache behaviour (verified)

- Passage vectors keyed by (passage, model, params, content hash):
  expansion re-import hit 16/16 cached demo passages (zero re-embed cost).
- Query vectors cached by (model, query): 32 queries cached; repeated eval
  runs cost $0 and return in ~20 ms.
- Every batch reserves worst-case cost (estimate × 1.5) before the request
  and commits provider-reported cost after; failures release the reserve.
  `usage_log` in the db records estimate vs reported per batch.

## Forward estimates (at $0.02/M, from inventory token sampling)

- Remaining quality-passing pages (~1,790: Atlal/bagAntiquities/
  bagHeritage-Commission/enternace rest): on the order of $0.01–0.03
  at current densities. Gate with `dry-run` before any batch.
- Regional booklets: blocked on extraction quality, not budget.
