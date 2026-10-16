# test100v2-p1: expert grades (Apertus-v1.5-70B, after fixes)

Run: `bench/results/Apertus-v1.5-70B-test100v2-p1.json`, 20 questions. There were 0 pipeline errors and 0 timeouts, so no retry was needed. The bench script crashed only at the final `print(summary)` (cp1252 console cannot encode `✗`). That happened after the JSON/MD had been written.
Scale: 3 = correct, concrete, right sources/authority · 2 = mostly right, minor gaps · 1 = partly right but important error / wrong governing source / very vague · 0 = wrong, off-topic or empty. Each answer was graded on its own before the old grades were opened.

**Average score: 1.35 / 3** (sum 27/60), up from 1.20 (24/60).
**Distribution:**

| score | count | was |
|---|---|---|
| 3 | 3 | 2 |
| 2 | 6 | 3 |
| 1 | 6 | 12 |
| 0 | 5 | 3 |

**Other measures:**

| measure | new | old |
|---|---|---|
| Answers with concrete factual errors | 12/20 | 13/20 |
| Answers with clearly off-topic acts in the source list | 12/20 | 11/20 |
| Language correct | 20/20 | 20/20 |
| Avg latency | **129.7 s** (min 49.2, max 193.1) | 87.6 s |
| Avg words (target < 230) | 474 | 407 |
| Verifier revisions | 55 | 34 |

