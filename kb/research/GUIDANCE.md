# GUIDANCE: coffee agronomy for the answer bank

Owner: research agent. Hand-off to content-voice. Accessed 3 Oct 2026. Source IDs point to `sources.json`.
Scope rule: no product brands, no doses, no spray quantities. Where a source names a brand or a dose I do not repeat it here.
Every line below is a quote or a close paraphrase marked as such. Content-voice must still get officer sign-off before anything reaches Noor.

## 0. Read this first (gaps)

| Topic | Kenyan primary source found? | Status |
|---|---|---|
| Coffee leaf rust: symptoms, timing, cultural control, copper timing, repeat interval | Yes (S03 Agronomy 2021 review by Coffee Research Institute authors, S17 Infonet Biovision/icipe) | Good |
| Cercospora (brown eye spot) | **No Kenyan source** after pass 2. CABI/Plantwise paywalled, Infonet has no coffee page, KALRO none. Pacific fact sheet (S18) and a Plantwise snippet (S44). | Weak. Symptoms and cause only. Treatment: "ask the officer" |
| Phoma | **No Kenyan source** after pass 2. CABI empty, Infonet none, KALRO none. Two secondary non-Kenyan pages (S42, S43). | Weak. Symptoms and the cool, windy, highland pattern only. Treatment: "ask the officer" |
| Leaf miner | **Yes: Kenyan extension text (S17 Infonet, icipe).** Species in Kenya are L. meyricki and L. caffeina. | Good for symptoms and "do not spray on your own". Treatment: "ask the officer" |
| Coffee berry disease (symptoms only, out of scope) | Yes (S17 Kenya-based, S19 Ethiopian paper) | Good enough for "out of scope" card |
| Published action threshold (% of leaves affected) | **No.** None found for Kenya. | NOT FOUND. Mark every threshold "assumption, officer to confirm" |
| PPE for spraying, general | Yes (S20 FAO/WHO 2020) | Good, general terms |

---

## 1. Coffee leaf rust (Hemileia vastatrix)

### 1.1 What it looks like
- S03 (Agronomy 2021): "Yellow to orange powdery blotches appear on the underside of leaves, with corresponding chlorotic patches on the upper side. Initially, these are only 2-3 mm diameter, but steadily expand, coalesce, the centers of older lesions become necrotic and the sporulating zone is restricted to the outermost zone". (Source uses an en dash in "2-3".)
- S03: "Young lesions may appear as small chlorotic spots before sporulation occurs".
- S03: "The major effect of CLR is defoliation which reduces the photosynthetic area."
- S17 (Infonet Biovision, icipe): "Yellow to orange powdery blotches appear on the underside of leaves, chlorotic patches appear on the upper side. They grow from 2-3 mm diameter to several centimetres. On older leaves, several lesions can merge together."
- S16 (CABI PlantwisePlus): "Trees infected with coffee rust develop yellow spots on the upper side of their leaves and an orange rust-like powder on the underside."
- Where to look: the **underside** of the leaf. This matters for the photo protocol (photograph the underside too, or say so as a limit). Not a decision for me; flag for ml and engine.

### 1.2 How it spreads (useful for the 10-leaf sampling)
- S16: "Wind and rain easily transport the powdery fungus spores. Humans can also help spread coffee rust, particularly farmworkers, as the spores can stick to clothes when moving around the plants."
- S03: "The spread of the disease within a farm is mainly by rain splash and reduction of the infectivity of the spores at the start of rains can greatly reduce the development of an epidemic".
- S17: "Leaf rust is favoured by wet, warm weather. Rainstorms of 7.5 mm or more are needed to cause disease outbreak."
- S03, East of the Rift Valley (the Nyeri side): "the long rains start in March through May and short rains start in October through December resulting in two CLR peaks in May to June and January to March". So the risk is highest soon after each rainy season, and sprays go on before it.
- S03: "Rainfall distribution is more influential in the progression of the disease whereby light and broken rain is more favorable than continuous rain".

