# PRIOR ART: projects and evidence we build on

Owner: lead (Claude), to be extended by the research agent (kb/prompts/10_prior_art.md). Accessed 3 Oct 2026.
Purpose: show judges we build on what already works, cite it, and position Jani precisely. Every line has a source.

## 1. Direct evidence for our design choices

### 1.1 Multi-leaf sampling beats single-leaf diagnosis (PlantVillage Nuru, Kenya and Tanzania)
Mrisho et al. (2020), "Accuracy of a Smartphone-Based Object Detection Model, PlantVillage Nuru, in Identifying the Foliar Symptoms of the Viral Diseases of Cassava: CMD and CBSD", Frontiers in Plant Science. https://www.frontiersin.org/journals/plant-science/articles/10.3389/fpls.2020.590889/full (PubMed 33391304). Field sites included Busia County, Kenya.
- "Nuru could diagnose symptoms of cassava diseases at a higher accuracy (65% in 2020) than the agricultural extension agents (40-58%) and farmers (18-31%)".
- Single-leaf accuracy was poor (21% for CBSD, 52 to 59% for CMD).
- "Nuru's accuracy in diagnosing cassava disease and pest symptoms, in the field, was enhanced significantly by increasing the number of leaves assessed to six (74-88%)".
**Use in Jani:** our 10-leaf plot check is not arbitrary; it follows published East African field evidence that aggregating several leaves raises accuracy sharply. Also supports "the model is a triage aid, the officer decides". Different crop (cassava), so we cite it as design precedent, not as our accuracy.

### 1.2 Kenya already has a national farmer registry (KIAMIS)
FAO news, 12 Jan 2026: https://www.fao.org/agroinformatics/news/news-detail/official-handover-of-kiamis-to-the-government-of-kenya--a-new-era-for-digital-agriculture/en
- KIAMIS (Kenya Integrated Agriculture Management Information System) is "an integrated system capable of supporting multiple services over time, including farmer registration, input management, advisory services and links to markets and finance."
- By mid-2025 it had registered "over 6.5 million farmers"; the farmer registration module was handed from FAO to the Government of Kenya in November 2025. Built by FAO with the Ministry of Agriculture and Livestock Development, funded by the Embassy of Sweden.
- Phase two (Aug 2025) targeted 500,000 more farmers: https://www.kenyanews.go.ke/government-embarks-on-registration-drive-to-onboard-500000-farmers-into-kiamis/
**Use in Jani:** Annex B says the binding constraint is often "the absence of a working farmer registry". In Kenya it exists. Jani's referral carries the cooperative member number today and can carry a KIAMIS ID tomorrow; officer-confirmed referrals could flow into KIAMIS advisory services. This is our institutional fit and scale path.

### 1.3 World Bank's own framing (Nov 2025 report)
"Harnessing Artificial Intelligence for Agricultural Transformation", World Bank, 25 Nov 2025. https://www.worldbank.org/en/topic/agriculture/publication/harnessing-artificial-intelligence-for-agricultural-transformation ; document: https://documents.worldbank.org/en/publication/documents-reports/documentdetail/099110225213024234
- "AI must be used where it truly adds value."
- Recommends to "Direct research funding toward building AI models with local institutions in low- and middle-income countries, focusing on crops, languages, and supply chains that global models often overlook."
**Use in Jani:** quote in Video 1 ("our take") and README. Our deliberate non-AI choices (rules, calendar, price lookup) are exactly "where it truly adds value".

## 2. World Bank AI Repository entries (agriculture)
Repository: https://airepository.worldbank.org (lists render by JavaScript; individual pages are at /use-case/<slug>).

| Entry | Country | What | Relevance to Jani |
|---|---|---|---|
| Virtual Agronomist (iSDA) https://airepository.worldbank.org/use-case/virtual-agronomist | Kenya, Uganda, Tanzania, Zambia, Malawi, Ghana, Rwanda | Prescriptive AI + computer vision via WhatsApp, built on iSDAsoil (open, CC BY 4.0, ~30 m). Reported 2.7 to 4.7x profit with full implementation (as stated on the page). | Needs WhatsApp and data; Jani covers the offline, basic-phone gap. iSDAsoil is in Annex B: candidate soil layer for the outlier map. |
| FAO GAEZ v4 https://airepository.worldbank.org/use-case/fao-gaez-v4-ai-enhanced-global-agro-ecological-zone-mapping | Global | AI-enhanced agro-ecological zoning | Context only. |
| Xnext https://airepository.worldbank.org/use-case/xnext-x-ray-ai-enabled-inspection-system-aimed-detecting-contaminants-real-time-during | n/a | X-ray inspection in food processing | Not relevant. |
| (rest to be scraped, see kb/prompts/10_prior_art.md) | | | |

## 3. Positioning (draft, one paragraph for README)
Nuru showed that offline phone diagnosis works in East Africa when several leaves are assessed and an extension system stands behind it. Virtual Agronomist showed that localised advice raises yields when farmers can reach it on WhatsApp. KIAMIS shows Kenya has the registry. Jani's contribution is the missing piece for the farmer the brief describes: a basic phone most of the week, a smartphone at weekends, no data bundle, a home language few tools speak. Plus the cooperative's own delivery records turned into "is it me, or is it everyone?".

## 4. What happens next (for the submission)
The AI Repository has a submission form: https://airepository.worldbank.org/ai-use-case-submit . Listing Jani there after the hackathon is a concrete "what next".
