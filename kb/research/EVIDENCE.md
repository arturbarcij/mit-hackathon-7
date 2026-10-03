# EVIDENCE: problem data for Jani

Owner: research agent. Accessed date for every item: 3 Oct 2026. Source IDs (S01 and so on) point to `sources.json`.
Confidence: **primary** (government, World Bank, FAO, peer-reviewed, dataset owner), **secondary**, **modelled**.
Rule for readers: if a number is not in this file with a source, do not use it. Figures are quoted as published. Where I calculated something, it says "my calculation".

## Summary table (what to use)

| # | Item | Use this value | Country | Year | Source | Confidence |
|---|---|---|---|---|---|---|
| E1 | Extension agent to farmer ratio | **1:1,380** (target 1:600) | Kenya | 2025 | S02 (and S01 for the target) | primary |
| E2 | Rust loss and timing | **yield losses in excess of 75% where outbreaks are severe**; sprays start **mid-October**, repeat **three weeks** later | Kenya (review) | 2021 | S03 | primary (the 75% is cited by the review from an earlier work) |
| E3 | Coffee yield and production | 2024: **49,500 t**, **435.7 kg/ha**; lowest production in the last ten years was 2021 (**34,500 t**), lowest yield was 2020 (**308.3 kg/ha**) | Kenya | 2015 to 2024 | S04, S05 | primary |
| E4 | Women's phones | **91.8080408756395%** of women own a mobile phone (Findex 2024); **42%** of women own a smartphone vs **50%** of men (GSMA 2024 survey) | Kenya | 2024 | S07, S06 | primary |
| E5 | Mobile money | **83.5097020779134%** of women and **91.6719907971862%** of men have a mobile money account (2024) | Kenya | 2024 | S07 | primary |
| E6 | Coverage | "over 96 percent of its population" has 3G or better. County level: NOT FOUND | Kenya | 2023 | S08 | primary |
| E7 | Languages | Kikuyu ethnic group **8,148,668** (census). Kiswahili is the national language (Art. 7). Kikuyu speaker count: NOT FOUND | Kenya | 2019 / 2010 | S09, S10 | primary |
| E8 | Data bundle cost | **KSh 20** for 250MB for 24 hours; **KSh 99** for 1.5GB for 24 hours | Kenya | 2026 | S11 | primary (prices change) |
| E9 | Smallholders | AFA: "About 70 percent of coffee in Kenya is produced by smallholder farmers under cooperative societies"; about **800,000** smallholders (2022) | Kenya | 2022 to 2024 | S13, S14, S05 | primary |

---

## E1. Extension coverage in Kenya

| Field | Value |
|---|---|
| Value (current) | **1:1,380** extension agent to farmer |
| Unit | agents per farmers (ratio) |
| Country, year | Kenya, February 2025 |
| Source | Agriculture Extension Manual (Version 1), Food Systems Resilience Project (S02) |
| Publisher | Ministry of Agriculture and Livestock Development |
| URL | https://fsrp.go.ke/sites/default/files/2025-08/Agriculture%20Extension%20Manual%20v1%20final.pdf (PDF page 12) |
| Confidence | primary |

Exact quote (S02, PDF page 12): "Currently, the extension agent-to-farmer ratio is 1:1,380. This is against the proposed 1:600 extension service agent to farmer ratio as recommended in the Agriculture Sector Transformation and Growth Strategy (ASTGS) 2019-2029 and the global Food and Agriculture Organization (FAO) recommendation of 1:400."
(Text extraction put spaces around the hyphens, "agent -to-farmer". The figures are unchanged.)

