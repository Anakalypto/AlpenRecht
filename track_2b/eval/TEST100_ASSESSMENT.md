# Alpenrecht AI — 100-question assessment (2026-10-16)

100 questions (eval/questions_test100.json; batches eval/questions_test100_p{1..5}.json), 5 batches run in parallel
through the real pipeline (Apertus v1.5 70B, 3 verification rounds), each graded 0–3 by an AI reviewer agent
(Claude, Anthropic) acting as a Swiss lawyer; not reviewed by a human lawyer.
Per-question grades: eval/results/test100-p{1..5}-grades.md.

| batch | topic | avg /3 | 3 | 2 | 1 | 0 | factual errors | avg s |
|---|---|---|---|---|---|---|---|---|
| p1 | permits, naturalisation, traffic | 1.20 | 2 | 3 | 12 | 3 | 13/20 | 87.6 |
| p2 | tenancy, employment | 1.70 | 4 | 8 | 6 | 2 | 13/20 | 73.0 |
| p3 | social insurance, family, inheritance | 1.75 | 2 | 12 | 5 | 1 | 11/20 | 88.4 |
| p4 | building, neighbours, communal | 1.50 | 2 | 8 | 8 | 2 | 11/20 | 84.9 |
| p5 | criminal, data, tax, consumer, short | 1.60 | 2 | 9 | 8 | 1 | 13/20 | 83.7 |
| **all** | | **1.55** | **12** | **40** | **39** | **9** | **61/100** | **83.5** |

Robustness: 0 errors / 0 timeouts in 100 runs; right language 99/100 (T025 answered in Romansh);
communal regulation retrieved 8/10, used well 5/10.

## Recurring failures (ordered by impact)
1. Governing article not retrieved (VZV 27, VRV 3b, BüG 9, AHVG 21, ZGB 264c/647c, DSG 19, StGB 31 …) — the model
   then paraphrases the nearest neighbour as if it were the rule.
2. Invented or wrong deadlines/figures, mostly in "Next steps" (10-year prescription instead of 3-month complaint
   deadline, per-mille vs percent, 10 vs 5 years for salary claims).
3. Off-topic acts in sources via loose word matching (guida → guida alpina, permis, treaties, LEFin, MPV).
4. Retrieved cantonal/communal provisions ignored ("no relevant source" while it is in the list).
5. No distinction by status (EU vs non-EU, tenant vs owner, private vs public body); ambiguous one-word questions
   answered without stating the assumption.
6. Fixed three-level template → Art. 49 BV boilerplate, empty sections, ~400 words, ~84 s.

## Verdict
Good engineering, not yet a reliable legal tool: sources are real and linked, it never crashes, and federal/
cantonal/communal retrieval works end-to-end — but only 12% of answers are fully right and 61% contain a concrete
error a user could act on. Fine for a hackathon demo on well-chosen questions; not fit for unsupervised use.

---

# Re-run after fixes (v2, same 100 questions, same rubric)

Fixes: Apertus picks federal articles from candidates (incl. the planner's named ones and their neighbours), planner
examples for driving / social insurance / family / criminal / data / tax, no-invented-figures rules in answer and
fact-check, off-topic sources removed from the visible list, unused cantonal/communal sources trigger a revision,
Italian no longer detected as Romansh, and readers for the Zürich, Geneva, Basel, Lausanne and Bern collections.
Grades: eval/results/test100v2-p{1..5}-grades.md.

| batch | v1 avg | v2 avg | v2 3/2/1/0 | factual errors v1 → v2 | avg s v1 → v2 |
|---|---|---|---|---|---|
| p1 permits, traffic | 1.20 | 1.35 | 3/6/6/5 | 13 → 12 | 87.6 → 129.7 |
| p2 tenancy, employment | 1.70 | 1.95 | 5/9/6/0 | ~12 → 7 | 73.0 → 110.7 |
| p3 social insurance, family | 1.75* | 1.70 | 3/10/5/2 | ~9 → 7 | 88.4 → 112.9 |
| p4 building, communal | 1.50 | 1.60 | 4/6/8/2 | ~11 → 10 | 84.9 → 117.4 |
| p5 criminal, data, tax, short | 1.60 | 2.00 | 6/8/6/0 | ~13 → 10 | 83.7 → 131.9 |
| **all** | **1.55** | **1.72** | **21/39/31/9** | **~58 → 46** | **83.5 → 120.5** |

*p3's grade file header says 1.85; its own table sums to 1.75.

Better: fully correct answers 12 → 21; factual errors ~58 → 46; key articles now found (OAC 27, LN 9, AHVG 21,
ZGB 264c, LPD 19, StGB 179bis/ter, OR 340, OR 266c/271a); treaty/noise acts gone from source lists; Bern readers
fixed both Bern communal questions; communal regulation found 9/10 (was 8/10), used well 6/10 (was 5/10).
Worse: latency +44% (more revisions under the stricter fact-check, plus 15 pipelines running at once); some
regressions from retrieval instability (RPG 18a, BauV AG § 49 lost between runs) and traffic-sanction tiers.

Fixed after this run, not yet measured: (1) communal articles leaking into unrelated answers (keyword fallback now
only for a regulation that matches the topic; communal sources go through the relevance filter again);
(2) the verifier's JSON example "SR 220 art. 266c" was being copied into answers → removed;
(3) bench.py summary crash on the Windows console.

Still open: EU/EFTA vs third-country split in migration answers (free-movement agreement rarely retrieved);
traffic-sanction tiers (LCR 16a-c, 90); fee questions without CHF figures (tariff annexes not indexed);
one-word questions don't state their assumption; wrong deadlines in "Next steps" (StGB 31, OR 201);
answers ~470 words / ~120 s.
