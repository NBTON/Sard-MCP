# Known limitations (19 Sep 2026)

1. **In-client runs pending.** MCP protocol verified over stdio and loopback
   HTTP with real round-trips, but no run inside Claude Desktop or ChatGPT
   Work has happened (Claude Desktop is not installed here; Work needs the
   demo account + tunnel/bridge step). Paired baseline/Sard comparisons and
   PDF/PPTX artifacts are therefore pending; see `docs/DEMO_SCORESHEET.md`.
2. **Regional booklets unindexed.** al-baha, Hail, Tabuk, Riyadh (except the
   reviewed p21), handi, major-arch, untangable, urban-major (~321 content
   pages) fail extraction in all three engines (replacement-glyph font).
   Options: local Arabic OCR (readiness unchecked) or reviewed transcription
   of selected pages.
3. **Atlal + remaining books not yet indexed.** ~1,790 quality-passing pages
   await reading-order/geography verification (Atlal journals are bilingual
   academic volumes; the Near East book mixes Egyptian/Iraqi/Arabian content).
4. **Raw-passage noise.** English ligature splits (`co ffee`, `e fforts`),
   Arabic alef/hamza ordering defects, and mangled footers persist in
   non-reviewed passages. Search normalization absorbs the systematic cases;
   display quotes from raw pages need care. Only 6 pages have reviewed
   transcriptions (pending the user review session).
5. **Printed labels.** Verified for the 6 reviewed pages; parsed from headers
   for bageng content pages (pattern validated 3/3). Other books: PDF index
   only. No blanket offset is ever assumed.
6. **Glossary gaps.** The EN↔AR alias table covers demo proper nouns; the
   held-out miss (HELD-10, جوجل↔Google) shows the boundary. Untracked
   transliterations fall back to vector similarity.
7. **Single-machine, online-embeddings.** The server, index, and key live on
   the demo machine; uncached queries need internet + OpenRouter. A 43 s
   provider outlier was observed once; caches absorb repeats.
8. **Individual source URLs unresolved.** Only the user-provided collection
   URL is recorded; per-publication links were not resolved.
