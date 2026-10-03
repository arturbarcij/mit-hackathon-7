# Agronomy guidance for the answer bank

Owner: research agent (Task 2). Accessed: 2026-10-03. Source ids (S1, S2, ...) refer to `kb/research/_sources_guidance.json`.

Rules used here:
- No product brand names and no doses. Where a product or dose would go, the line is "Ask the cooperative or officer for product and dose."
- Every statement has a source id and a short exact quote. Quotes keep the source's spelling.
- "What sources say" is evidence. "Suggested line for Noor" is a plain-language draft for content-voice; it is not a quote. Lines are short so they can be read aloud.
- Anchors (e.g. `GUIDANCE#rust-timing`) match the section ids below, for use in `answers.json` `sources`.

## Summary for content-voice and engine

| Topic | Status | Main source |
| --- | --- | --- |
| Rust symptoms | Sourced | S1, S2, S3 |
| Rust timing and copper schedule | Sourced (Kenyan, KALRO CRI) | S1, S3 |
| Rust cultural control | Sourced (pruning strong; shade mixed; nutrition weak) | S1, S3 |
| Incidence threshold | One Kenyan figure: about 20% of leaves with rust, for a curative (systemic) spray, not for starting copper | S2, S3 |
| Cercospora (brown eye spot) | Sourced; Kenya lists it as minor | S3, S4, S5, S6 |
| Phoma | Symptoms sourced (Kenyan dataset paper); no Kenyan management guidance found | S4, S7 |
| Leaf miner | Sourced | S3, S4 |
| Coffee berry disease | Symptoms sourced; out of scope | S2, S3 |
| PPE and handling | Sourced (general pesticide, FAO/WHO); nothing copper-specific found | S8, S3 |

---

## rust-symptoms: Coffee leaf rust, symptoms

### What sources say
- [S1] "Yellow to orange powdery blotches appear on the underside of leaves, with corresponding chlorotic patches on the upper side."
- [S1] "Young lesions may appear as small chlorotic spots before sporulation occurs"
- [S1] "Initially, these are only 2–3 mm diameter, but steadily expand, coalesce, the centers of older lesions become necrotic"
- [S3] "Pale yellow spots appear on the underside of the leaves at the onset of infection"
- [S3] "The spots later change to yellow/orange powdery masses"
- [S3] "Affected leaves fall off prematurely in case of severe infection. This condition may cause dieback if not controlled"
- [S2] "Orange patches appear on the lower surface of the leaves"
- [S1] "The major effect of CLR is defoliation"
- [S1] "The disease can cause yield losses in excess of 75% where outbreaks are severe"
- [S1] "Defoliation, by reducing the growth potential of the plant, restricts the growth of new stems on which the following season's crop would be produced"

### Suggested line for Noor
- Rust is yellow or orange powder under the leaf. The top of the leaf has pale yellow patches.
- Bad rust makes leaves fall early. This can cut next season's harvest.

---

## rust-timing: When rust peaks

