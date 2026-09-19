# Known limitations (19 Sep 2026, corpus rev r2)

1. **OCR passage noise (new corpus).** The 8,765 OCR passages carry
   single-letter/word recognition errors (e.g. `الكشابات` for
   `والكتابات`), occasional dropped words, and residual 4+ letter Latin
   misreads; isolated 1–3 letter Latin fragments were filtered (~80%
   removed). Cleanliness is comparable to r1 raw-extraction noise, but
   verbatim quotes from OCR pages need render checks. No reviewed
   transcriptions exist yet for the new books (pending the user review
   session, as in r1).
2. **English-against-Arabic ranking.** English queries over the
   Arabic-only new books depend on alias expansion + vector similarity:
   verified rank 1–2 for Darb Zubaidah, typology terms, and Dumat
   al-Jandal, rank 4 for Farasan, but rank 7 for Ukhdood (single alias
   term outscored by same-language r1 passages). Querying in Arabic, or
   naming the book via `doc_ids`, is more reliable for these books.
3. **Seed drift under growth.** Seed hit@5 moved 8/8 → 7/8 (SEED-05
   coffee query: same-document coffee passages still rank 1–2, but the
   exact anchor page left the top 10). Held-out is unchanged at 11/12.
   Page-exact hit@k is brittle at 14× corpus size; the ranker was not
   retuned.
4. **In-client runs pending.** MCP protocol verified over stdio and loopback
   HTTP with real round-trips, but no run inside Claude Desktop or ChatGPT
   Work has happened (Claude Desktop is not installed here; Work needs the
   demo account + tunnel/bridge step). Paired baseline/Sard comparisons and
   PDF/PPTX artifacts are therefore pending; see `docs/DEMO_SCORESHEET.md`.
5. **Regional booklets unindexed.** al-baha, Hail, Tabuk, handi,
   major-arch, untangable, urban-major (~280 content pages) fail
   extraction in all engines (replacement-glyph font). Local Arabic OCR
   is now a proven path (r2) and is the recommended next step; Riyadh
   keeps only its reviewed p21 for the same reason.
6. **Atlal + remaining books not yet indexed.** ~1,790 quality-passing pages
   await reading-order/geography verification (Atlal journals are bilingual
   academic volumes; the Near East book mixes Egyptian/Iraqi/Arabian content).
7. **Raw-passage noise (r1 carried over).** English ligature splits
   (`co ffee`, `e fforts`), Arabic alef/hamza ordering defects, and
   mangled footers persist in non-reviewed passages. Search normalization
   absorbs the systematic cases; display quotes from raw pages need care.
   Only 6 pages have reviewed transcriptions (pending the user review session).
8. **Printed labels.** Verified for the 6 reviewed r1 pages; parsed from
   headers for bageng content pages (pattern validated 3/3). The 15 new
   books: PDF index only (OCR headers too noisy for label parsing).
   No blanket offset is ever assumed.
9. **Glossary gaps.** The EN↔AR alias table now covers the new regions
   and key sites (verified spellings), plus the r1 demo nouns; the
   held-out miss (HELD-10, جوجل↔Google) shows the boundary. Untracked
   transliterations fall back to vector similarity.
10. **Single-machine, online-embeddings.** The server, index, and key live on
    the demo machine; uncached queries need internet + OpenRouter. A 43 s
    provider outlier was observed once; caches absorb repeats.
11. **Individual source URLs unresolved.** Only the user-provided collection
    URL is recorded; per-publication links were not resolved — including
    for the 15 new books, whose publishers were verified from title pages
    but whose download provenance was not supplied.

R1 audit note: the r1 list (8 items) was renumbered and extended
above; no r1 limitation was closed except “local Arabic OCR (readiness
unchecked)”, which r2 validated as a working import path.
