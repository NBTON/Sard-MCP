# Ministry demonstration and evaluation pack

Prepared 18 September 2026. Prompts and criteria are ready; no baseline outputs, Sard outputs, or comparative scores have been generated. Source anchors below were inspected during preparation; they are guidance for evaluation, not invented citations to put in an answer without retrieval.

## Demonstration claim

Show that existing agents can turn the supplied cultural publications into useful answers, PDFs, and presentations while preserving evidence, geography, and source limitations. Measure the added value rather than assuming it. The agent's native artifact tools create the files; Sard supplies searchable evidence.

## Comparison design

For each task run a fresh baseline conversation and a fresh Sard-enabled conversation in the same client, with the same model/version, reasoning setting if exposed, language, prompt, artifact tools, web access, and time allowance. Use clean projects without prior Sard answers or corpus memory. Log any hidden model setting that cannot be controlled as unknown. Do not compare one vendor's baseline with another vendor's Sard run as if that isolates the MCP.

Use the exact prompts below in both conditions. In A, Sard is disconnected. In B, Sard is available. Keep the ordinary source/citation instruction identical; avoid coaching B with answer keys. Log whether the client actually called Sard. If it fails to discover the tool, report that as a discovery problem; any explicit @Sard rerun is a separate assisted condition.

- A: Normal agent with its usual tools, without Sard or the local corpus. Measures the value of adding curated evidence access.
- B: Same agent plus Sard. Record source IDs, retrieved pages, call timings, cost, and output files.
- C, for at least the main PDF and slide task: Same agent with the same relevant PDFs attached directly, without Sard. Measures whether structured retrieval offers value beyond simply providing the documents. Record any upload size/context limit; do not silently reduce C's evidence.

Allow ordinary web search equally in A and B, and record its use. If running a no-web controlled variant, disable web for both and label the variant. Use identical source-integrity and uncertainty instructions. A comparison with unequal access demonstrates the benefit of evidence access, not a universal reasoning improvement.

Keep complete unedited outputs. Where time allows, repeat the two principal tasks in both conditions twice; report variation and all runs. Predeclare these tasks and record any substitutions with reasons. Do not select only favorable outcomes. The local developer receives the seed questions, so they are development tests, not held-out evaluation.

## Five principal demo prompts

### D1: Arabic visitor briefing, PDF

> أنشئ ملف PDF عربيًا من صفحتين بعنوان «المجلس والقهوة: فهم الضيافة في سياقها الثقافي»، موجّهًا إلى وفد دولي يزور المملكة. اشرح الدور الاجتماعي للمجلس ودور القهوة في الضيافة، ثم اقترح أربعة إرشادات عملية للزائر وميّز بوضوح بين ما تقوله المصادر وما تقترحه أنت. استخدم المصادر المتاحة، وأرفق اسم المرجع ورقم الصفحة لكل معلومة ثقافية جوهرية متى أمكن. لا تعرض عادة محلية باعتبارها قاعدة موحّدة لجميع السعوديين. اجعل العربية سليمة واتجاه النص من اليمين إلى اليسار، وأدرج فقرة قصيرة تشرح حدود المعلومات.

Evaluator anchors: MAJLIS-95 and COFFEE-MIZMAR-96. Expected advantage to test: social context, traceable evidence, and a clear boundary between documented practice and suggested visitor behavior. These two pages do not support inventing a detailed universal coffee-serving ritual.

Artifact acceptance: actual two-page PDF, readable Arabic and citations, no clipped text, and inspectable source-to-claim mapping. If the client cannot export PDF, record that limitation; an outline is not a passed PDF task.

### D2: Ministry briefing, editable presentation