### What sources say
- [S1] "the peak of the disease coming soon after the rainy seasons when it fully sporulates from latent infections that occur during the rainy season but sporulate when temperatures rise after the rains"
- [S1] East of Rift (Nyeri, Kirinyaga, Murang'a, Kiambu, Embu are East of Rift): "In areas East of Rift, the long rains start in March through May and short rains start in October through December resulting in two CLR peaks in May to June and January to March"
- [S1] "Rainfall distribution is more influential in the progression of the disease whereby light and broken rain is more favorable than continuous rain"
- [S1] "Uredinial germination and infection require about 24 to 48 h of continuous free moisture."
- [S3] "Warm and wet conditions"; "Wind and or rain – disperses the spores"
- [S3] "at least 3 hours of wetness on the leaves are required for them to germinate"
- Note: S1 (24 to 48 h free moisture for infection) and S3 (at least 3 h wetness for germination) describe different steps; they are not in conflict for our purposes. Neither number is needed in farmer text.

### Suggested line for Noor
- Rust spreads in the rains. It shows most just after the rains.
- Protect the leaves before the rains start.

---

## rust-copper-timing: Copper spray timing relative to rains, and repeat interval

### What sources say
- [S1] "fungicide sprays for CLR control in Kenya starts in mid-October, just before the start of short rains followed by a second spray, three weeks after the first spray"
- [S1] "These two sprays reduce the production of new spores leading to low inoculum potential at the beginning of the long rains"
- [S1] "For the long rain period, the first spray is applied in late February or early March followed by one or two sprays at three weeks intervals for copper formulations and four-week intervals for other formulations."
- [S3] "the sprays should be applied before the commencement and during the early period of the rainy season"
- [S3] "Start the 1st round of sprays just before the short rains and repeat 3 weeks later"
- [S3] "Start the 2nd round of sprays before the onset of long rains and do 2 more at 3 weeks interval"
- [S2] "Spray every 21 days if using copper formulations and every 28 days if tank mixtures."
- [S2] "If it becomes too wet bring the is spray forward to every 14 days." (typo "the is" in original)
- [S1] "the spray program needs to be monitored and varied in response to weather patterns"
- [S1] Products and rates are set nationally: "PCPB uses the CRI report to register the fungicide and provides farmers with a list of registered products, indicating the recommended rates as well as the proper timing of application."
- [S3] "use of PCPB registered Copper-based fungicides"
- [S1] "Timely application of chemical control is critical in its success"

Small disagreement on long-rains repeats: S1 says "one or two sprays" after the first; S3 says "2 more". Use "one or two more, as the officer advises".

S2 states the 21-day copper interval in the context of its combined CBD and CLR spray section; S1 and S3 state three weeks specifically for rust. All agree on three weeks for copper.

**Recommended statement for the app**
- Short rains window (East of Rift): first copper spray in mid October, just before the short rains; repeat about three weeks later. [S1, S3]
- Long rains window: first copper spray in late February or early March, before the long rains; then one or two more at three-week intervals. [S1, S3]
- Product and rate: from the cooperative or officer (PCPB registered list). [S1]

### Suggested line for Noor
- Before the short rains: Spray copper in mid October, before the rains. Spray again three weeks later.
- Before the long rains: Spray copper in late February or early March. Repeat after three weeks, one or two more times.
- In the rains (assumption, officer to confirm): The rains have started. Ask the officer if it is still worth spraying.
- Dry season, outside both windows (assumption, officer to confirm): Prune now. Plan to spray before the next rains.
- Always: Ask the cooperative or officer for product and dose. Wear protection.

---

## rust-threshold: Published incidence threshold for action

### What sources say
- [S2] KALRO leaflet: "Where leaf rust infection approaches approx. 20% level (percentage of leaves with rust), its use a curative fungicide" (wording as in original)
- [S3] Kenya Coffee Sustainability Manual (compiled by CRI): "In case the infection is severe (20% of leaves have rust), it is necessary to use a systemic PCPB registered coffee fungicide."
- [S3] "Do not spray more than 2 times a year" (systemic); [S2] "Do not apply more than 2 sprays of any systemic fungicide in one coffee season."
- [S9] Brazil, not Kenya: fungicides "must be applied when the visual sign or manifestation of the pathogen sporulation in the leaves is still below a 5% incidence."

### What this means (research note, not a quote)
- A Kenyan threshold exists: about 20% of leaves with rust. It triggers a **curative (systemic) spray**, which needs the officer. It is not a threshold for starting copper.
- Copper in Kenya is **calendar based and preventive** (before the rains), not triggered by incidence. No published incidence threshold for starting copper was found.
- The sources do not say how many leaves to sample or where on the tree. Mapping "20% of leaves" to Noor's 10-leaf sample (2 of 10) is an **assumption, officer to confirm**. Ten leaves chosen from worried rows is a small, biased sample; it will tend to overstate incidence.
- No published threshold found for cercospora, phoma or leaf miner. S3 mentions the idea of an "economic threshold levels (ETL)" for insect pests but gives no number for leaf miner.

### Suggested line for Noor
- Rust is on many leaves. Ask the officer. A stronger spray may be needed, and only the officer can advise it.
- (Thresholds in `rules.json`: cite `GUIDANCE#rust-threshold` for the 20% figure and mark the 10-leaf mapping `"assumption": true, "note": "officer to confirm"`.)

---

## rust-cultural: Cultural control (pruning, shade, nutrition, varieties)

### What sources say
- [S1] "Pruning plays a major role in the management of CLR as it reduces the tree foliage increasing air circulation between branches"
- [S1] "This causes rapid evaporation resulting in reduced periods of leaf wetness, a key factor in spore germination."
- [S1] Pruning helps the spray: "increasing the efficiency of chemical sprays by enhancing spray penetration"
- [S1] "heavily foliated trees having more rust particularly at low inoculum levels"
- [S3] "Cultural control - proper and timely pruning and regular change of cycle"
- [S2] "Timely pruning, handling and desuckering."
- [S3] When to prune: "normally carried out after the main harvesting"
- Shade, mixed evidence:
  - [S1] "the disease severity was significantly higher in the trees in shade than in open sun"
  - [S1] "Canopies of shade trees can also lower CLR levels by intercepting and reducing the energy of raindrops"
  - [S1] "Proper shading is critical"
- Varieties:
  - [S1] "The growing of resistant coffee varieties has always been considered the most sustainable and affordable management of CLR"
  - [S3] "Ruiru 11 and Batian are resistant to CBD and CLR"
  - [S3] "conversion of susceptible varieties to resistant ones through top-working (grafting)"
- Nutrition: weak evidence only. [S1] "management of the tree architecture increases nutrient and water use efficiency resulting in healthier plants". NOT FOUND: no Kenyan source found that links a specific nutrition practice to less rust. Tried S1, S3 (nutrition chapter), web search. Do not make a nutrition claim for rust.

### Suggested line for Noor
- Prune so air and light pass through the bush. Leaves dry faster and rust spreads less.
- Pruned bushes also take the spray better.
- Ask the officer about shade, and about rust-resistant varieties such as Ruiru 11 or Batian.

---

## cercospora: Cercospora (brown eye spot)

### What sources say
- [S4] Kenyan pathologist description: "the appearance of circular grey,spots with tan, or white centers is a strong indication of the presence of Cescospora" (spelling as in original)
- [S5] "Small brown spots occur on the leaves, more obvious on the upper surface"
- [S5] "they have light brown or sometimes light grey centres, surrounded by a wide, dark brown ring, and a yellow margin"
- [S6] "Lesions are sometimes surrounded or ringed by a bright yellowish "halo,""; "Affected leaves may defoliate prematurely."
- [S5] "The disease is usually a problem when coffee plants are not growing well because of poor nutrition or too little shade."
- [S5] "In nurseries, it can cause leaf fall of seedlings ... Generally, it is less important on mature plants"
- [S3] Kenya classes it as minor: "Other minor coffee diseases include Botrytis Warty disease, Root rot, Brown eye spot, Leaf blight and stem die back. However, these are not of major economic importance."
- [S3] Nursery advice only: "Control diseases such as damping-off and Brown eye spot by using 0.5% copper solution." (a nursery rate; do not use in farmer text)

General response: no Kenyan field management guidance for mature trees found beyond "minor". S5 links it to weak, poorly fed or under-shaded plants.

### Suggested line for Noor
- These look like brown eye spots: round brown spots with a pale centre and a yellow ring.
- This is usually minor. Keep the bushes well fed and ask the officer at the next visit.

---

## phoma: Phoma

### What sources say
- [S4] Kenyan pathologist description: "a leaf that dies from the tip area towards the other sides [4] is a strong indication that the leaf is suffering from phoma"
- [S4] "identify the leaves whose trees were beginning to die from the tip of the leaves"
- [S7] Brazil, peer-reviewed: "losses of between 15 and 43% from damage such as stem drying, flower necrosis, pinhead mummification and leaf spot"
- [S7] "Fungus penetration is facilitated by mechanical damage to the plant tissues that is produced by insects or by friction between leaves due to intense winds in cold months."
- [S7] "Higher altitudes provided higher disease incidence and severity values."

NOT FOUND: Kenyan management guidance for phoma. Tried S3 (lists only "Leaf blight and stem die back" as minor; it does not name phoma, so we cannot be sure that entry is phoma), S2, web search for KALRO/CRI phoma. Doubt: the tip-dieback description in S4 overlaps with other causes of leaf-tip browning (for example scorch or drought); the photo model may confuse them.

### Suggested line for Noor
- Leaves are dying from the tip. This may be phoma, which is worse in cold, windy places.
- The tool is not sure of the cause. Ask the officer.

---

## miner: Leaf miner

### What sources say
- [S3] "Irregular brown blotches on the upper side of the leaves, covering white caterpillars of size 12 mm (½ in) long within the "mine"."
- [S3] "The pest is most common in the East of the Rift Valley."
- [S4] Kenyan pathologist description: "yellow trails are left underneath the coffee leaf epidermis"
- [S3] Chemical control is with "recommended systemic insecticides that are ground/soil applied" or "biological PCPB registered insecticides (Insect Growth Regulators - IGR's)". (No products or doses here; officer only.)
- [S3] IPM: "It is important to avoid unnecessary insecticide sprays in order to conserve the beneficial insects or natural enemies"
- [S3] "Control the common insect pests like green scales, giant looper and leaf miners as they occur." (nursery section)

### Suggested line for Noor
- These look like leaf miner marks: brown patches on top of the leaf, with small caterpillars inside.
- Do not spray without advice. Ask the officer which treatment, if any.

---

## cbd: Coffee berry disease (out of scope)

### What sources say
- [S3] "On green berries: small dark sunken patches/lesions which spread rapidly and may cover the whole berry. Infected berries may be shed or remain on the trees in a black shrivelled condition"
- [S3] "On ripe berries: dark sunken lesions with black dots spreading rapidly on the ripe berries (late Blight)"
- [S3] "On flowers: dark brown blotches/streaks on the petals."
- [S3] "On leaves: brown marginal spots. However, leaf infection is not common"
- [S2] "Berries most susceptible at 4-20 weeks after flowering."
- [S3] "Coffee Berry Disease may lead to total crop loss"

### Suggested line for Noor
- Dark, sunken spots on the berries may be coffee berry disease. This tool checks leaves only.
- Take a few berries to the officer quickly.

---

## ppe: PPE and handling for copper sprays (general)

### What sources say
- [S8] "at the very least, long-sleeved shirts, long trousers, boots, socks and chemical-resistant gloves should be worn, even if the label does not require any PPE"
- [S8] "read the label carefully to determine correct use, risks and required PPE"
- [S8] "They should never eat, drink or smoke while applying pesticides."
- [S8] "It is also important to wash gloved hands before removing the gloves."
- [S8] "Work clothing and PPE must be washed separately from other family clothes and kept in a separate place."
- [S8] "Boots used during pesticide use should not be worn when returning home"
- [S8] "do not spray in inappropriate weather conditions, that is, when it is too windy (> 3m/s), to prevent spray drift, when it is raining or > 30 °C"
- [S8] "not work with pesticides when ill, malnourished, pregnant, or breastfeeding"
- [S8] "Pesticides should always be stored securely, away from livestock, separated from food and drinks and locked away to prevent access by children"
- [S8] "Pesticides should never be decanted into food containers, drinking bottles or unmarked containers"
- [S8] Empty containers: "cleaned by triple rinsing (not in waterways)"; "should not be discarded and burnt in the field or re-used as containers for storage of food or water"
- [S3] Kenya: "Appropriate personal protective clothing should be used." and sprayers "well calibrated and with appropriate nozzles"

NOT FOUND: copper-specific PPE advice from a Kenyan source. The FAO/WHO guidance is for all pesticides and applies to copper. Tried S3, S2, web search.

### Suggested line for Noor
- Wear long sleeves, long trousers, boots and gloves when you spray.
- Do not eat, drink or smoke while spraying. Wash well after.
- Do not spray in wind, in rain, or in the hottest part of the day.
- Do not spray if you are pregnant or breastfeeding. Ask someone else.
- Keep sprays locked away from children and food. Never reuse the empty container.

---

## Season note (for the engine's `season_window`)

From S1 for East of Rift: short rains "October through December", long rains "March through May". S3 and S1 put copper sprays just before each. The exact dates for Nyeri belong in `season.json` (research Task 4), not here.

## Doubts and open points
1. The 20% figure (S2, S3) is for curative/systemic sprays, not copper. Its mapping to a 10-leaf sample is an assumption.
2. Phoma: no Kenyan management guidance found; tip dieback has other causes.
3. Kenyan sources call brown eye spot "minor"; the app should not alarm farmers about it.
4. Nutrition and rust: no supporting Kenyan source found.
5. S2 was read via a search-engine extract because the KALRO repository timed out; the quotes match across two separate extracts, but the full table of products and spray programme was not read (we do not need it: no brands, no doses).
6. S1 (MDPI) blocked direct download; text read via a full-page capture from the search tool. Quotes were checked against that capture.
