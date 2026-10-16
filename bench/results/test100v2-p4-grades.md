# Grades: test100v2-p4 (Apertus-v1.5-70B), building/zoning/neighbour + communal, after the fixes

Graded by hand as a strict Swiss lawyer. Each answer was graded on its own merits first, then compared with `test100-p4-grades.md`.
Run: 20/20 rows, 0 errors or timeouts, no retry needed. (bench.py exited with code 1 only because printing the summary to a cp1252 console failed on "✗". The JSON and MD were written before that.)

**Avg score 1.60 / 3** (old 1.50). Distribution: 3: 4, 2: 6, 1: 8, 0: 2 (old 3: 2, 2: 8, 1: 8, 0: 2).
**Avg latency 117.4 s** (old 84.9 s). Min 58.7, median 134.0, max 195.9.

| id | question | old | new | com regulation found/used | main issue | total_s |
|---|---|---|---|---|---|---|
| T061 | Lausanne: permis panneaux solaires ? | 2 | **1** | found but wrong topic (Règl. antennes extérieures) / not relevant | **Regression.** LAT 18a (roof solar installations need only an announcement) and OAT 32a were not retrieved. LAT 24ter (non-national-interest solar plants outside the building zone) came back instead. So the answer says "oui, autorisation nécessaire" except for minor works, which is wrong for conforming roof panels. Padded with an irrelevant step on the 2-year implantation permit and a 5-year plan d'affectation deadline. CO 266c in the list. | 135.9 |
| T062 | Zürich: Baubewilligung Gartenschuppen? | 1 | 1 | found (OrgR Bausektion Art. 4), procedural only / not used | BVV ZH (700.6) was retrieved, but only §§ 7/15/17/19 (procedure), not § 1 (bewilligungsfreie Kleinbauten). No exemption threshold given. Kanton/Gemeinde say "keine einschlägige Quelle", yet [3][4][5] are cited in the next steps. Slowest answer. | 195.9 |
| T063 | Bern: Grenzabstände für Bauten | 1 | **2** | **found and used** (BO Stadt Bern Art. 33/34/36) | Correct chain: BauG BE Art. 12 (delegation to communes) → BO Bern (definitions of grosser/kleiner Grenzabstand, Gebäudeabstand, Näherbau with consent). Still no actual metre figures (these depend on the Bauklasse/zone table). RPG 19 Erschliessung is padding. EG ZGB private-law distances missing. | 83.2 |
| T064 | Lugano: licenza per piscina | 2 | 2 | not found | The conclusion (licence needed, granted by the Municipio after cantonal advice) is right and LE/RLE TI are the right acts. Problems: it claims that LE art. 1 / RLE art. 4 "esplicitamente" list pools (doubtful), it files the application with the UDC instead of the Municipio, and it leaves out the notification procedure for small pools. | 94.7 |
| T065 | Fribourg: voisin trop bruyant | 0 | **1** | **found and used** (RGP Ville de Fribourg art. 38) | Improvement: the communal police rule on noisy activities is now used. Still leaves out CC 684/679 (civil action) and CO 257f (tenant). Most of the answer covers plan opposition and appeal (LATeC 84-88), which applies to land-use plans, not to an existing noisy neighbour. LPE 20 / OPB 7 / 37a are wrong topic. | 185.0 |
| T066 | Luzern: Äste vom Nachbarbaum abschneiden? | 2 | 2 | n/a (VNöG retrieved, correctly called irrelevant) | ZGB 687 is correct and LU EGZGB §§ 86/87 (Grenzabstände, Zutrittsrecht) are now present. Error: it says "der Schnitt muss die kantonalen Grenzabstände einhalten" and misreads the 0.5 m distance as "gegenüber Wald". This mixes up the planting-distance rules with the Kapprecht. | 134.9 |
| T067 | Genève: autorisation véranda ? | 1 | 1 | not found (Ville de Genève: none) | LCI L 5 05 art. 1-3 are right (permit, mandataire qualifié, FAO 30 days). It again misapplies the art. 1 interior-works exemption to "une véranda située à l'intérieur d'une villa". The APA procedure (LCI art. 3 al. 7) is still missing. Mentions CO 266c (lease termination) with no reason. | 149.1 |
| T068 | Aarau: welche Bauten bewilligungsfrei? | 1 | **0** | found (BNO Aarau §§ 17/23) / **not used** | **Regression.** BauV AG § 49 (the list of exempt works) is no longer retrieved. The answer wrongly says that there are no bewilligungsfreie Bauten and that cantons "dürfen keine zusätzlichen bewilligungsfreien Tatbestände einführen". Both are wrong (see RPG 18a, BauV AG § 49). § 67a (relief from distance rules) is presented as the answer. | 139.2 |
| T069 | Sion: louer sur Airbnb ? | 2 | 2 | not found (old run had the Sion tax rules) | CO 262 (landlord consent) is now present, which is good. The cantonal taxe de séjour (LTour VS) is detailed. The LPC VS / announcement duty and the communal tax rules from the old run are gone. PPE regulation not mentioned. CO 266c notice period is irrelevant. | 134.0 |
| T070 | Chur: Stockwerkeigentum Renovationen | 1 | 1 | not found | Better core: ZGB 647c and 647e majorities are now stated correctly. Still leaves out 647d (nützliche Massnahmen), the most common renovation category. The short answer is half filled with GR EGzZGB Art. 99 Brandmauer rules between neighbours, misapplied to StWE "Miteigentümer". | 175.2 |
| T071 | Chur: ab wann Nachtruhe? | 3 | 3 | **found and used** (PG Chur Art. 30) | 23-07 h plus the evening/holiday rule, concrete. ZGB 437 and OR 266c are random entries in the source list. | 82.3 |
| T072 | Bern: Hund an der Leine? | 2 | **3** | **found and used** (HV Stadt Bern Art. 3) | Improvement from the new Bern reader: cantonal Hundegesetz Art. 7 plus the city's extra leash zones (buildings, Tierpark, annexes, cemeteries). Microchip paragraph is padding. | 67.4 |
| T073 | Ittigen: Hundetaxe? | 1 | 1 | **not found** (old run had it but did not use it) | No CHF figure. Gives only the cantonal framework (Hundegesetz BE Art. 13 exemptions). ZGB 779l, OR 1170 and BE 661.11 are random entries. | 80.6 |
| T074 | Morges: heures de repos ? | 0 | 0 | found (Règl. police art. 52/81) / wrong articles | Still answers labour-law rest periods (LTr 15a, OTR 2). The Morges police regulation was retrieved, but only articles on fires and hygiene, not the night/midday quiet-hours article. Adds a labour-court step. | 151.7 |
| T075 | Sion: coût concession de tombe | 1 | 1 | found (règl. cimetières art. 27) / no figures | Says honestly that the tariffs are in an annex that was not retrieved. No invented "trentenaire" this time. No CHF amount. CC 5/915 and VS 173.8 are random entries. | 60.3 |
| T076 | Fribourg: calcul taxes déchets | 2 | **3** | **found and used** (règl. déchets art. 21/23-25) | Concrete: base fee ≤ CHF 150 set by the Conseil général, bag tariffs 1.50/2.50/4.00/7.50 set by the Conseil communal, LGD FR art. 23 (≥ 70 % cost cover, half proportional). Doubtful details from the old run are gone. USG 32a still missing. | 58.7 |
| T077 | Wädenswil: Abfallgebühren berechnet? | 2 | 2 | **found and used** (Abfallgebührenordnung Art. 2-5) | Good structure (base fee by rooms/m², 50 % refund if unused, fees per bag/weight). No CHF amounts. The cantonal part uses ZH 710.2 (fees for environmental-law enforcement), which is the wrong act; it should be AbfG ZH / USG 32a. One citation is invented ("[allgemeine verwaltungsrechtliche Beweisregeln des Kantons Zürich]"). | 153.2 |
| T078 | Holderbank SO: Kehrichtabfuhr Kosten | 2 | **1** | found (Gebührenreglement §§ 1/5) / no figures | **Regression.** § 4 (Fr. 100 per household) is no longer retrieved, so there is no figure. "Kantonales Recht geht vor, Art. 49 BV" is wrong again. OR 941, ZGB 954 and SO 615.11 are random entries. | 68.0 |
| T079 | (coords → Rickenbach TG): Grabesruhe | 3 | 3 | **found and used** (Friedhofreglement Art. 35) | 20 / 15 years plus the 8-year urn rule. ZGB 686 is a random entry. | 70.8 |
| T080 | Cham: Bewilligung Reklameschild? | 1 | **2** | **found and used** (Reklamereglement § 3) | Improvement: the general permit duty and the concrete exemptions (Angebotstafeln, 25 cm Storen-Volants, 0.2 m² Einzeltafeln) are now used. Problems: the exemptions are wrongly called "nur Bauanzeige". The V PBG ZG § 44 list (heating, Erdwärme, Dachfenster) is padding. SSV (signs along roads) missing. | 128.6 |

