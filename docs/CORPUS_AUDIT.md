# Initial corpus audit

Prepared 18 September 2026. This is a preliminary inventory and selected-page inspection, not a completed extraction or ingestion audit.

## Inventory

17 PDFs; 2,774 PDF pages; 573,411,566 bytes (546.85 MiB). Large file size often reflects images and does not establish embedding cost.

Source directory: `C:\Users\nawaf\OneDrive - KFUPM\Culture`

The user states that all files came from https://culturalhub.moc.gov.sa/ar-SA/HeritageBookListing and permits their use with external processing for this demo. The page could not be retrieved during preparation. Treat this as a user-supplied collection URL, not a verified individual source URL or a redistribution license. No source files were edited.

| File | PDF pages | MiB |
|---|---:|---:|
| al-baha.pdf | 27 | 3.60 |
| Atlal-30-web-pdf.pdf | 376 | 12.02 |
| atlal21.pdf | 383 | 15.61 |
| atlal32.pdf | 530 | 16.64 |
| bag-Intangible-Heritage.pdf | 170 | 62.80 |
| bagAntiquities.pdf | 152 | 65.86 |
| bagarUrban-and-Handicrafts.pdf | 194 | 65.14 |
| bagengUrban-Heritage-1-1.pdf | 92 | 80.83 |
| bagHeritage-Commission.pdf | 208 | 86.89 |
| enternace-to-west-old.pdf | 299 | 97.24 |
| Hail.pdf | 28 | 4.90 |
| handi.pdf | 31 | 7.51 |
| major-arch.pdf | 56 | 7.20 |
| Riyadh.pdf | 41 | 3.77 |
| Tabuk.pdf | 50 | 3.73 |
| untangable.pdf | 84 | 6.74 |
| urban-major.pdf | 53 | 6.39 |

## What was inspected

All files opened with pypdf and yielded page counts. Text was sampled at the start, early pages, and midpoint. Additional selected pages were compared using pdfplumber and PDFium. Seven page images were rendered and inspected: intangible heritage PDF page 86; Riyadh PDF page 21; crafts PDF pages 97 and 98; English urban heritage PDF page 47; Near East book PDF pages 2 and 150.

This does not establish that every page is searchable or accurate. No file has been fully indexed, and no embedding API calls were made.

## Material findings

1. Several Arabic samples contain incomplete words, replacement characters, detached ligatures, or omitted line portions. For example, pypdf extracted 576 characters from Riyadh PDF page 21, while pdfplumber yielded 1,642 and PDFium 1,695; the additional text also has ordering/character defects. Character count alone cannot select the best extraction.
2. pdfplumber produced reversed Arabic word sequences on inspected pages. PDFium produced reversed English word order for the English urban heritage sample. Choose and validate extraction behavior by script/layout; do not apply blanket reversal.
3. Some files contain two-page spreads. Riyadh PDF page 21 contains a printed page labelled 40 on the right and a photo on the left. A blanket numerical offset between PDF index and printed page is unsafe.
4. PDF page 150 of `enternace-to-west-old.pdf` is visually blank. Other sampled pages contain text. Do not classify the book as an image-only scan from the blank page.
5. The Near East book includes ancient Egypt and Iraq as well as broader subject matter. Its PDF page 2 identifies the title as `المدخل إلى فنون الشرق الأدنى القديم (مصر-العراق-الجزيرة العربية)`. Its publisher location does not make all its content Saudi heritage. Its front matter attributes the information to the author unless otherwise stated.
6. Photo attribution exists in the publications. Do not assume evidence retrieval also grants blanket permission to reuse every photo in public marketing. The initial demo can use typography and simple diagrams without copying book photography.
7. Historical registration dates and program descriptions in these books are source-dated claims, not evidence of current registration status, opening hours, or event schedules.

## Reviewed anchors for development examples

These are selected evidence anchors, not a comprehensive answer key.

| Anchor | File | PDF page (1-based) | Printed label | Supported use |
|---|---|---:|---|---|
| FOOD-84 | bag-Intangible-Heritage.pdf | 86 | 84 | The page describes kleija with Qassim attribution, hanini ingredients, and Hail kubayba ingredients. It does not provide full recipes, ingredient weights, or nutrition. |
| MAJLIS-95 | bagarUrban-and-Handicrafts.pdf | 97 | 95 | Social functions of the majlis: receiving guests, meetings, discussion, dispute resolution, occasions, and social connection. Preserve the source's phrasing/scope. |
| COFFEE-MIZMAR-96 | bagarUrban-and-Handicrafts.pdf | 98 | 96 | Coffee as hospitality and livelihood; mizmar associated with the western region. The page states registration years 2015 and 2016 respectively; describe them as what this source states. |
| URBAN-45 | bagengUrban-Heritage-1-1.pdf | 47 | 45 | Local initiatives, heritage towns/villages, historic downtowns and markets, multiple funding participants, and training for restoration workers. No quantitative impact evaluation is given on this page. |
| RIYADH-40 | Riyadh.pdf | 21 | 40 (right side of spread) | Qasr al-Hukm's historical role, associated places, Safat clock, and reconstruction context for Thumairi Gate. No current opening schedule is established. |

Citations should prefer verified publication title + PDF page + printed label where known. Preserve filename as an exact source locator. Resolve individual public document URLs later; a collection URL cannot identify a page by itself.

## Ingestion priorities

1. Quality-approved passages from the five anchors above: enough to prove the demo workflows and extraction/citation handling.
2. Expand across the associated publications, with page-level quality checks.
3. Regional booklets and archaeological reports, after confirming reading order and geography.
4. Keep poorly extracted pages excluded and reported until repaired by verified extraction/OCR/transcription.

Local OCR can be an option, but OCR readiness and Arabic model availability have not been checked. No paid OCR service is selected. Any reviewed transcription must be labelled with its derivation and mapped back to the unchanged PDF page. Never fill unreadable source text from general model knowledge.

## Outstanding source work

- Full page-level readability report and duplicate checks.
- Confirm exact publication titles, authors, dates, and calendars from front matter.
- Resolve individual document URLs, leaving unresolved ones explicit.
- Build searchable text with original and normalized versions.
- Visually verify all passages used in the Ministry demonstration.
- Generate token/cost estimates from accepted chunks before paid indexing.