**KASEP (S01), the document named in the brief.** KASEP does **not** state a current ratio. It states a target and says the ratio has not improved. PDF page 24 (printed page 8):
"Currently, some counties have employed extension personnel, however, the ratio of extension staff to famer has not improved. To address this gap, the Government of Kenya launched the Agriculture Sector Transformation and Growth Strategy whose objective is to ensure that the country attains a ratio of one (1) extension personnel to six hundred (600) famers by the year, 2029."
("famers" is the source's spelling.) KASEP also names the problem in its challenges list, PDF page 46: "Aging agricultural extension workforce and low staffing levels in both public and private extension service providers resulting in a low extension staff to farmer ratio".

**Farming households (denominator).** KASEP PDF page 18: "The total farming households as per the 2019 census is approximately 6.4 million (1.7 million crop farmers, 3.9 million mixed farming, 760,000 Livestock farmers, and about 30,000 fisher folks)".

**Disagreement.** MASTER_PROMPT cites a secondary figure: "fewer than 5,000 public extension officers for over 8 million farmers" (Kilimo Trust, 2025, S36). I did not open that X post and did not verify it. A Facebook post by a newspaper (found in search, not opened) says "at best 1: 1000 nationally. At county levels it is as high as 1:2000". Neither is used.
**We use:** 1:1,380 (S02, primary, 2025) with the 1:600 target (S01, S02). For farmer count we use 6.4 million farming households (S01), not "over 8 million".

**Constraint worth quoting for the product (KASEP PDF page 39):** "However, the cost of some technology is relatively high in regard to access to internet, availability of electricity and complexity of utilization of ICT tools. It is also hampered by lack of a compatible gadget and low literacy levels of farmers."

NOT FOUND: "extension officer visits the sub-county twice a year at best" is from the challenge brief, not a published statistic. No Kenyan source for visit frequency was found.

---

## E2. Coffee leaf rust: impact and timing in Kenya

| Field | Value |
|---|---|
| Source | "Coffee Leaf Rust (Hemileia vastatrix) in Kenya: A Review", Agronomy 2021, 11(12), 2590 (S03) |
| Publisher | MDPI. Authors include E. Gichuru (Coffee Research Institute, Kenya). Published 20 December 2021 |
| URL | https://www.mdpi.com/2073-4395/11/12/2590 , DOI https://doi.org/10.3390/agronomy11122590 |
| Country | Kenya |
| Confidence | primary (peer-reviewed). The 75% figure is a statement in the review's introduction citing an earlier work, not a Kenyan field measurement |

Quotes (S03):
1. Impact: "The disease can cause yield losses in excess of 75% where outbreaks are severe [13] due to loss of foliage by up to 100% and loss of berries by up to 70% [14]."
2. Timing, link to rain: "These weather patterns affect the epidemics of CLR with the peak of the disease coming soon after the rainy seasons when it fully sporulates from latent infections that occur during the rainy season, but they sporulate when temperatures rise after the rains".
3. Regions, East of Rift (this includes Nyeri, the Mount Kenya and Aberdare area): "In areas East of Rift, the long rains start in March through May and short rains start in October through December resulting in two CLR peaks in May to June and January to March".
4. Spray timing, short rains: "Following the rainfall patterns in the main coffee growing regions, fungicide sprays for CLR control in Kenya starts in mid-October, just before the start of short rains followed by a second spray, three weeks after the first spray".
5. Spray timing, long rains: "For the long rain period, the first spray is applied in late February or early March followed by one or two sprays at three weeks intervals for copper formulations and four-week intervals for other formulations."
6. Caveat in the same passage: "However, the spray program needs to be monitored and varied in response to weather patterns [67] because climate change is affecting the rainfall amounts and distribution."
7. Regions defined: "Coffee in Kenya is mainly grown in two regions, the East of Rift Valley (areas around Mount Kenya, the Aberdare ranges, and Machakos) and West of Rift Valley".

Check against MASTER_PROMPT section 3.3: the claims "peaks soon after the rainy seasons", "mid October", "repeat about three weeks later" and "losses above 75% in severe outbreaks" all match the review. One nuance for the lead: the review's mid-October start is described for "the main coffee growing regions" in general. For East of Rift the rust peaks it lists are May to June and January to March, which come after the long rains and after the short rains. Our video line "protect new leaves before the short rains" is consistent with item 4.

---

## E3. Kenya coffee yield and production, last ten years

Source: FAOSTAT, domain Crops and livestock products (QCL), item "Coffee, green", area Kenya (S04). Bulk file downloaded 3 Oct 2026. Every value has FAOSTAT flag **A** ("Official figure", from the file's own flags table). Country: Kenya. Units as in the file.

| Year | Production (t) | Area harvested (ha) | Yield (kg/ha) |
|---|---|---|---|
| 2015 | 42000 | 113500 | 370.0 |
| 2016 | 46100 | 114000 | 404.4 |
| 2017 | 38620 | 114700 | 336.7 |
| 2018 | 41375 | 115570 | 358.0 |
| 2019 | 44500 | 119600 | 372.1 |
| 2020 | 36900 | 119700 | 308.3 |
| 2021 | 34500 | 108200 | 318.9 |
| 2022 | 51900 | 109400 | 474.4 |
| 2023 | 48700 | 111900 | 435.2 |
| 2024 | 49500 | 113600 | 435.7 |

(Earlier values for reference: 2012 yield 446.3, 2013 362.5, 2014 450.0 kg/ha.)

Cross-check, Kenya National Bureau of Statistics (S05, Table 5.1, coffee year Oct to Sep, source Agriculture and Food Authority): area (ha) 119,675 / 108,199 / 109,384 / 111,902 / 113,501* and production (tons) 36,873 / 34,512 / 51,853 / 48,649 / 49,501* for 2019/20 to 2023/24 (*provisional). These agree with FAOSTAT to within rounding.
Smallholder versus estate yield, 2023/24* (S05, Table 5.1.2, kg/ha): Co-operatives 414.7, Estates 578.1. Note from the same table: "Yield Is Obtained By Dividing Current Production By Acreage Two Years Ago".

How to say it honestly: the series is **not a steady decline**. Yield was lowest in 2020 (308.3 kg/ha) and 2021 (318.9), then 474.4 in 2022. The Annex B line "yields dropped this season" is a farm-level story, not what the national series shows for 2022 to 2024. Do not claim a national decline.
Confidence: primary. Country-level data; says nothing about one farm.

---

## E4. Women's mobile phone and smartphone ownership in Kenya

**(a) Any mobile phone, women.** World Bank Global Findex Database (Findex 2025 round, survey year 2024), indicator `con1.1` "Own a mobile phone, women (% age 15+)", Kenya, 2024: **91.8080408756395**. Men (`con1.2`): **93.6989094857674**. Rural (`con1.9`): **91.493057124906**. Source S07. Primary.

**(b) Smartphone.** GSMA, The Mobile Gender Gap Report 2025 (S06), data from the "GSMA Consumer Survey, 2024", base "Total population aged 18+", Kenya.
- Smartphone ownership (Figure 2, PDF page 17): men **50%**, women **42%**, gender gap **16%**.
  Method note: the chart text extracts as one run of numbers, so I read the order from the arithmetic: (50 minus 42) divided by 50 is 16%, and the same check works for the other countries on the chart. Confidence primary, extraction check passed. **Eyeball Figure 2 on the PDF before it goes on screen.**
- Journey stages (Figure 5, PDF page 21, printed page 25), Kenya, women: mobile ownership **93%**, internet-enabled phone ownership **54%**, mobile internet adoption **43%**. Men: **95%**, **60%**, **55%**.
- Definition from the report (same figure note): "A mobile owner is defined as a person who has sole or main use of a SIM card (or a mobile phone that does not require a SIM) and uses it at least once a month."
- Sample note from the report: n=493 to 982 for women and n=483 to 1,234 for men (across countries; Kenya's own n not shown in the extract).

Superseded: GSMA blog 2019, "37% of men own a smartphone, compared to only 27% of women" in Kenya (S34, snippet only). Do not use.

Why it matters for Jani: most women in Kenya own a basic or smart phone, but fewer than half own a smartphone (42%). That supports the two-phone design in the brief. The 42% is a national adult figure, not Nyeri farmers.

---

## E5. Mobile money use in Kenya by gender

Source: World Bank Global Findex Database, Kenya (S07). Indicator names as published: "Mobile money account (% age 15+)" and its women and men splits.

| Year | All adults | Women | Men | Rural |
|---|---|---|---|---|
| 2024 | 87.4994112747318 | 83.5097020779134 | 91.6719907971862 | 85.7077645122401 |
| 2021 | 68.6586915682757 | 66.0427561215072 | 71.4192115036634 | not reported |
| 2017 | 72.9316807234182 | 69.3801385620088 | 76.8989865647738 | not reported |

Account of any kind (`account.t.d`, % age 15+), 2024: all 90.1199173733613, women 86.5155344015748, men 93.8895090496553.
Values are as returned by the API; the publisher rounds to whole numbers on its pages. Country Kenya, years as shown. Primary. Findex surveys adults aged 15 and over, nationally.
Note the gap: women 83.5 vs men 91.7 in 2024, a difference of 8.1623 percentage points (my calculation).

---

## E6. Mobile coverage in coffee counties (Nyeri, Kiambu, Murang'a, Kirinyaga, Embu)

National statement (S08, World Bank Kenya CCDR, Digital sector background note, November 2023, PDF page 5): "Kenya boasts mobile broadband networks of 3G and higher for over 96 percent of its population. Unique mobile internet penetration rate stood at 34.2 percent of the total population at the start of 2023, compared to the East African average of 23 percent, with a fixed broadband penetration of only 1.5 percent."
Country Kenya, 2023, primary.

**NOT FOUND: county-level coverage for the five coffee counties.** Tried: Communications Authority Q3 FY2025/26 sector statistics report (S15, opened; reports subscriptions and penetration, no coverage by county, no coverage percentage); Google searches for CA and GSMA coverage by county; OpenCelliD (needs a registered API token or a database download, not attempted because it needs an account and the output is tower locations, not population coverage). Suggested wording for docs: "National 3G+ coverage is above 96 percent (World Bank, 2023). We have no county-level coverage figure for the coffee counties; coverage on a slope can be much worse than the population figure."
Caveat: population coverage is not the same as signal on the farm.

---

## E7. Kikuyu and Swahili

- **Kikuyu ethnic group, Kenya 2019 census:** **8,148,668** of a total population of **47,564,296** (S09, Volume IV, Table 2.31 "Distribution of Population by Ethnicity/Nationality", PDF page 436). As a share: 17.13% (my calculation: 8,148,668 divided by 47,564,296). KNBS Table 2.31 lists "16 KIKUYU 8,148,668".
- **This counts people of the ethnic group, not speakers of the language.** NOT FOUND: a primary count of Gikuyu speakers. Ethnologue is paywalled and the census volume I read tabulates ethnicity, not language spoken. Say "the Kikuyu community numbers 8,148,668 (2019 census)", not "8 million speakers".
- **Swahili:** Constitution of Kenya 2010, Article 7 (S10): "(1) The national language of the Republic is Kiswahili. (2) The official languages of the Republic are Kiswahili and English."

---

## E8. Cost of a small data bundle in Kenya (to price the app download)

Source: Safaricom PLC, Terms and Conditions for Safaricom PrePay and PostPay Data Bundles (S11), table "Daily Data Bundles" (columns: bundle, data, SMS, price in Kshs, validity). Search listing dated 31 August 2026; page accessed 3 Oct 2026.

| Bundle | Data | Price (KSh) | Validity |
|---|---|---|---|
| Daily 10MB | 10MB | 5 | 24 Hours |
| Daily 60MB | 60MB | 10 | 24 Hours |
| Daily 250MB | 250MB | **20** | 24 Hours |
| Daily 750MB | 750MB | 50 | 24 Hours |
| Daily 1.5GB | 1.5GB | **99** | 24 Hours |

Monthly example from Safaricom's tariff page (S12): "1GB, Ksh. 250.00, Valid for 30 days". The same page also lists a second block of 30-day plans all at Ksh. 200.00; I could not tell what that block is, so I did not use it.
Safaricom changed its bundles in August 2026 (news reports, not opened). **Re-check the price on the day of the video.**

Calculations for docs (my calculation, labelled as such):
- The 15 MB offline bundle target is 6.0% of a 250MB daily bundle (15 divided by 250), which costs KSh 20. So the whole app fits in the cheapest bundle that is large enough, with room to spare.
- Download time at 1 Mbit/s: 15 MB x 8 = 120 Mbit = 120 seconds. The 5 MB model alone: 40 seconds. Ignores protocol overhead.
Primary (company tariff). Prices and bundle names change; date-stamp every use.

---

## E9. Coffee smallholders and cooperatives in Kenya

1. AFA (S13), exact quote: "About 70 percent of coffee in Kenya is produced by smallholder farmers under cooperative societies while the remaining 30 percent is produced by small, medium and large-scale estates. Coffee farming supports about 1.5 million Kenyan households either directly or indirectly through forward and backward linkages. The leading coffee-producing counties are Kiambu, Kirinyaga, Nyeri, Murang'a, Kericho and Bungoma."
2. Coffee Development and Marketing Strategy 2024-2029, Ministry of Agriculture and Livestock Development, January 2024 (S14), PDF page 16: "Kenya coffee is produced under two farming systems namely smallholder farmers estimated at 800,000 in 2022 an increase from 11,000 in 1963 and registered estates 3,000 with 2694 estates being active (AFA, 2021/2022). The smallholders are clustered into co-operative societies for primary processing and marketing coffee." And: "The total area under coffee is estimated at 109,384.45 Ha in 2021/2022 with two-thirds of the acreage under smallholders' farmers (AFA,2021/2022)." PDF page 30: "In 2021/22, there were 1,190 primary coffee pulping stations (wet mills) operated by 590 cooperatives societies".
3. KNBS National Agriculture Production Report 2025 (S05), Table 5.1.2, 2023/24 provisional: area, Co-Operatives 85.0 thousand ha of Total 113.6 thousand ha; production, Co-Operatives 37.2 thousand tonnes of Total 49.5 thousand tonnes. My calculation: cooperatives hold 74.8% of area and 75.2% of production.
4. **Nyeri (our reference county), S05 Table 5.1.1, 2023/24 provisional, hectares:** Co-op Society 8,856.0, Estate 1,160.0, Total 10,016.0. Co-op share 88.4% of area (my calculation). For comparison, totals for other coffee counties: Kiambu 19,746.0, Kirinyaga 10,412.0, Murang'a 9,321.0, Embu 7,078.0.

**Disagreement between sources.** AFA says about 70 percent of coffee is cooperative-produced; the strategy says two-thirds of acreage (2021/22); KNBS gives about 75 percent of area and of production (2023/24, provisional). They differ by definition and year. **We use:** the AFA sentence for a headline ("about 70 percent", quoted), and the KNBS table for any precise or Nyeri figure. Do not average them.
Cooperative member counts (members per society) were not found in a primary source. NOT FOUND, tried: AFA page, strategy document, KNBS report. A COSA 2019 figure of "570,000 small-scale farmers organized in 421 farmer cooperative societies" appeared in search (secondary, old, not opened); not used.
