# Sard MCP v0.1 — local Saudi cultural evidence server

Local MCP that lets existing agents (ChatGPT Work, Claude) ground Saudi
cultural answers, PDFs, and presentations in supplied Heritage Commission
publications. Sard returns evidence passages; the client agent writes the
artifacts. Built for the 21 September 2026 Ministry of Culture demo.

Start with `START_HERE.md`, then `docs/BUILD_BRIEF.md`.

## Fresh install (Windows)

```powershell
git clone https://github.com/NBTON/Sard-MCP.git
cd Sard-MCP
uv sync
copy .env.example .env   # then fill OPENROUTER_API_KEY in .env (never commit it)
uv run sard-import inventory            # read-only survey of the source PDFs
uv run sard-import dry-run --demo       # token + cost estimate (no writes, no paid calls)
uv run sard-import import --demo        # index the reviewed demo subset
uv run pytest -q                        # full suite incl. live protocol tests
```

Source PDFs live outside the repo (`SARD_SOURCE_DIR`, default
`C:\Users\nawaf\OneDrive - KFUPM\Culture`) and are only ever read.
The index, caches, and logs live outside the repo under
`%LOCALAPPDATA%\SardMCP` (`SARD_HOME`).

## Run

```powershell
uv run sard-mcp                        # stdio (Claude Desktop)
uv run sard-mcp --http --port 8765     # loopback streamable-HTTP (bridges)
uv run sard-import budget              # app ledger + provider key state
```

Client wiring: `docs/CLIENT_SETUP.md`. Instruction snippet for the
client: `docs/CLIENT_INSTRUCTIONS.md`.

## Corpus operations (CLI-only, never agent tools)

```powershell
uv run sard-import dry-run --docs "a.pdf,b.pdf"   # estimate before paying
uv run sard-import import --docs "a.pdf,b.pdf"    # index (cached, idempotent)
uv run sard-import import --all                   # everything that passes the gate
uv run sard-import import --docs "scan.pdf" --ocr # local Tesseract fallback for scanned PDFs
uv run python scripts/eval_seed.py                # dev fixtures (not held out)
uv run python scripts/eval_seed.py --seed evals/heldout_cases.json
```

Budgets: first indexing ≤ $1.00 estimated; cumulative app cap $3.00
(provider key limit is $4.00; $1.00 preserved). Embeddings are the only
paid calls; unchanged passages are never re-embedded.

## Reports

- `docs/EXTRACTION_NOTES.md` — engine comparison on rendered pages
- `docs/INGESTION_REPORT.md` — what is indexed, what is excluded, why
- `docs/COST_REPORT.md` — ledger, caps, cache behaviour
- `docs/EVAL_REPORT.md` — seed + held-out results, latency
- `docs/LIMITATIONS.md` — known gaps and next steps
- `docs/DEMO_SCORESHEET.md` — empty paired-run score sheet (runs pending)
