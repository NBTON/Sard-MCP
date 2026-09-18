# Sard MCP: coding-agent handoff

Prepared 18 September 2026. Target demonstration: Monday, 21 September 2026, Asia/Riyadh. These are planning and evaluation assets; the MCP has not been implemented or benchmarked.

## Read in order

1. [Build brief](docs/BUILD_BRIEF.md): scope, architecture, tool contracts, budget, schedule, acceptance.
2. [Corpus audit](docs/CORPUS_AUDIT.md): 17 PDFs, extraction risks, inspected evidence anchors.
3. [Demo and evaluation](docs/DEMO_AND_EVALUATION.md): identical baseline/enabled prompts, PDF and slide scenarios, scoring.
4. [Seed evaluation cases](evals/seed_cases.json): source-anchored development fixtures; not a held-out benchmark.

## Instruction to the implementing agent

Implement the local Sard MCP described in the build brief in this folder. First inspect existing files and Git state, preserve this handoff, verify the remote repository, and run the client-connectivity and PDF-extraction checks. Use the source PDFs read-only. Work through the brief's milestones, run meaningful acceptance checks, and document actual results. Do not report untested client support, unverified source links, or fabricated quality improvements. The three tools provide evidence; the user's existing agent creates the PDF, slides, and answers. Follow the explicit spending ceiling. If a client requires account access, finish all independent implementation and document the exact remaining connection step.

Remote repository supplied by the user: https://github.com/NBTON/Sard-MCP.git

Project folder: `C:\Users\nawaf\OneDrive - KFUPM\Sard-MCP`

Source folder: `C:\Users\nawaf\OneDrive - KFUPM\Culture`

At preparation time the project folder was empty and was not a Git checkout. Do not clone over these newly added files or assume the remote is empty. Inspect remote refs, then establish the checkout without overwriting this handoff. No commit, push, public endpoint, or paid API call was made during preparation.

## User preparation still needed

- Put an OpenRouter key in the implementing agent's local environment as `OPENROUTER_API_KEY`. Never paste it into a public issue, task brief, or committed file.
- Confirm developer-mode/custom-plugin access in the exact ChatGPT Work account used for the demonstration. A documented connection route does not prove account access.
- Confirm whether the Claude demonstration means Desktop chat or Cowork/web. Desktop supports local connections; the other surfaces require their documented remote connector route.
- Reserve a short review session to approve the cultural interpretations and the final demonstration outputs.

No hosting purchase is needed for the local core. ChatGPT Work access needs a supported bridge to the local server, described in the brief. Source PDFs and generated indexes must stay out of the public repository by default; use external corpus paths.
