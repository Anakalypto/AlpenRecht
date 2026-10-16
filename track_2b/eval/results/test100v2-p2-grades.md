# test100v2-p2 grades (T021-T040, Apertus-v1.5-70B, after fixes)

Graded by an AI reviewer agent (Claude, Anthropic) instructed to grade as a Swiss lawyer against the official texts; not reviewed by a human lawyer. Same rubric as before. 3 = correct, concrete, with the right sources and authority. 2 = mostly right, with minor gaps or imprecision. 1 = partly right, but with an important error, the wrong governing source, or too vague. 0 = wrong, off-topic, empty or an error. Each answer was graded on its own merits before the old grades were opened.

Run: `bench.py --set questions_test100_p2.json --tag test100v2-p2 --workers 3`. All 20 rows completed with no errors or timeouts, so no retry was needed. bench.py crashed *after* writing the JSON and MD files: `print(summary)` hit a cp1252 UnicodeEncodeError on "✗". This is cosmetic, but it gives exit code 1 on Windows consoles unless PYTHONIOENCODING=utf-8 is set.

**New average 1.95 / 3** (39/60), up from **1.70** (34/60).
Distribution: 3 → 5, 2 → 9, 1 → 6, 0 → 0 (old: 4 / 8 / 6 / 2).
Avg latency **110.7 s** (min 58.8, max 155.3), up from 73.0 s (min 30.9, max 133.1).

| id | question | old | new | sources ok | main issue | total_s |
|---|---|---|---|---|---|---|
| T021 | Mietkaution Höhe (ZH) | 3 | 3 | yes (OR 257e) | Correct: 3 Monatszinse, account in the tenant's name, release rules, 1 year. Clean | 104.2 |
| T022 | Hausse sans formule officielle (GE) | 2 | 3 | yes (CO 269d; "OLOG 12" label odd) | Correct: null without the form, 10 days, reasons given. Facsimile-signature rule credited to 269d (it is in OBLF 19). The GE filler is gone | 116.2 |
| T023 | Délai de résiliation (VD) | 1 | 2 | yes (CO 266c) | Correct rule now (3 months to the local-usage term). Vague: says the sources don't give the Vaud term (it is in the RULV / the lease). No written-form requirement (266l), no early return (264) | 96.0 |
| T024 | Untervermieten (BE) | 3 | 2 | yes (262, 273b) + off-topic BE EG ZGB 135a / OR 270 | 262 content correct. The short answer is padded with the Bern form obligation for the main lease, which is irrelevant to subletting. Unsourced "Formular beim Amt für Gemeinden und Raumordnung" | 126.4 |
| T025 | Accesso del locatore (TI) | 0 | 1 | **no** (257f, 266c, TI expropriation law) | Italian now (fixed). Conclusion ("not without notice") roughly right, but the governing CO 257h (visits with timely notice for maintenance, sale or re-letting) is missing. Built on 257f and expropriation acts | 122.1 |
| T026 | Schimmel – Minderung (BS) | 1 | 1 | partly (259a/d/e/g ok; BS 861.625, 724.115 off-topic) | Short answer makes deposit of rent / a deadline a condition for the reduction (wrong, that is 259g). Says damages are owed "sofern den Vermieter kein Verschulden trifft" (inverted: owed *unless he proves* no fault). Stiftungsrat-Ermässigung step is irrelevant | 137.8 |
| T027 | Loyer initial (FR) | 2 | 1 | partly (270 ok; 270a/270d misapplied) | 30 days correct, FR form now covered. **Error:** applies the 270a procedure (written request to the landlord, 30 days to reply) to the initial rent. The 270 challenge goes directly to the conciliation authority. "Situation du marché local" ground missing. 270d misparaphrased | 84.8 |
| T028 | Kleine Reparaturen (LU) | 2 | 2 | yes (OR 259) + off-topic LU 200 §38/§93g | Rule correct but thin (no CHF 100–200 practice figure, no landlord duty 256). Lists and comments on irrelevant Beistand / Grundbuch rules | 69.9 |
| T029 | Congé après demande de réparations (VS) | 1 | 2 | yes (271, 271a al.1 let.a, 273) + off-topic Sion police reg. | Right governing source now, 30-day deadline (273) correct, VS commission correct. Sion police regulation used to invent conciliation-request form rules ("date, heure, lieu de l'audience"). No 3-year protection (271a let.e) | 137.3 |
| T030 | Hund in der Mietwohnung (SG) | 0 | 1 | **no** (257f + SG Hundegesetz) | Wrong premise "grundsätzlich zulässig nach 257f". It turns on the lease and house rules or the landlord's consent; there is no statutory right. Garbled "fristlos ... erst nach 30 Tagen" (257f Abs. 3 is extraordinary notice). Dangerous-dog measures padding | 154.2 |
| T031 | Überstunden (BS) | 2 | 2 | partly (321c ok; milk-workers NAV, BS staff ordinance off-topic) | 321c and the 25% supplement correct. Short answer and next steps still built around BS cantonal staff rules. No ArG Überzeit (12/13). States Art. 49 BV backwards ("kantonales Recht geht vor") | 131.0 |
| T032 | Settimane di vacanza (TI) | 3 | 3 | yes (329a/329c/329e) | Correct (4 weeks / 5 up to age 20, 2 consecutive). 329e two-month notice garbled in the next steps | 100.6 |
| T033 | Temps d'essai (NE) | 2 | 2 | yes (335b) | Still omits the key default: **1 month** if nothing is agreed. Max 3 months, 7 days, extension correct | 67.5 |
| T034 | Kündigung bei Krankheit (ZH) | 2 | 2 | partly (336c ok; ZH Personalgesetz off-topic) | Periods, nullity and probation exception correct. ZH public-staff Mahnung rule mixed in. No suspension of a running notice (336c Abs. 2). "Missbräuchlich wegen Krankheit" overstated | 123.4 |
| T035 | Salaire maladie (GE) | 2 | 2 | partly (324a ok; GE J 3 05 off-topic) | Base rule (3 weeks in the 1st year, then equitable) correct. No 3-month condition, no Bernese/Geneva scale, no IJ insurance. GE LAMal affiliation for foreigners is in the short answer | 100.0 |
| T036 | 13. Monatslohn (BE) | 2 | 1 | partly (322d only) | Still conflates the 13th salary with a Gratifikation. Says pro rata only "sofern verabredet" (wrong for an agreed 13th salary, which is always pro rata). "Bund: Keine einschlägige Quelle" while citing [1] | 58.8 |
| T037 | Travail du dimanche (VD) | 3 | 2 | yes (LTr 18/19) | Correct on 23h–23h, SECO vs canton, 50%, consent, 4 Sundays. Says Sunday work is otherwise "prohibé" and ignores the OLT 2 sector exemptions (old answer cited OLT2). No compensatory rest (LTr 20) | 130.0 |
| T038 | Mutterschaftsurlaub (LU) | 1 | 3 | yes (EOG 16c/16d, EOV) | Fixed: 98 days / 14 weeks, +56 days for hospitalisation, end of claim. Minor: OR 329f / ArG 35a not cited | 95.0 |
| T039 | Konkurrenzverbot (GR) | 1 | 3 | yes (OR 340–340c) | Fixed: written form, insight requirement, 3-year limit, judicial reduction, Konventionalstrafe, lapse. Complete | 155.3 |
| T040 | Licenciement immédiat (VS) | 1 | 1 | partly (337/337c ok; Sion police reg., VS 822.1, CO 127 wrong) | 337c consequences now correct (fixed). But the Sion section and next steps tell the user about the animal pound and poster rules. Still sends to the prescription of CO 127 (10 yrs; salary is 5 yrs, 128). Admin-appeal step irrelevant | 103.1 |