> أنشئ عرض PowerPoint عربيًا قابلًا للتحرير من ست شرائح بعنوان «من حفظ المباني إلى إشراك المجتمع: فرص تفعيل التراث العمراني». الجمهور فريق يعمل في القطاع الثقافي. نظّم العرض إلى: الفكرة الأساسية، مجالات العمل التي تصفها المصادر، أدوار الجهات والمجتمع، بناء القدرات، تجربة مقترحة صغيرة، وحدود الأدلة والمراجع. فرّق بوضوح بين البرامج الموثقة ومقترحاتك. لا تختلق أرقام أثر أو ميزانيات أو نتائج. أضف المراجع وأرقام الصفحات في ملاحظات المتحدث أو هوامش الشرائح. استخدم تصميمًا مهنيًا من دون شعارات توحي باعتماد رسمي.

Evaluator anchor: URBAN-45, with further corpus retrieval if available. Expected advantage to test: a usable Arabic synthesis of English source material, stakeholder distinctions, and recommendations labelled as proposals. Do not turn published program descriptions into claims that specific programs are currently funded or successful.

Artifact acceptance: editable six-slide PPTX, complete readable Arabic, factual references in notes/footers, source/proposal distinction, and no fabricated charts. Inspect every slide visually.

### D3: Regional food evidence, short answer

> ما الذي تذكره المصادر المتاحة عن الكليجا والحنيني وكبيبة حائل؟ قدّم جدولًا موجزًا يوضح المكونات المذكورة، والارتباط الجغرافي عندما يصرّح به المصدر، ومرجع كل صف. لا تحوّل وصف المكونات إلى وصفة كاملة، ولا تفترض منطقة منشأ إذا لم يذكرها المصدر.

Evaluator anchor: FOOD-84. Expected behavior: Qassim attribution for kleija; mashed dates and wheat-bread description for hanini without inventing a region from this page; vine leaves, meat, and rice for Hail kubayba. Preserve the distinction between an association and an exclusive origin claim. Do not hallucinate weights or cooking instructions.

### D4: International audience, bilingual interpretation sheet

> Create a one-page bilingual Arabic-English interpretation sheet about the historical significance of Qasr al-Hukm in Riyadh. Explain its role in the city and describe two associated landmarks supported by the available evidence. Keep historical descriptions separate from current visitor information. Cite publication titles and page numbers where available. If opening hours or access conditions cannot be verified, say so. Deliver a PDF with balanced Arabic and English typography.

Evaluator anchor: RIYADH-40. Expected advantage to test: historically grounded details, correct PDF-versus-printed-page citation, and no invented live visitor information. Check that translations preserve proper names and factual qualifiers.

### D5: Educational content and regional specificity

> صمّم نشاطًا تعليميًا مدته 15 دقيقة للمرحلة الثانوية يعرّف الطلاب بالفرق بين الممارسة الاجتماعية وفن الأداء، مستخدمًا المجلس والمزمار مثالين. أدرج هدفين للتعلّم، شرحًا موجزًا، وثلاثة أسئلة مع إجاباتها. انسب الأمثلة جغرافيًا فقط بقدر ما تسمح به المصادر، واذكر المراجع والصفحات. ميّز الأنشطة التعليمية التي تقترحها عن المعلومات المنقولة من المصادر.

Evaluator anchors: MAJLIS-95 and COFFEE-MIZMAR-96. Test western-region attribution for mizmar without labelling every example Najdi or generalizing geography. The proposed activity itself does not require a source citation; its cultural assertions do.

## Additional stress prompts

1. «أعطني مقادير وصفة الكليجا بالغرام كما وردت في المرجع، وحدّد الصفحة.» The inspected food page has no gram quantities. Search the available corpus, then state whether a real recipe was found; do not infer unsupported measurements.
2. «هل يثبت وصف الكليجا في المصادر أنها لا تُصنع خارج القصيم؟» Distinguish regional association from exclusive distribution.
3. «هل توجد في المصادر عبارة: جميع السعوديين يقدّمون القهوة بالطريقة نفسها؟ أعطني اقتباسًا حرفيًا إن وُجد.» Do not fabricate the quotation; a fruitless search is not universal proof of nonexistence.
4. «ما ساعات زيارة قصر الحكم يوم الاثنين 21 سبتمبر 2026؟» Historical PDFs alone cannot verify this. If browsing is enabled, verify separately and cite the current source; otherwise state the limitation.
5. “Does a book about ancient Egypt and Iraq become evidence about Saudi customs merely because it is hosted by a Saudi cultural institution?” Require content geography and source attribution to remain distinct.
6. “Translate the source's discussion of heritage restoration funding into Arabic without adding budget figures or a claim of proven economic impact.” Anchor URBAN-45.
7. «اذكر الفرق بين رقم الصفحة في ملف PDF ورقم الصفحة المطبوع في دليل الرياض عند الإشارة إلى منطقة قصر الحكم.» Anchor PDF page 21 / printed 40, not a universal offset rule.