### 1.3 When to act (timing against the rains)
- S03: "Following the rainfall patterns in the main coffee growing regions, fungicide sprays for CLR control in Kenya starts in mid-October, just before the start of short rains followed by a second spray, three weeks after the first spray [35,44]. These two sprays reduce the production of new spores leading to low inoculum potential at the beginning of the long rains [67]."
- S03: "For the long rain period, the first spray is applied in late February or early March followed by one or two sprays at three weeks intervals for copper formulations and four-week intervals for other formulations."
- S03: "However, the spray program needs to be monitored and varied in response to weather patterns [67] because climate change is affecting the rainfall amounts and distribution."
- S17: "Spray with copper before the onset of rains, open pruning and good weeding."
- S17: "For emergencies use copper sprays at 21 days intervals starting just before flowering."
- S35 (KALRO Coffee Research Institute post, **snippet only, not opened**): "Farmers are advised to apply copper-based fungicides before the onset of the rains when the disease is most likely to spread". Corroborates S03 and S17. Secondary.
- Dates for Nyeri: NASA POWER puts the median start of the short rains at about 16 Oct and the long rains at about 20 Mar (see `season.json`). That is consistent with the published mid-October and late-February to early-March spray starts.

### 1.4 Repeat interval
- Copper: three weeks (S03, S17 "21 days"). Other formulations: four weeks (S03). **Product and dose are not ours to give.** S03 says the national register does it: "After evaluation, PCPB uses the CRI report to register the fungicide and provides farmers with a list of registered products, indicating the recommended rates as well as the proper timing of application." (PCPB is the Pest Control Products Board.) So the card should say: ask the cooperative or officer which registered product and dose.
- S03 also warns: "Systemic formulations are applied only twice in a season to reduce the risk of the development of resistance." and "The use of these compounds needs to be alternated to avoid the development of tolerant strains of the pathogen". Do not put this on a farmer card; it is for the officer.
- S03 frames chemicals as a last resort: "Efforts continue to be made to reduce the reliance on chemical control and only consider it as the last resort because it is expensive and injurious to humans and the environment."

### 1.5 Cultural control (no chemicals)
- Pruning, S03: "Pruning plays a major role in the management of CLR as it reduces the tree foliage increasing air circulation between branches thus modifying the within tree microclimate. This causes rapid evaporation resulting in reduced periods of leaf wetness, a key factor in spore germination."
- S03: "Coffee Research Institute has developed an elaborate coffee canopy management guideline that is accessible to all farmers [36]. This guideline emphasizes that pruning and shading is a critical integral cultural practice for the control of CLR."
- Shade is not simple. S03: "Studies in Kenya showed that coffee bushes under shade retained the infected leaves for significantly longer periods than coffee in the open sun while the disease severity was significantly higher in the trees in shade than in open sun". Do **not** write "more shade means less rust" on any card. Say "ask the officer about shade and pruning for your plot".
- Nutrition, S16: "Low-nutrient trees are more vulnerable to coffee rust, so spreading organic manure can be beneficial as it increases nutrients for plants."
- Weeding, S17: "open pruning and good weeding". S16: "removing weeds and pruning unnecessary vegetation improves air circulation and can also help stop the fungus."
- Tree age and leafiness, S03: "heavily foliated trees having more rust particularly at low inoculum levels."
- Resistant varieties. S14 (Coffee Development and Marketing Strategy 2024-2029, PDF page 27): "Traditional varieties (SL 34, SL28 and K7) which are susceptible to major coffee diseases such as Coffee Berry Disease, and Coffee Leaf Rust" and "Improved varieties Ruiru 11 and Batian are high yielding and tolerant to Coffee Berry Disease and Leaf Rust." Note that S14's own variety table (PDF page 28) says K7 is "Tolerant to Coffee Leaf Rust", which contradicts its text on page 27; S17 says "'Ruiru 11' and 'K 7' have been found resistant to leaf rust". **Do not state anything about K7.** Same page of S14: "the original coffee growing areas such as central Kenya region grow the traditional varieties but farmers are slowly adopting the new varieties". So much of Nyeri may still be SL28 and SL34, which are the susceptible ones. Our model does not label variety (see DATASETS.md).