## Worst answers

- **T040 (1):** the legal core is now right (337, 337c), but the answer reproduces off-topic Sion police rules on impounding animals and posting bills. One next step says "respect the police regulation to avoid your animal being impounded". This would destroy user trust. The CO 127 10-year prescription error from the old run is still there.
- **T030 (1):** still answered from the dangerous-dog law. The premise is wrong: there is no general right to keep a dog under 257f. The lease or house rules and the landlord's consent decide.
- **T026 (1):** two errors in the short answer: it makes deposit of rent a condition for the reduction, and it inverts the burden of proof for damages (259e). The detailed section below is correct, so the short answer contradicts the body.
- **T027 (1, regression):** applies the 270a procedure (request to the landlord, 30-day reply) to the initial rent. The tenant would lose time when the 30-day deadline to go to the conciliation authority is running.
- **T036 (1, regression):** the 13th salary is still treated as a Gratifikation, with a wrong pro-rata statement. The headings contradict the citation ("keine Quelle" plus [1]).
- **T025 (1):** the language is fixed, but CO 257h, the decisive provision, is still absent. The answer is built on 257f and Ticino expropriation law.

## Improvements vs the old run

- T038 (+2) and T039 (+2): fully fixed. The federal EO rule is used instead of cantonal staff law, and there is no more invented 339c "Entschädigung".
- T025 (+1): Italian instead of Romansh. T030 (+1): no OR 266 nonsense, though still weak.
- T023 and T029 (+1 each): the right governing article is now cited (266c; 271a + 273), with correct deadlines.
- T022 (+1): the off-topic GE filler is gone.
- No 0 scores. Invented deadlines dropped markedly (no "1 Jahr ZPO", no "30 j. après réponse").

## Regressions

- **T024 (3→2):** an irrelevant Bern form obligation is pulled into the short answer, plus an unsourced claim about which office supplies the form.
- **T027 (2→1):** the new 270a/270d sources were misapplied, giving the wrong procedure.
- **T036 (2→1):** the pro-rata error is now stated explicitly, and the Bund heading contradicts the citation.
- **T037 (3→2):** OLT 2 is no longer retrieved, so the answer overstates the prohibition.

## Remaining failure patterns

1. **Off-topic cantonal or communal sources still reach the answer** (11/20 have wrong-topic sources). The worst are T040 and T029 (Sion police regulation), T025 (expropriation), T030 (dog law), T028 (Beistand / Grundbuch) and T026 (BS Stiftung). The model often notes that a source is irrelevant but still lists it or builds next steps on it.
2. **Cantonal public-staff law mixed into private employment answers** (T031 BS, T034 ZH, T035 GE). Better than before (T038 fixed), but not solved.
3. **The short answer contradicts the detailed section** (T026 burden of proof, T036 heading vs citation). The short answer is where the errors land.
4. **Neighbouring article used instead of the decisive one** (T025 257f vs 257h; T027 270a vs 270; T040 127 vs 128).
5. **Key default rules missing** (T033 one-month default, T035 3-month condition and court scale, T028 practice amount, T023 Vaud usage terms).
6. **Art. 49 BV boilerplate**, sometimes stated backwards (T031).
7. **Latency regressed sharply:** 110.7 s on average (+52%), with 7/20 above 125 s. This is probably the extra verification and revision passes, and it is too slow for interactive use.
