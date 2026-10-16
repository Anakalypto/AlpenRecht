# Grades: test100-p5 (Apertus-v1.5-70B, T081-T100)

Graded by an AI reviewer agent (Claude, Anthropic) instructed to grade as a Swiss lawyer against the official texts (StGB, DSG/DSV 2023, DBG/StHG/cantonal tax law, OR, SchKG, LEI); not reviewed by a human lawyer. Scale 0-3. All 20 rows ran with no pipeline error, so no retry was needed.

**Average 1.60 / 3**: two 3s, nine 2s, eight 1s and one 0. **Average latency 83.7 s** (fastest 37.5 s, slowest 164.6 s).

| id | question | score | sources ok | main issue | total_s |
|---|---|---|---|---|---|
| T081 | Heimlich filmen strafbar? (ZH) | 2 | partial (179quater ok; 320/321, ZH 551.11 noise) | Says "ja, heimliches Filmen ist strafbar" without limit: 179quater only covers the Geheim- and Privatbereich, filming in public is not criminal under it. No ZGB 28/DSG. Spends space on 179sexies (devices) | 66.2 |
| T082 | Insulter sur réseaux sociaux (VD) | 2 | yes (177, 31 CP) | Core correct (177, 90 jours-amende, plainte 3 mois). Says the judge "renonce" (mandatory) where the law says "peut exempter". No 173/174 for factual allegations online | 95.2 |
| T083 | Ohrfeige strafbar? (BE) | 2 | partial | 126 correct (Busse, Antrag, Offizialdelikt for partners/wards). Imports the 177 exemption rules as if they applied to 126. No 123 if there is an injury | 72.0 |
| T084 | Danneggiare proprietà altrui (TI) | 1 | no (LCAP, WIPO convention, LRespPubb) | 144 correct. Then says the querela can be filed within the **10-year prescription period**, which is wrong: the deadline is 3 months (art. 31 CP). Half the answer is about state liability for public agents (off-topic). No art. 41 CO | 145.7 |
| T085 | Entreprise doit m'informer ? (GE) | 1 | no (Art. 12 registre, LPN, obtentions végétales) | Art. 19 LPD not retrieved. Uses the **processing register (Art. 12)** as the duty to inform, so the list of items is wrong. Mixes in GE LIPAD (public bodies). "Next steps" address the company, not the user | 68.5 |
| T086 | Datenpanne melden? (BS) | 2 | partial (Art. 24 ok; BS public-body law) | Art. 24 DSG correctly rendered (hohes Risiko, EDÖB, content, info to data subjects). Wrongly suggests a company may report to the **cantonal** DSB "je nach Trägerschaft". Art. 26 digression | 69.5 |
| T087 | Ask company what data it holds (ZH) | 2 | yes (Art. 25) | Art. 25 correct. Misses the 30-day deadline (DSV 18) and states fees wrongly (it is free in principle, CHF 300 max under DSV 19, and there are no "cantonal charges"). Calls the EDÖB "cantonal". Says cantons "may not impose stricter" rules | 75.4 |
| T088 | Qu'est-ce que la diffamation ? (NE) | 2 | yes (173) | Definition correct. Al. 3 is garbled (it excludes the proof of truth, it is not a separate offence) and so is al. 5. Never contrasts calomnie (174) or injure (177) although both were retrieved | 113.1 |
| T089 | Telefongespräch aufnehmen (SG) | 1 | partial (179bis/ter right, PAVO/V-StGB noise) | **Mixes up 179bis and 179ter**: says 179ter = keeping or using recordings from 179bis. In fact 179ter is a participant recording without consent (up to 1 year), the user's most likely case. No own vs foreign conversation distinction, no 179quinquies | 41.8 |
| T090 | Caméra qui filme la rue (VS) | 0 | no (VS police law, LPD 36/37 federal organs) | **Wrong reading**: treats the user as a public authority. Tells them to ask the conseil général to adopt a communal regulation. Nothing on a private camera (DSG proportionality, EDÖB: public space must not be filmed, 179quater towards neighbours) | 93.0 |
| T091 | Steuerabzüge (ZH) | 1 | partial (DBG/StG ok; DBA Dänemark noise) | "Spenden bis Fr. 100.– pro Empfänger" is wrong: CHF 100 is the **minimum**, the maximum is 20%. The 40% Leibrenten rule is outdated (2025 reform). Says Sozialabzüge are "bundesrechtlich geregelt". ZH deadline given as 30 April, it is 31 March. No 3a cap, Kinderabzug or premium figures | 164.6 |
| T092 | Deduzioni fiscali Ticino | 1 | partial (only TI Berufskosten regulation) | Covers **only professional expenses** and presents that as the answer. Misses premiums, 3a, children, interest, medical costs, donations. Says the Confederation has "no source" although LIFD was retrieved. Claims cantonal rules "prevail" | 52.2 |
| T093 | Imposition de la fortune (GE) | 1 | partial (LIPP ok; LIFD 13/14, DBA noise) | Top rate given as "**3,83 %**", which is impossible: wealth tax rates are per mille. Does not say that there is no federal wealth tax. Cites Art. 127 Cst. as "principles of wealth tax". GE social deductions not quantified | 122.1 |
| T094 | Haustürvertrag widerrufen (BE) | 2 | partial (40d/40e ok; OR 216, BE noise) | 14 days, formfrei, Fristbeginn and Beweislast all correct. Misses the exclusions in Art. 40c (customer asked for the visit, market stall, < CHF 100) and the consequences under Art. 40f | 51.1 |
| T095 | Durée de la garantie (VD) | 2 | yes (210 CO) | 2 years, 5 years (immeuble), biens culturels and al. 4 all correct. Omits the duty to inspect and notify immediately (Art. 201) and that the warranty can be **excluded entirely** (Art. 199) | 37.5 |
| T096 | Rechtsvorschlag erheben (BS) | 3 | yes (74/75) | Correct and concrete (10 days, oral or written, no reasons, partial dispute, free certificate). Could add Rechtsöffnung and Art. 265a | 73.4 |
| T097 | "permis" (FR) | 1 | partial (LEI ok; Finland agreement noise) | Picks residence permit without stating the assumption or offering permis de conduire/construire. Short answer garbled ("séjour d'au moins une année" as a requirement). Ignores the ALCP route for EU citizens. Long | 150.2 |
| T098 | "Kündigung" (ZH) | 1 | yes for tenancy | Silently picks tenancy (employment is just as likely). Misses written form and the approved form for landlords (266l), the 30-day challenge period (273) and the Familienwohnung rule | 55.7 |
| T099 | "cane" (TI) | 2 | partial (TI Legge cani ok; LRCN nuclear, space convention noise) | Sensible reading (keeping a dog in TI): insurance, courses, tax CHF 75-125. Assumption not stated. No Art. 56 CO liability or AMICUS microchip. Says "no federal source" although LPAn was retrieved | 74.6 |
| T100 | Landlord keep deposit? (BE) | 3 | yes (257e) | Correct (bank account in tenant's name, max 3 months, release conditions, 1-year rule). Could say explicitly that deductions require agreement or a judgment | 51.5 |

## Worst answers

- **T090 (0):** The question is plainly from a private person who wants a camera facing the street. The model answered as if the user were a commune and told them to get a communal regulation adopted and approved by the Conseil d'État. Private video surveillance falls under the DSG (proportionality; the EDÖB says public space must essentially not be filmed) and under 179quater towards neighbours. Neither is mentioned.
- **T089 (1):** It swaps the content of 179bis and 179ter. The everyday case, someone recording a call they take part in, is exactly 179ter (up to 1 year or a fine). The answer presents 179ter as an offence of "keeping or using" recordings.
- **T084 (1):** It tells the victim the complaint can be filed within the 10-year prescription period. The Antragsfrist is 3 months, so a user following this would lose the right to complain. Most of the answer is cantonal state liability for public agents, which is irrelevant.
- Close behind: **T085** (register instead of the duty to inform), **T093** (3,83 % wealth tax rate) and **T091** (CHF 100 donation minimum turned into a cap).

## Recurring failure patterns

1. **Retrieval misses the key article and the model answers from the nearest neighbour.** Art. 12 instead of Art. 19 LPD (T085), public-authority video rules instead of DSG (T090), state-liability law (T084). The model never says "the core provision was not retrieved".
2. **Off-topic federal noise in almost every source list.** Double-taxation agreements (T091-T093), Finland agreement (T097), nuclear liability and the space convention (T099), PAVO (T089), plant varieties and LPN (T085). 14 of 20 rows have clearly irrelevant sources.
3. **Deadline and number errors in "next steps".** 10-year prescription given as the complaint deadline (T084), wrong tax-return dates (T091), per mille vs percent (T093), donation minimum turned into a cap (T091).
4. **Mis-paraphrasing statutes.** Article content swapped (179bis/ter), "peut" turned into a mandatory rule (T082), 177 exemptions grafted onto 126 (T083), garbled 173 al. 3/5 (T088).
5. **Public-law cantonal sources applied to private parties.** Cantonal DSB for a company (T086), GE LIPAD (T085), communal regulation (T090).
6. **Ambiguous queries are never flagged.** T097, T098 and T099 each pick one reading without saying so or offering alternatives.
7. **Boilerplate.** Every answer has an "Art. 49 BV" paragraph and empty "Kanton/Gemeinde: keine Quelle" sections. Statements about how the levels fit together are sometimes wrong ("cantonal rules prevail", "cantons may not be stricter").
8. **Incomplete coverage of broad questions** (T091, T092): one category is treated in detail and presented as the whole answer.
9. **Latency.** 83.7 s on average; the broad tax and ambiguous questions take 120-165 s.