## Summary vs old run
- **Score**: 1.60 vs 1.50. 6 up (T063, T065, T072, T076, T080 by +1; none by +2), 3 down (T061, T068, T078), 11 unchanged.
- **Communal regulation (T071-T080)**: found 9/10 (old 8/10). Used well 6/10 (old 5/10): T071, T072, T076, T077, T079, T080. Used without figures: T075, T078. Not found: T073. Wrong articles: T074.
- **Big cities (new readers)**:
  - Bern: clear win on both questions (T063 BO Art. 33-36, T072 HV Art. 3).
  - Zürich (T062): only an organisational regulation came back, not BZO/BVV § 1, so no gain.
  - Lausanne (T061): the reader returned an off-topic antenna regulation, and the answer got worse because LAT 18a also went missing.
  - Genève (T067): no communal hit. This is expected, since the canton governs.
  - Basel: no question in this set.
- **Factual errors**: about 10 answers (T061, T064, T065, T066, T067, T068, T070, T074, T077, T078) vs about 11 in the old run. The kind of error shifted: fewer invented deadlines; more misapplied retrieved provisions (Brandmauer, Grenzabstände, LATeC plan opposition).
- **Wrong-topic sources**: still in about 17/20 source lists. OR 266c (lease termination) leaks into T061, T067, T069 and T071. Random ZGB/OR entries fill the federal slot in 7/10 communal questions (old: 13/20 overall).
- **Latency**: 117.4 s vs 84.9 s (+38 %). 9 answers took over 130 s; the max was 195.9 s (T062). The extra time is probably the verification/revision pass plus the bigger contexts from the new readers. Three bench runs (p1/p4/p5) were running in parallel, which may also have added time.

