# Fees, émoluments and figures (2026-10-16)

Set: eval/questions_fees.json, 18 questions (communal dog/waste/grave/parking/building fees in 12 communes incl. the
big cities and Lugano; federal fees for debt-collection extracts, passports, naturalisation; a speeding fine).
Metric: the short answer states an amount taken from a source.
These changes (commit 9eb4d52) came after the held-out evaluation. They were measured on this set and on the
regression sample below, not on the held-out 100 questions (see `heldout/README.md`).

| run | amount in short answer | avg time |
|---|---|---|
| before (`results/Apertus-v1.5-70B-fees-base.json`) | 6/18 | 71 s |
| after (`results/Apertus-v1.5-70B-fees-v4.json`) | 17/18 in the full run; 18/18 after a targeted re-run of F18 (`results/Apertus-v1.5-70B-fees-v6.json`) | 78 s |

Verified figures: Ittigen dog tax Fr. 100; Basel CHF 160; Lugano CHF 115; Fribourg CHF 100; Chur Fr. 150–300;
Wädenswil waste base fee CHF 140 / 90; Lausanne bag CHF 1.95 (35 L); Sion grave concession CHF 1 500 / 25 years;
Zürich parking card Fr. 300; Bern Fr. 264/year; Geneva terraces CHF 21–100/m²; Lausanne building permit CHF 200–5 000;
Betreibungsregisterauszug CHF 17 (GebV SchKG 12a); passport CHF 140 (OLDI annex 2); naturalisation CHF 100/150/50
(OLN 25); 11–15 km/h in town Fr. 250 (OBV annex 1).

What changed
- Communal: for fee questions the tariff that goes with a chosen regulation is loaded too — named by number or by
  title next to a fee word (Geneva LC 21 318, Bern Gebührenreglement), a tariff document on the same topic (Lausanne
  830.7), or the law next to a chosen ordinance (Basel 365.100); if no picked provision holds an amount, the
  provisions that do are added first.
- Tariff tables are split at their numbered items ("4.9 Parkkartengebühren"); the 12,000-character cut that dropped
  the second half of long regulations (half of Bern's fee tariff) is gone.
- Federal: main act → fee ordinance by rule (SchKG→GebV SchKG, SVG/VRV→OBV, BüG→BüV, AIG→GebV-AIG, …) plus question
  words (Busse, poursuite, passeport, naturalisation); annex parts ranked by the question's words are offered to and,
  when needed, added after the article picker.
- Answers: a fees rule (amount first, with unit and categories; range or ceiling when that is all the source gives);
  a mechanical check sends back any CHF amount or percentage that appears in no source.
- Relevance filter sees where the amounts are and keeps communal provisions and annexes that carry them.
- New city reader: Lugano (122 regulations). Basel excludes Riehen/Bettingen acts.

Regression sample (20 questions of test100 with a known governing source): key source retrieved 19/20 before and
after; average time 115 s → 98 s.
