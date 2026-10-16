# test100-p2 grades (T021-T040, Apertus-v1.5-70B)

Graded by hand, from an expert Swiss-law point of view. Scale: 3 = correct and concrete, 2 = mostly right with minor gaps, 1 = partly right but with an important error or a wrong source, 0 = wrong, off-topic or in the wrong language.
Run: `bench.py --set questions_test100_p2.json --tag test100-p2 --workers 3`. All 20 rows completed with no errors or timeouts.

**Average 1.70 / 3** (34/60). Distribution: 3 → 4, 2 → 8, 1 → 6, 0 → 2. Avg latency 73.0 s (min 30.9, max 133.1).

| id | question | score | sources ok | main issue | total_s |
|---|---|---|---|---|---|
| T021 | Mietkaution Höhe (ZH) | 3 | yes (OR 257e) | Correct (3 Monatszinse, Bank, 1 Jahr). Minor: "Obergrenze nicht unterschreiten" is the wrong way round | 51.9 |
| T022 | Hausse sans formule officielle (GE) | 2 | yes (CO 269d, OBLF 19/20) | Core correct (nulle, 10 j., 30 j. contestation 270b). Off-topic GE "contrat-cadre / Feuille d'avis" in the short answer; next steps written for the landlord | 91.9 |
| T023 | Délai de résiliation appartement (VD) | 1 | partly (266a/272d instead of 266c, 264) | Says "3 mois pour la fin d'un mois". The legal rule is 3 months to the next local-usage term (266c). Says the tenant must use the cantonal official form, which applies only to the landlord (266l). No mention of early return (264) or the spouse's co-signature (266m) | 81.3 |
| T024 | Untervermieten (BE) | 3 | yes (OR 262, 273b) | Correct and complete. The "Nächste Schritte" step telling the tenant to inform the landlord of disadvantages is odd | 56.5 |
| T025 | Accesso del locatore senza preavviso (TI) | **0** | no (257h retrieved but not used) | **Answered in Romansh, not Italian.** Ignores CO 257h (visits for maintenance, sale or re-letting with timely notice). Wrongly says cantonal or communal law prevails | 95.7 |
| T026 | Schimmel – Mietzinsminderung (BS) | 1 | yes (OR 259a/259d) | Reduction runs from the landlord's knowledge (259d), not the tenant's. Invented "Klagefrist ZPO 1 Jahr". Skips the Schlichtungsstelle and goes straight to the Mietgericht. Deposit of rent without the 259g conditions; no warning against unilateral reduction | 54.1 |
| T027 | Contester le loyer initial (FR) | 2 | yes (CO 270) | 30 days and conditions correct. Says federal law "impose aux cantons" the official form (wrong: the cantons *may* require it). Fribourg's own form requirement not mentioned. Irrelevant OBLF 26 transitional rules | 56.8 |
| T028 | Kleine Reparaturen (LU) | 2 | yes (OR 259) | Rule correct but no practical amount (about CHF 150–200 in practice). Landlord step is inverted. Deposit of rent stated without the 259g conditions (written deadline, prior notice) | 94.1 |
| T029 | Résiliation après demande de réparations (VS) | 1 | **no** (266g, LBFA) | Conclusion right, but cites 266g (justes motifs) instead of 271/271a al.1 let.a CO. Omits the 30-day deadline to contest from receipt of the notice (273) and the 3-year protection (271a let.e). Wrong deadline "30 j. après la réponse" | 48.5 |
| T030 | Hund in der Mietwohnung (SG) | **0** | **no** (SG Hundegesetz, OR 266) | Off-topic: dangerous-dog measures and OR 266 (fixed-term lease). Ignores the lease and house rules, the landlord's consent, 257f, and the Federal Supreme Court view on blanket bans. Invents a "Hausrecht" basis | 133.1 |
| T031 | Überstunden anordnen (BS) | 2 | partly (OR 321c ok; BS staff ordinance) | 321c and the 25% supplement correct. Large part applies Basel-Stadt cantonal staff rules to a generic employee. No ArG Überzeit (Art. 12/13 ArG) distinction | 99.6 |
| T032 | Settimane di vacanza (TI) | 3 | yes (CO 329a/329c) | Correct (4 weeks / 5 weeks up to age 20, pro rata, 2 consecutive weeks) | 30.9 |
| T033 | Durée du temps d'essai (NE) | 2 | yes (CO 335b) | Omits the key default: **1 month** if nothing agreed. Max 3 months, 7-day notice and extension correct | 52.0 |
| T034 | Kündigung während Krankheit (ZH) | 2 | mostly (OR 336c; NAV Hauswirtschaft misapplied) | Periods correct. "Nein" is too absolute: the dismissal is void only during the protection period, and the protection does not apply during probation. No suspension of the notice period (336c Abs. 2). Cites the ZH household-workers NAV as general cantonal law | 58.4 |
| T035 | Salaire en cas de maladie (GE) | 2 | partly (CO 324a/324b; LDét irrelevant) | Base rule correct. Misleading "assuré obligatoirement contre la maladie" (LAMal is not loss-of-earnings insurance). No court scale (Bernese) and no equivalent IJ insurance (80%, 720 days). Posted-worker digression | 81.1 |
| T036 | 13. Monatslohn (BE) | 2 | partly (OR 322d) | Treats the 13th salary as a Gratifikation. If agreed it is salary (pro rata always), unlike a discretionary Gratifikation. No mention of GAV/NAV | 75.4 |
| T037 | Travail du dimanche (VD) | 3 | yes (LTr 18/19, OLT2) | Correct (23h–23h, SECO vs canton, 50%, consent, 4 Sundays). Vaud-specific rules missing; next steps addressed to "canton/commune" | 87.8 |
| T038 | Mutterschaftsurlaub (LU) | 1 | **no** (LU staff law only) | Gives 16 weeks (LU cantonal staff) as the general answer. Federal 14 weeks / 98 days, 80% EO (EOG 16b ff., OR 329f) missing ("Bund: keine Quelle") | 62.8 |
| T039 | Konkurrenzverbot gültig? (GR) | 1 | partly (OR 340/340a ok; 339c, 127 wrong) | Invents a 2–8 month "Entschädigung" (that is the 339c severance payment, irrelevant). 10-year limitation for a "Klage" is nonsense. Missing 340b (Konventionalstrafe) and 340c (lapse) | 64.1 |
| T040 | Licenciement immédiat (VS) | 1 | partly (CO 337 ok; 127, LDét wrong) | Says the claims prescribe in 10 years; salary claims prescribe in **5 years** (128 ch. 3 CO). Omits 337c (salary for the notice period plus an indemnity of up to 6 months) and the need to react immediately | 83.6 |