## Worst answers
- **T068 (0)**: says no works are exempt from a permit and that cantons may not add exemptions. Both statements are false (RPG 18a, BauV AG § 49). The old run had the correct AG list; retrieval lost it.
- **T074 (0)**: "heures de repos" is still read as labour law. The Morges police regulation is now retrieved, but only the wrong articles (fires, hygiene).
- **T061 (1)**: the solar-panel answer lost LAT 18a and now says a permit is required. This is the opposite of the federal rule since 2014. The Lausanne reader added an antenna regulation.
- **T065 / T070 (1)**: the answer is built around a retrieved provision that does not fit the question: LATeC plan opposition for neighbour noise, and GR Brandmauer rules for StWE renovations.

## Remaining failure patterns
1. **Anchor provisions not retrieved, or lost between runs**: LAT 18a / OAT 32a, BVV ZH § 1, BauV AG § 49, CC 684, ZGB 647d, Gebührenreglement Holderbank § 4. Retrieval is unstable from run to run (T061, T068 and T078 regressed only because of this).
2. **Misapplication of retrieved but neighbouring provisions**: the model forces whatever was retrieved into the answer (Brandmauer → StWE, Grenzabstände → Kapprecht, plan opposition → noise, interior-works exemption → véranda).
3. **Communal reader returns the right regulation but the wrong article** (Morges art. 52/81 instead of the quiet hours; Holderbank §§ 1/5 instead of § 4; Zürich OrgR instead of BZO; Lausanne antennas). Tariff annexes are still not indexed (T073, T075, T077, T078: no CHF figures).
4. **Filler sources**: random OR/ZGB articles and recurring OR 266c in the source lists.
5. **Small errors that keep coming back**: Art. 49 BV stated the wrong way round (T078), invented citations (T077), "keine einschlägige Quelle" while still citing sources (T062).
6. **Latency** went up by about 32 s on average. The 175-196 s answers (T062, T065, T070) are long and padded.
