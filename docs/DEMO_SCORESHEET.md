# Paired demo score sheet (empty — runs pending in-client)

Per `docs/DEMO_AND_EVALUATION.md`: same client/model/settings/prompt in all
conditions; fresh conversations; log tool traces. Fill only from real runs.

## D1: Arabic visitor briefing (PDF)

| | A baseline | B +Sard | C +PDFs attached |
|---|---|---|---|
| Client/model/date | | | |
| Sard calls (n, pages) | n/a | | n/a |
| Factual support /5 | | | |
| Citation traceability /5 | | | |
| Regional precision /5 | | | |
| Gaps+proposals /5 | | | |
| Usefulness /5 | | | |
| Artifact usability /5 | | | |
| Weighted /100 | | | |
| Critical defects | | | |
| Output file | | | |

## D2: Ministry briefing (PPTX)

| | A baseline | B +Sard | C +PDFs attached |
|---|---|---|---|
| Client/model/date | | | |
| Sard calls (n, pages) | n/a | | n/a |
| Factual support /5 | | | |
| Citation traceability /5 | | | |
| Regional precision /5 | | | |
| Gaps+proposals /5 | | | |
| Usefulness /5 | | | |
| Artifact usability /5 | | | |
| Weighted /100 | | | |
| Critical defects | | | |
| Output file | | | |

## D3/D4/D5 + stress prompts

| Task | Condition | Output | Supported claims | Correct locations | Notes |
|---|---|---|---|---|---|
| D3 food table | A | | / | / | |
| D3 food table | B | | / | / | |
| D4 Qasr sheet | A | | / | / | |
| D4 Qasr sheet | B | | / | / | |
| D5 school activity | A | | / | / | |
| D5 school activity | B | | / | / | |
| Stress (each) | B | | | | |

## Sard-side evidence traces (local, pre-run for rehearsal)

Representative decomposed queries per demo task were run against the live
index; traces under `%LOCALAPPDATA%\SardMCP\demo_traces\` (see table below).
These show what evidence Sard returns — they are NOT paired client runs.

| Task | Query run | Top evidence | Trace |
|---|---|---|---|
| D1 | المجلس… / القهوة… | p097:00 #1, p098:00 #1 | demo_traces/D1-majlis_*.json |
| D2 | local initiatives… / دعم المبادرات… | p047:00 #1 / #2 | demo_traces/D2-urban_*.json |
| D3 | الكليجا الحنيني كبيبة… | p086:02 #1, p086:01 #3 (kleija needs a follow-up query; SEED-01 covers it) | demo_traces/D3-food_*.json |
| D4 | Qasr al-Hukm Safat… | Riyadh p021:08 #1, p021:03 #2 | demo_traces/D4-qasr_*.json |
| D5 | المزمار… / المجلس… | p098:01 #1, p097:00 #1 | demo_traces/D5-school_*.json |