| id | question | old | new | sources ok | main issue | total_s |
|---|---|---|---|---|---|---|
| T001 | Comment avoir le permis C ? (Ecublens) | 1 | 2 | mostly (LEI 34, 58a, OA-DFJP 3 ok; Ecublens police reg., CO 266c, LEI 6 visa off-topic) | Now gives both the 10-year route and the 5-year route (art. 34 al. 2/4 LEI) correctly. Errors: the anticipated route is tied to "art. 62 al. 1 let. b et c", but art. 34 al. 4 refers to the art. 58a criteria. The appeal goes to the "Greffe municipal d'Ecublens / Comité de Direction" (taken from a police regulation), but it belongs before the CDAP of the Tribunal cantonal. Language levels (A2/A1, art. 60 OASA) and settlement-agreement nationals are still missing. | 191.2 |
| T002 | permis b renouvellement (Lausanne) | 1 | 1 | partly (LEI 33, VD 142.11 ok; Lausanne 700.2 is a fee regulation for another kind of "permis", most likely building permits; LEI 37 irrelevant) | Art. 33 al. 3 (renewable absent art. 62 grounds) and SPOP are correct. It invents a "taxe communale" for permit renewal from Lausanne reg. 700.2, citing its entry-into-force articles 12/13. It still says to file with SPOP, but in VD renewals go through the commune's bureau des étrangers. No mention of B UE/AELE (ALCP), deadlines or documents. | 152.4 |
| T003 | C früher? (Zürich) | 2 | 2 | yes (AIG 34, 58a; ZH 631.41 unused) | Art. 34 Abs. 4 AIG and the Migrationsamt are correct. It inverts Art. 34 Abs. 5: training stays **are** counted if a 2-year B follows, but the answer says they are not counted. It gives no B1/A1 language level (Art. 62 VZAE) and omits the 5-year treaty route (DE/FR/IT/AT/NL…). | 125.5 |
| T004 | Requisiti permesso B lavoratori UE (Lugano) | 1 | 0 | **no** (LStrI 11/21/23/33 instead of ALC/OLCP; CO 266c off-topic) | Wrong regime again, now presented more forcefully. It lists the priority test (art. 21) and the qualified-worker requirement (art. 23) as conditions for EU workers. Under the ALC (annex I art. 6), neither applies: an employment contract ≥ 1 year gives a 5-year B UE/AELS. Only the TI procedural details (e-platform, convocation) are usable. | 193.1 |
| T005 | Conjoint étranger peut me rejoindre ? (Genève) | 1 | 1 | partly (LEI 44, 47, 85c; Swiss/C/EU sponsor articles missing) | Art. 47 deadlines are now included, but stated wrongly: the 12-month limit applies to **children over 12**, not to a spouse "de plus de 12 ans". It still assumes a B sponsor and never distinguishes Swiss (art. 42, a right), C (art. 43), EU (ALCP) or B (art. 44, discretionary) sponsors. Art. 85c (admission provisoire) is padding. OCPM is correct. | 174.6 |
| T006 | Permis C widerrufen bei Sozialhilfe? (Bern) | 1 | 2 | yes (AIG 63/62; Bauordnung Stadt Bern off-topic) | Art. 63 Abs. 1 lit. c AIG is correct and there is no self-contradiction this time. Omits Rückstufung to B (Art. 63 Abs. 2), proportionality (Art. 96) and the end of the 15-year protection. The BE Nothilfe articles are irrelevant padding. First instance is the SID, not the Verwaltungsgericht directly. | 122.9 |
| T007 | Durée de résidence pour naturaliser (Fribourg) | 1 | 3 | yes (LN 9, LDCF FR art. 9, commune reg.) | Correct and concrete at all three levels: the 10 years / 3 of the last 5, double counting from 8 to 18, at least 6 years of actual stay and the C permit; 3 years in the canton (2 of them in the last 5); 2 years in the commune. Only cosmetic padding (LN 18 is unused). | 94.8 |
| T008 | Einbürgerung in Chur | 2 | 2 | partly (BüG 9-18 ok; KBüG GR 370.100 retrieved but declared "keine einschlägige Quelle"; PG Chur, OR 266c off-topic) | The federal procedure (BüG 13-15, SEM approval, 1-year decision) is correct and the answer is no longer truncated. But the cantonal and communal part is now empty even though six KBüG GR articles were retrieved. It loses the Bürgergemeinde interview and the residence rules that the old answer had. | 182.9 |
| T009 | Sprachkenntnisse Einbürgerung (Basel) | 2 | 1 | partly (BüG 11/12, BS 153.300; **BüV 6 not retrieved**; OR 12 off-topic) | Never gives the core figure, B1 oral / A2 written (Art. 6 BüV), and says the requirements "nicht festgelegt" are. It gives no exemptions and no fide reference. | 89.6 |
| T010 | Permis G pour frontaliers (Sion) | 1 | 1 | partly (LEI 35/39/21 ok; Sion police regulation on fires and posters off-topic) | Still presents the third-country regime, including the art. 21 priority rule, as the general one, and ignores the ALCP regime for EU/AELE frontaliers (no zones, no priority check, 5-year G UE). It now pastes **Sion rules on open-air fires and posters** into the answer as "restrictions locales". | 163.8 |
| T011 | Permis catégorie C camion (Suchy) | 1 | 1 | partly (OAC 3/4/13 ok; OAC 35a/24a irrelevant) | The definition of cat. C and the SAN are correct. Most of the answer is about cancellation of the probationary licence, which is irrelevant. Still omits the prerequisites: cat. B held, age 18, medical exam (level-2 doctor), and the OACP/CZV certificate for professional drivers. Wrongly says the C licence is issued "pour une durée illimitée" without mentioning the periodic medical checks (art. 27 OAC). | 188.5 |
| T012 | Gültigkeit Lernfahrausweis (Zürich) | 3 | 3 | yes (VZV 16, ZH 741.11) | Correct and concrete (4/12/24 months, +12 after Grundschulung, grounds for expiry) and the citation markers are clean. Adds the ZH filing at the Einwohnerkontrolle. | 71.4 |
| T013 | Guidare con patente straniera? (Lugano) | 1 | 0 | **no** (OVF/VZV 44 retrieved but unused; LCStr 42 on noise off-topic) | Still misses the 12-month rule for new residents and the exchange requirement (VZV 42/44), even though VZV 44 was retrieved. The answer is about noise and loudspeakers (LCStr 42) and vehicle registration, and implies there is "no recognition" of foreign licences. That is misleading. | 132.9 |
| T014 | 0.8 Promille am Steuer (Bern) | 1 | 2 | mostly (SVG 91, AlkV 2 ok; StGB 306, BE 761.11/761.111 off-topic) | Now correct that 0.8 ‰ is the qualified threshold, with the criminal penalty of Art. 91 Abs. 2 lit. a SVG (up to 3 years or a monetary penalty). Still omits the key administrative consequence: serious offence, Art. 16c, **withdrawal of at least 3 months**. It pads the answer with the BE tax-data access article. | 116.4 |
| T015 | Excès de 25 km/h en localité (Genève) | 1 | 0 | **no** (LCR 90 al. 1, 16a; 16c missing; GE LPG/fourrière off-topic) | **Regression.** It calls 25 km/h in a localité an *infraction légère* (art. 16a) with an amende and an avertissement. In fact ≥ 25 km/h in a localité is **grave**: art. 90 al. 2 LCR, and art. 16c with withdrawal of at least 3 months. The old answer had the penal side right. It adds GE parking and fourrière rules and placeholder citations such as "[dispositions cantonales sur la fourrière]". | 150.4 |
| T016 | Auto nach Umzug neu einlösen? (Luzern) | 1 | 1 | partly (VZV 71/74 ok; LU Parkplatzreglement off-topic; LU 777 tax rules marginal) | It now says re-registration is needed on a change of canton, but then claims "Kontrollschilder und Fahrzeugausweis bleiben gültig". That is wrong: a change of canton requires a new Fahrzeugausweis and new plates. No 14-day deadline (Art. 74 Abs. 5 VZV) and no split between a move within the canton and a change of canton. | 128.0 |
| T017 | Casque à vélo électrique ? (Lausanne) | 0 | 0 | yes (OCR 3b now retrieved) | Retrieval is fixed, but the answer reverses the rule: it says the helmet is **compulsory for e-bikes ≤ 25 km/h**. The rule is the opposite: compulsory for fast e-bikes up to 45 km/h with a yellow plate, not for light mopeds ≤ 25 km/h. Its own exemption list contradicts the short answer. Still dangerous. | 85.6 |
| T018 | Höchstgeschwindigkeit Autobahn (Winterthur) | 3 | 3 | yes (VRV 4a, 5) | 120 km/h, with the start and end signals, and 100 km/h for the vehicle classes in VRV 5. Minor gap: 80 km/h for heavy goods vehicles is not mentioned. Concise, and the fastest answer at 49 s. | 49.2 |
| T019 | Controllo medico patente dopo 75 (Bellinzona) | 0 | 2 | yes (OAC 27, TI 760.110 50/51) | **Fixed.** Every 2 years from 75 (art. 27 cpv. 1 lett. b OAC), the cantonal reminder and the TI medici fiduciari are all correct. Garbles the C/D schedule ("dopo il 75° … entro i 77, poi ogni cinque anni"). | 93.7 |
| T020 | Trottinette électrique sur trottoir ? (Neuchâtel) | 0 | 0 | **no** (LCR 1/2, OAC 27g, NE 916.421; OCR/OETV not retrieved) | Still an empty "no source" shell. The answer: e-trottinettes ≤ 20 km/h are light mopeds treated like cycles. They are **not allowed on the sidewalk** unless signage permits it (art. 43 LCR, OCR). | 87.3 |

