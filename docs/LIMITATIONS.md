# Known limitations (19 Sep 2026, corpus rev r3)

1. **OCR passage noise (new corpus).** The 9,425 OCR passages (8,765 r2
   books + 660 r3 booklets) carry
   single-letter/word recognition errors (e.g. `الكشابات` for
   `والكتابات`), occasional dropped words, and residual 4+ letter Latin
   misreads; isolated 1–3 letter Latin fragments were filtered (~80%
   removed). Cleanliness is comparable to r1 raw-extraction noise, but
   verbatim quotes from OCR pages need render checks. No reviewed
   transcriptions exist yet for the r2/r3 books (pending the user review
   session, as in r1).
2. **English-against-Arabic ranking.** English queries over the
   Arabic-only new books depend on alias expansion + vector similarity:
   verified rank 1–2 for Darb Zubaidah, typology terms, and Dumat
   al-Jandal, rank 4 for Farasan, but rank 7 for Ukhdood (single alias
   term outscored by same-language r1 passages). Querying in Arabic, or
   naming the book via `doc_ids`, is more reliable for these books.
3. **Seed drift under growth.** Seed hit@5 moved 8/8 → 7/8 (r2) →
   6/8 (r3); held-out 11/12 → 10/12 (r3). All three misses are rank
   drift with evidence intact and topically-correct rivals: SEED-05
   coffee anchor out of the top 10 (rank 1 answers the query); SEED-08
   Riyadh anchor at ranks 8–9 behind a Safat-clock page that answers
   the query; HELD-08 English-castle anchor at ranks 6–7 behind Atlal
   fort pages. Page-exact hit@k is brittle at 21× corpus size; the
   ranker was not retuned.
4. **In-client runs pending.** MCP protocol verified over stdio and loopback
   HTTP with real round-trips, but no run inside Claude Desktop or ChatGPT
   Work has happened (Claude Desktop is not installed here; Work needs the
   demo account + tunnel/bridge step). Paired baseline/Sard comparisons and
   PDF/PPTX artifacts are therefore pending; see `docs/DEMO_SCORESHEET.md`.
5. **Regional booklets: OCR-indexed with residual gaps (r3).**
   al-baha, Hail, Tabuk, handi, major-arch, untangable, urban-major
   (250 approved pages, 660 passages) were imported via the r2 OCR path
   extended to font-corrupt pages. Five real content pages stay excluded
   (spread-layout confidence 55–59, no clean threshold); booklet spreads
   interleave both sides line-by-line (retrieval-OK, display quotes need
   care). Riyadh keeps only its reviewed p21 for the same font reason.
6. **Atlal indexed; enternace rest still out.** The 3 Atlal journals +
   bagAntiquities + bagHeritage-Commission are indexed (r3; 1,524
   approved pages). Still out: the unimported rest of
   enternace-to-west-old.pdf (the Near East book mixes
   Egyptian/Iraqi/Arabian content — needs geography care) and the
   Riyadh exclusion set.
7. **Raw-passage noise (r1 carried over).** English ligature splits
   (`co ffee`, `e fforts`), Arabic alef/hamza ordering defects, and
   mangled footers persist in non-reviewed passages. Search normalization
   absorbs the systematic cases; display quotes from raw pages need care.
   Only 6 pages have reviewed transcriptions (pending the user review session).
8. **Printed labels.** Verified for the 6 reviewed r1 pages; parsed from
   headers for bageng content pages (pattern validated 3/3). The 22 OCR
   books (15 r2 + 7 r3 booklets): PDF index only (OCR headers too noisy
   for label parsing). No blanket offset is ever assumed.
9. **Glossary gaps.** The EN↔AR alias table now covers the new regions
   and key sites (verified spellings), plus the r1 demo nouns; the
   held-out miss (HELD-10, جوجل↔Google) shows the boundary. Untracked
   transliterations fall back to vector similarity.
10. **Single-machine, online-embeddings.** The server, index, and key live on
    the demo machine; uncached queries need internet + OpenRouter. A 43 s
    provider outlier was observed once; caches absorb repeats.
11. **Individual source URLs unresolved.** Only the user-provided collection
    URL is recorded; per-publication links were not resolved — including
    for the 27 added books (15 r2 + 12 r3), whose publishers were verified
    from title pages but whose download provenance was not supplied.

R1 audit note: the r1 list (8 items) was renumbered and extended
above; no r1 limitation was closed except “local Arabic OCR (readiness
unchecked)”, which r2 validated as a working import path.