## Worst answers

- **T025 (0):** answered in Romansh instead of Italian. Ignored the relevant CO 257h, which was retrieved, and said cantonal law prevails over federal law.
- **T030 (0):** retrieval returned the St. Gallen dangerous-dog law and the LLM built the answer on it. The tenancy question (lease or house-rules clause, consent, 257f) went unanswered, and an irrelevant OR 266 statement was added.
- **T038 (1):** cantonal staff law (Luzern, 16 weeks) was presented as the general rule. The federal 14 weeks / 80% EO, which applies to almost every user, is absent.
- **T039 / T040 (1):** off-topic articles retrieved alongside the right one (339c severance, 127 ten-year limitation) were turned into confident, wrong legal statements, including a wrong limitation period.
- **T023 / T029 (1):** a neighbouring article was cited instead of the key one (266a instead of 266c; 266g instead of 271a). This led to a wrong deadline or the omission of the decisive deadline.

## Recurring failure patterns

1. **Cantonal-staff or special-sector law presented as general law** (T031 BS staff, T034 ZH household NAV, T038 LU staff). The retriever returns cantonal public-employment acts and the answer treats them as applying to private employees.
2. **Neighbouring or irrelevant articles cited** (T023, T029, T030, T039, T040; LDét / médecins-assistants / EpG / Lohngleichheit retrieved in T034–T036). The answer then turns their content into claims.
3. **Invented or wrong deadlines** (T026 "1 Jahr ZPO", T029 "30 j. après réponse", T039/T040 10-year limitation). Deadlines are where errors are most costly.
4. **Key default or practical rule missing** (T033 one-month default, T028 no amount, T035 no court scale, T040 no 337c consequences).
5. **Off-topic "cantonal" filler**, because the template forces a cantonal section (T022 GE contrat-cadre, T030 dog law).
6. **Wrong language** (T025 Romansh for an Italian question).
7. **Perspective drift**: next steps written for the landlord, canton or court instead of the user (T022, T028, T037, T039).
8. **Latency:** 73 s on average and up to 133 s, too slow for an interactive app.
