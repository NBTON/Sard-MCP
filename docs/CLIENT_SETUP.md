# Client setup and integration status (19 Sep 2026)

## Status

| Surface | Route | Status |
|---|---|---|
| MCP stdio (protocol) | local subprocess | VERIFIED: initialize/tools-list/tools-call round-trip in `tests/test_server_stdio.py` |
| Streamable HTTP (protocol) | loopback 127.0.0.1 | VERIFIED: SDK-client round-trip in `tests/test_server_http.py` |
| Claude Desktop chat | local stdio server | PENDING USER: Claude Desktop is not installed on this machine (no `%APPDATA%\Claude` config, no running process). Config below is ready to paste. |
| ChatGPT Work | Secure MCP Tunnel or HTTPS dev bridge to loopback HTTP | PENDING USER: needs the demo Work account + tunnel/bridge step (below). |
| Claude Cowork / web | remote connector | NOT TESTED: separate route; Desktop success would not establish it. |

## Claude Desktop (stdio)

1. Install Claude Desktop and run it once so `%APPDATA%\Claude\claude_desktop_config.json` exists.
2. Merge this entry (keep any existing `mcpServers`):

```json
{
  "mcpServers": {
    "sard": {
      "command": "C:\\Users\\nawaf\\OneDrive - KFUPM\\Sard-MCP\\.venv\\Scripts\\sard-mcp.exe",
      "cwd": "C:\\Users\\nawaf\\OneDrive - KFUPM\\Sard-MCP",
      "env": { "PYTHONUTF8": "1" }
    }
  }
}
```

3. Fully quit and reopen Claude Desktop. The hammer/tools menu should list
   `search_saudi_culture`, `get_source_passage`, `get_corpus_coverage`.
4. Verify: ask "Use Sard: what does the corpus cover?" then
   "Use Sard: what does the source say about kleija?" Confirm cited PDF pages
   open to matching text. Paste `docs/CLIENT_INSTRUCTIONS.md` into the
   project's custom instructions.
5. If tools are missing: check the config path, restart the client, and run
   `uv run pytest tests/test_server_stdio.py` to confirm the server side.

## ChatGPT Work (needs the demo account)

1. On the demo machine, start the loopback endpoint:
   `uv run sard-mcp --http --port 8765` (binds 127.0.0.1 only).
2. In the exact ChatGPT Work account used for the demo, enable developer
   mode and attach the local server via Secure MCP Tunnel (tunnel ID,
   runtime key, permissions, workspace association), or an explicitly
   selected HTTPS development bridge to the loopback endpoint.
   References (checked 18 Sep 2026):
   - https://developers.openai.com/plugins/deploy/connect-chatgpt
   - https://developers.openai.com/api/docs/guides/secure-mcp-tunnels
3. Verify in Work: Sard tools discoverable, a search call returns evidence,
   and the agent can create a PDF/PPTX artifact with its own tools.
4. Do not expose the endpoint publicly and do not paste `OPENROUTER_API_KEY`
   anywhere except the local `.env`. OpenRouter credit is unrelated to
   tunnel/bridge credentials.

## Notes

- The MCP supplies evidence only; PDF/PPTX/DOCX files are created by the
  client's own agent tools. A content-only fallback must be labelled honestly.
- Record client name/version, model, timestamp, and tool traces for every
  demo run (see `docs/DEMO_AND_EVALUATION.md` and `docs/DEMO_SCORESHEET.md`).