### 1.6 Impact numbers (for context only, see EVIDENCE.md E2)
- "yield losses in excess of 75% where outbreaks are severe" (S03).

---

## 2. Brown eye spot (Cercospora coffeicola): still no Kenyan source

Pass 3 (3 Oct, later, Bright Data again): CABI/Plantwise factsheet 20207800275 still empty. KALRO KEEP (`keep.kalro.org`) returns "Loading app..." (JavaScript shell, no coffee disease text). AFA Coffee Directorate updates have no disease pages. No new Kenyan quote. Result:
- CABI Compendium and Plantwise pages return empty or "No access" through Bright Data (paywalled). Not used. Raw attempts are in `raw/gaps/`.
- Infonet Biovision has **no coffee brown eye spot page**. Its "Cercospora leaf spot" page (`raw/gaps/infonet_biovision_org_PlantHealth_MinorPests_cercospora_leaf_spot.md`) is about capsicum (*Cercospora capsici*). **Do not use it for coffee.** The Infonet coffee page does not mention Cercospora.
- KALRO: no page found. The only KALRO hit is a Facebook post that returned empty (S35).

What we can quote:
- S18 (Pacific Pests, Pathogens and Weeds, fact sheet 142; general, not Kenyan). Symptoms: "Small brown spots occur on the leaves, more obvious on the upper surface. The spots occur within the leaf, mostly between the veins, and also at the margins. The spots can grow up to 15 mm diameter; they have light brown or sometimes light grey centres, surrounded by a wide, dark brown ring, and a yellow margin."
- S18 conditions: "The disease is usually a problem when coffee plants are not growing well because of poor nutrition or too little shade."
- S18 importance: "Generally, it is less important on mature plants, although, when conditions favour the disease, epidemics occur on even well-maintained trees."
- S18 response: "Nutrition and shade should be improved before chemical control is considered." Cultural list: "Provide the plants with adequate nutrition, especially sufficient nitrogen and potassium." "Prune the bushes to improve air movement in the canopy." "Do not leave debris from pruning the bushes in the field - spores in the debris can reinfect leaves and berries."
- S44 (Plantwise Knowledge Bank factsheet 20207800275, **search-result snippet only, page not retrievable**, dated 1 May 2019): "Brown-eye spot is a fungal disease that spreads by wind and rain splash, favoured by humid-warm conditions: Too much shade, and poor air flow". The snippet is cut off. It agrees with S18 on wind, rain splash and air flow, and disagrees on shade (S18 says too little shade, S44 says too much).
- Conflict to flag: the sources disagree on shade, and S03 (Kenya, for rust) says shade can raise rust severity. **Do not put any shade statement on a card.**
- Do **not** reuse S18's copper schedule (Pacific, not Kenya).
- Weak Kenyan link: the JMuBEN authors labelled a cercospora class on Kenyan Arabica with a plant pathologist (S22), so the disease is present in the data. That is not agronomy guidance.
- Proposed card line (content-voice to confirm): "Brown spots with a pale centre and a yellow ring can be brown eye spot. It is often worse when trees are short of food or stressed. Ask the officer what to do."
- Status: **symptoms and general cause only. Treatment: ask the officer.**

## 3. Phoma: still no Kenyan extension source; secondary sources added

Pass 2 (3 Oct, late): tried the CABI datasheet for *Phoma costarricensis* (40417; abs, full and pdf forms), Infonet Biovision (no Phoma entry; the search returned its bacterial blight page), KALRO (none found). CABI returned empty. **No Kenyan government or extension page on Phoma was found.**
Pass 3: same result. KALRO KEEP and AFA Coffee Directorate have no Phoma page. CABI still empty.