## Scoring rubric

Score each output 0-5 per dimension. 0 = absent/incorrect; 1 = major defects; 2 = substantial corrections needed; 3 = usable with corrections; 4 = strong with minor issues; 5 = all applicable checks met. Mark genuinely inapplicable dimensions N/A and renormalize the applicable weights identically for the paired outputs.

| Dimension | Weight | What to inspect |
|---|---:|---|
| Factual support and accuracy | 30% | Do the actual source passages support the material claims? |
| Citation traceability | 25% | Can a reviewer locate the publication and correct page? Are quotes faithful? |
| Regional/contextual precision | 15% | Avoids confusing region, period, institution, author opinion, and nationwide practice |
| Treatment of gaps and proposals | 15% | Separates documented facts, proposals, and unverifiable/current information |
| Usefulness for the audience | 10% | Direct, actionable structure and clear Arabic/English |
| Artifact usability | 5% | Real editable/openable file, readable layout, RTL, no clipping |

Weighted score out of 100 = sum(weight * dimension score / 5), adjusted for N/A. Report factual and provenance sub-scores separately so attractive layout cannot hide poor grounding. A major false attribution, invented quotation, or fabricated source is a critical defect regardless of total score.

For each artifact enumerate its checkable cultural claims and map them to evidence. Report supported / total assessed claims and correct source locations / total citations. Treat no citations as zero provenance, not perfect precision. Assess all material claims in these short artifacts, rather than cherry-picking five easy ones.

Development success targets: at least 4/5 average for factual support and traceability, no critical defects in selected demo outputs, and measurable improvement over A on those dimensions. Desired comparison improvement: 15 percentage points or more on the weighted score, subject to baseline ceiling effects; this is a target, not a result to manufacture. If A already performs well, show narrower provenance/workflow benefits or a tie honestly. C may outperform Sard; report it.

## Held-out retrieval benchmark

Build a separate 20-question set after extraction, across at least four documents, with Arabic and English questions and explicit source-page answers. Reserve 12 supported questions plus 8 regional/out-of-scope/freshness traps; report categories separately. A reviewer should select the set before final tuning. Never describe the supplied seed cases as unseen.

Measure supporting-passage hit rate at 5 on supported questions (target at least 85%, i.e. 11/12 for that split); exact source-location integrity; cross-language retrieval results; and honest gap handling. Expand beyond this small sample later; it cannot establish performance across Saudi culture as a whole.

## Presentation sequence: approximately 8 minutes

1. State the concept and demonstrate that the same existing agent is used in both conditions.
2. Show D3 live: ask, inspect the answer, open its cited PDF page, and explain what is and is not supported.
3. Show saved, real D1 and D2 paired outputs: compare a few predeclared claims and their sources. Label saved outputs as rehearsed runs.
4. Show one limitation prompt live so the audience can see evidence boundaries.
5. Present actual scores, corpus coverage/exclusions, and the future hosting step.

Keep saved actual outputs as a network-failure fallback. Never label cached evidence or prerecorded outputs as live retrieval. The locally hosted server still needs the machine running, any selected bridge connected, and internet for uncached embedding calls.

## Results to save during implementation

For each condition/task/run: client and version, model/settings when visible, timestamp, prompt hash, enabled tools/web state, corpus revision, duration, tool trace, embedding usage/cost, output files, claim-evidence table, reviewer scores, and limitations. Save a before-after score sheet with empty cells until runs happen. No scores or improvement claims exist yet.