## Notes on the worst answers

- **T017 (0, dangerous):** the fix made OCR 3b reach the context, but the model reverses the e-bike categories and tells slow e-bike riders that a helmet is compulsory. Its own exemption bullets contradict this. Better retrieval does not help if the generation and verification step cannot read the exemption clause.
- **T015 (0, regression):** the verifier added LCR 16 and 16b in its rounds, yet the final answer classifies 25 km/h in a localité as *légère*. The tier tables (ASTRA practice / Federal Supreme Court case law: inside a localité, 16-20 légère, 21-24 moyennement grave, ≥ 25 grave) are not in any retrieved source, so the model guesses. It also leaves bracketed pseudo-citations ("[procédures administratives genevoises]") in the text.
- **T004 (0):** EU workers are still answered under the LStrI third-country rules. The ALC/OLCP is not in the index or is never retrieved. That is the same root cause as in T002, T005 and T010.
- **T013 (0):** VZV 44 was retrieved, but the model built the answer on LCStr 42 (noise). The 12-month exchange rule (VZV 42) is still missing.
- **T020 (0):** the retrieval for "trottinette/trottoir" still never reaches OCR/OETV, and the answer has no substance.

## Remaining failure patterns

1. **EU/ALCP regime missing** (T002, T004, T005, T010). Migration questions are answered only under the LEI third-country rules, with no case split by nationality or sponsor status. This is the most consequential remaining gap.
2. **Traffic sanction tiers and thresholds** (T014, T015, T017). The model picks the wrong tier or reverses categories, and it omits minimum withdrawal periods (16c: 3 months). This is high-stakes and needs a curated tariff and threshold note in the retrieval.
3. **Off-topic communal and cantonal regulations end up in the answer body, not only in the source list.** Examples: Sion fires and posters (T010), the Ecublens police regulation as the appeal venue (T001), the Lausanne "permis de c…" fee regulation turned into a renewal tax (T002), and GE parking and fourrière rules (T015). The communal retrieval matches on "permis" or "police" and the model feels obliged to fill the commune section.
4. **The verifier injects irrelevant sources.** CO/OR 266c (lease termination) was added by verification in T001, T004 and T008. OR 12, StGB 306 and LCR 17 were also added. The verification loop now runs 3 rounds on 17/20 questions (55 revisions vs 34), which drives latency up without fixing the substantive errors (T015 still wrong after adding 16b).
5. **Retrieved but ignored or declared absent.** KBüG GR in T008 and VZV 44 in T013 were retrieved, yet the answer says "keine einschlägige Quelle" or answers from the wrong article.
6. **Key ordinance figures still missing:** BüV 6 language levels (T009, a regression), OASA 60/62 (T001, T003), VZV 74 Abs. 5, 14 days (T016), and OCR/OETV for e-scooters (T020).
7. **Length and latency got worse.** Answers average 474 words (target < 230), latency is 129.7 s on average (+48 %), and 7 answers took more than 150 s. The Bund/Kanton/Gemeinde/"Art. 49 BV" template padding remains.