Secondary, non-Kenyan sources now in `raw/gaps/` (both are trade or encyclopaedic pages, not peer-reviewed):
- S42 Revista Cultivar (Brazil), "Management of Phoma spot in coffee plants", 5 Apr 2019: "Its severity is greater in high-altitude regions where low temperatures, cold winds and humidity in crops predominate." And: "The fungus attacks coffee leaves, flowers, fruits and branches, producing very characteristic lesions." And: "flower buds and new shoots die, mummification of fruits and poor fruit granulation due to defoliation".
- S43 Roastopedia, "Phoma Leaf Spot (Phoma costarricensis)": "On mature leaves (typically the second pair and beyond), it produces circular, dark, necrotic spots that can expand to roughly two centimeters in diameter, often with a lighter center and darker margin." And: "On young shoots and branches, the fungus causes sunken, dark lesions that can girdle the stem entirely, producing the characteristic 'dry shoot' or tip blight symptom in which the growing tip wilts and dies back." And: "generally recognized as a disease of montane and highland coffee cultivation". It also says the related *Phoma tarda* was first documented in Ethiopia in 1954.
- Relevance to Nyeri: coffee there is highland, so Phoma is plausible. The JMuBEN authors also labelled a Phoma class on Kenyan Arabica (S22). Neither is agronomy guidance.
- Not used: the Revista Cultivar trial gives a copper product rate; **no doses**. The Roastopedia temperature and humidity figures were not cross-checked against a primary source, so they are not repeated here.
- Status: **symptoms (from secondary sources) and the cool, windy, highland pattern only. Treatment: ask the officer.** Do not describe a spray or timing for Phoma.
- Proposed card line: "Dark round spots on leaves, or a shoot tip that dries and dies back, can be Phoma. It is often worse in cool, windy, damp weather. I am not sure. Ask the officer."

## 4. Leaf miner: Kenyan species and Kenyan extension text now found

Source: S17, Infonet Biovision "Coffee (Revised)" (icipe, Kenya), page `raw/gaps/infonet_biovision_org_crops_fruits_vegetables_coffee_revised.md`, section "Leafmining caterpillars (*Leucoptera meyricki* and *Leucoptera caffeina*)". This resolves the earlier species caveat: in Kenya the leaf miners are *L. meyricki* and *L. caffeina*, not *L. coffeella* (the Neotropical species in S21).
- Symptoms: "These mines appear as irregular brown blotches on upper side of leaves, which when opened reveals many whitish caterpillars."
- Mechanics: "Upon hatching, the caterpillars bore into the leaf and mine just below the upper leaf surface. The mines of each L. meyricki caterpillar are initially separated but after few days they join to form one large mine."
- Effect: "The mining activity causes a reduction of the active leaf surface, reducing assimilation. Attacked leaves are usually shed prematurely."
- Natural enemies: "The caterpillars and pupae are attacked by a large number of parasitic wasps, which occur naturally in the field, and eggs are sucked dry by a predacious mites."
- The key safety line: "The indiscriminate applications of insecticide usually kill the natural enemies faster than it kills the moths, resulting in more serious attacks."
- Threshold: "Economic threshold level: If they tree is shaken vigorously and more than 35 moths are seen, the yield of coffee can be affected." (Source typo "they" kept.) This is a count of moths on a shaken tree, not a fraction of leaves in a photo, so Jani's 10-leaf check **cannot apply it**.
- Pruning hygiene: "When using coffee prunings, take care that no pests (leafminers, mealybugs, etc.) are on the prunings otherwise they could re-infest the trees."
- Other: "When intercropping Artemisia with coffee in East Africa, the incidence of coffee leafminers is drastically reduced (Per Diemer, FAO consultant)." One-person attribution; do not put on a card.
- S45, Springer, "Integrated pest management of coffee for small-scale farmers in East Africa: needs and limitations" (Nyambo, 1996; abstract read): "Chemical pesticides are far more popular at the farm level than any of the other recommended pest control measures." And: it reports "development of pest strains resistant to the cheap and commonly available chemical pesticides". Its reference list includes a Tanzanian study titled "Confirmation of resistance of the coffee leaf miner, Leucoptera meyricki Ghesq. (Lepidoptera: Lyonetiidae) to organophosphate insecticide spray in Tanzania" (title only; paper not read).
- S21 (Neotropical review, *L. coffeella*) still gives the Latin American symptom wording: "feeds in the mesophyll triggering necrosis and causing loss of photosynthetic capacity, defoliation and significant yield loss". Use only as background; Kenyan wording above is preferred.
- Search snippet only, not opened: a CATIE-hosted older paper says "The leaf-miners Leucoptera meyricki Ghesq, and L. caffeina Washbn are the most serious pests of Coffea arabica in Kenya and Tanzania." Corroborates the species names. Not used as a quote in cards.
- Not retrievable: CABI datasheets for *L. meyricki* (30488), *L. caffeina* (30484) and *L. coma* (30485). Pass 3 re-fetched `https://plantwiseplusknowledgebank.org/doi/10.1079/PWKB.Species.30488`. The page title is "Leucoptera meyricki (coffee leaf miner)" and the body is **"No access"** (CABI Compendium subscription). Saved as `raw/gaps/plantwiseplusknowledgebank_org_doi_10_1079_PWKB_Species_30488.md`. Not used.
- Status: **symptoms, species, and the safety line against indiscriminate spraying are now sourced to a Kenyan extension page. Treatment: ask the officer.**
- Proposed card line: "Brown, dry patches that look like blisters on the top of the leaf can be leaf miner. Do not spray on your own, because sprays can kill the helpful wasps and make it worse. Ask the officer." (Safety clause now supported by S17.)

## 5. Coffee berry disease (CBD): symptoms only, for the "out of scope" card

- S17 (Kenya-based): "The characteristic symptom is a progressive blackening of young, expanding coffee berries. This begins as small water-soaked lesions. They rapidly become dark and sunken. As they grow they cause the whole berry to rot. Under humid conditions, pink spore masses become visible on the surface of the lesion." And: "Berries often drop from the branch at an early stage of the disease."
- S17 on impact: "This disease does not kill trees, but crop losses can be more than 80%." Wet conditions favour it: "Wet conditions and temperatures between 15 and 27.7 C favour disease development."
- S19 (Ethiopia, 2025), abstract: "On average, national losses due to CBD range from 24 to 30% and in optimal conditions for the disease, damage can be total, reaching 100% in susceptible coffee trees."
- S17 response (general): "Plant resistant variety where coffee berry disease is endemic (e.g. 'Ruiru 11')." "Strip off diseased berries." "Timely spray copper fungicide."
- Tool limit: Jani does not look at berries. The card: "This tool only looks at leaves. Dark, sunken spots on green berries need the officer." (Content-voice to word it.)
- Also out of scope per S17: coffee wilt (*Fusarium xylarioides*): "wilting, chlorosis and defoliation of the aerial parts of the crop, and numerous vertical and spiral cracks in the bark of the trunk"; bacterial blight, "confined to a few coffee growing areas in Kenya (Solai in Nakuru District and around Mt. Elgon). Recently a few cases have been reported in the East of Rift Valley." Include only if the answer bank wants an "other problems" card.

## 6. Action thresholds: NOT FOUND for Kenya

- S03, the Kenyan review, gives a calendar (mid-October, late February to early March, three-week repeats) and says to monitor and adjust to the weather. It gives **no percentage of leaves affected** that triggers a spray.
- Tried: S03 full text, S17, S14, Google searches for "incidence threshold" with Kenya and CRI.
- Non-Kenyan snippets, not opened, not to be used as Jani thresholds: a Plantwise Rwanda page snippet "The threshold level of disease is 3-6% of infected coffee trees in a coffee plantation" (S37); an Agronomy 2022 snippet "Incidence increased above threshold levels (5%)" (S38).
- **Instruction to content-voice and ml:** every incidence band in `rules.json` (for example "few", "some", "many" of 10 leaves) is an **assumption, officer to confirm**. The timing logic (season windows) is supported; the incidence cut-offs are not.

## 7. Safety when spraying copper (general terms)

FAO and WHO, Guidelines for personal protection when handling and applying pesticides, 2020 (S20). Licence CC BY-NC-SA 3.0 IGO. Quotes:
- "These guidelines recommend that when pesticides are used, at the very least, long-sleeved shirts, long trousers, boots, socks and chemical-resistant gloves should be worn, even if the label does not require any PPE."
- "As a minimum precaution and to reflect real-life situations in LMIC, users should wear lightweight work clothing that covers most of the body, such as a long-sleeved shirt, long trousers, a hat, chemical-resistant gloves and boots that do not absorb spray."
- "They should never eat, drink or smoke while applying pesticides."
- "During rest breaks, they should pay particular attention to ensuring that their hands and face, especially around the mouth, are washed well before eating or drinking".
- "Work clothing and PPE must be washed separately from other family clothes and kept in a separate place."
- "Boots used during pesticide use should not be worn when returning home, as pesticide residues may contaminate the family".
- Who should not spray: users should "not work with pesticides when ill, malnourished, pregnant, or breastfeeding" and "read and understand the label".
- Vulnerable groups, defined in the guidelines: "persons that include pregnant and nursing women, the unborn, infants and children, the elderly".
(Text extraction added stray spaces inside some sentences; words are unchanged.)
Not found: copper-specific hazard advice from a Kenyan source (the Infonet Biovision "Copper fungicides in Kenya" page returned 404). Keep the card general: wear covering clothes, gloves and boots; wash after; keep children away; follow the label; ask the cooperative for the product.

## 8. Facts the answer bank may state (proposal, each with source)

| Proposed plain statement | Source | Strength |
|---|---|---|
| Rust shows as yellow to orange powder on the underside of leaves. | S03, S17, S16 | Strong |
| Rust is usually worst soon after the rains. | S03 | Strong |
| In Kenya, spraying for rust starts in mid-October, just before the short rains, with a second spray about three weeks later. | S03 | Strong |
| For the long rains, the first spray is late February or early March. | S03 | Strong |
| Pruning opens the tree and helps leaves dry, which slows rust. | S03 | Strong |
| The cooperative or officer tells you which registered product to use and how much. | S03 (PCPB register) | Strong |
| Wear long sleeves, trousers, boots and gloves when spraying. Do not eat or drink while spraying. Wash afterwards. | S20 | Strong |
| Dark sunken spots on green berries are not leaf rust. This tool does not check berries. Ask the officer. | S17, S19 | Strong |
| Brown eye spot is often worse on stressed or underfed trees. | S18 | Weak (non-Kenyan) |
| Leaf miner shows as irregular brown blotches on the top of the leaf. | S17 | Good (Kenyan extension) |
| Spraying insecticide on your own can kill the helpful wasps and make leaf miner worse. | S17 | Good (Kenyan extension) |
| Phoma is often worse in cool, windy, damp highland weather; it can dry out shoot tips. | S42, S43 | Weak (non-Kenyan, secondary) |

## 9. Do NOT put on any card

- Any percentage threshold as a fact.
- Any product name or dose (including those named in S03).
- Any statement that shade reduces rust.
- Any treatment, spray or timing for Phoma, brown eye spot or leaf miner. Symptoms and "ask the officer" only.
- The leaf miner moth threshold ("more than 35 moths" on a shaken tree): it cannot be checked from a leaf photo.
- Anything about which variety is resistant, other than "Ruiru 11 and Batian are described as tolerant to rust and berry disease" (S14), and only if the officer agrees.
