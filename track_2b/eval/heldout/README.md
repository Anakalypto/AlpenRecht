# Held-out evaluation (100 questions)

Evidence behind `../ACCURACY_heldout100.txt`: two versions of the pipeline answered the same 100 questions, and
Claude agents graded both answers to each question blind, side by side, against a reference answer.

## Files

| file | what it is |
|---|---|
| `../questions_heldout100.json` | the 100 questions (H001–H100): 49 communal, 12 cantonal, 39 federal; DE 46 / FR 34 / IT 12 / EN 8 |
| `../heldout100_reference.json` | per question: reference answer, key facts, common errors, governing sources with quotes and links |
| `answers_original.jsonl` | answers of the **original** version (commit eabfc3b, the first flat-layout checkout), one JSON line per question, written by `../accuracy_run.py`: plan, steps, sources with excerpts, answer, verification log, seconds |
| `answers_evaluated.jsonl` | answers of the **evaluated** version (commit c0c4e48, same pipeline code as fdb96d8 after the move into `track_2b/`), same format; a copy of the local runner output `eval/runs/ho-v5-all.jsonl` |
| `make_packets.py` | builds one blind grading packet per question: question, reference, then Answer A and Answer B with their sources; A/B order is set per question by a hash of the id |
| `blind_key.json` | per question, which of A and B is the original (`x`) and which the evaluated (`y`) run; graders never saw it |
| `grades_blind.json` | the graders' output on the blind packets: per answer a 0–3 score, `factual_error`, `errors`, `missing`, `governing_source_cited`, `padding`; per question which answer was `better` |
| `score.py` | un-blinds the grades with the key and prints the summary |
| `grades_unblinded.json` | per-question grades after un-blinding (`score.py --write` output); the evaluated version is labelled `current` here |

The raw runner output on these questions (`eval/runs/ho-*`: `ho-base*` the original version, `ho-v5*` the
evaluated one, the rest earlier candidate versions, see "Independence and limits" below) stays local:
`eval/runs/` is not committed. The two answer files above are the runs that were graded.

## How the questions, references and grades were made

- **Questions and reference answers** were drafted by AI agents (Claude, Anthropic) researching the official sources
  (Fedlex, cantonal law collections, communal regulations). A second Claude agent re-checked every item: 15 were
  corrected, none dropped. They were not written by humans and not checked by a lawyer.
- **Grading** was done by Claude agents in a single pass, blind and pairwise: each packet showed the reference and the
  two answers as A and B, without saying which version wrote which. Each answer got a 0–3 score (3 correct and
  concrete, 2 mostly right, 1 partly right with an important error or the wrong rule, 0 wrong or empty) plus the
  flags above. Grading was against the reference answers; in this pass the graders did not check claims online
  (`verified_online` is false for all 100). No human reviewed the grades.

## Result

| | original | evaluated |
|---|---|---|
| mean score | 1.38/3 | 1.39/3 |
| usable (score ≥ 2) | 46 | 46 |
| fully correct (score 3) | 19 | 21 |
| factual error flagged | 53 | 43 |
| governing source cited | 58 | 53 |
| off-topic padding flagged | 36 | 22 |
| judged the better answer | 36 | 43 (21 ties) |
| federal / cantonal / communal mean | 1.92 / 1.92 / 0.82 | 1.95 / 1.58 / 0.90 |

The cantonal level has only 12 questions.

Latency (stored seconds per answer, 15 answers in parallel on a shared endpoint): evaluated version mean 99 s,
median 96 s, 10–90% 61–142 s, max 208 s; original version mean 140 s.

## Reproduce

From `track_2b/eval/heldout`:

```bash
python score.py grades_blind.json blind_key.json original evaluated ../questions_heldout100.json
```

This prints `../ACCURACY_heldout100.txt` word for word.

To rebuild the blind packets (the `_key.json` written to the output folder equals `blind_key.json`):

```bash
python make_packets.py ../questions_heldout100.json answers_original.jsonl answers_evaluated.jsonl <out_dir> ../heldout100_reference.json
```

Re-running the answers needs an API key in `.env` and a live endpoint, and gives different answers each time.
From `track_2b/`: `python eval/accuracy_run.py --set eval/questions_heldout100.json --out eval/runs/<name>.jsonl`;
for the original version, add `--root <checkout of eabfc3b>`.

## Independence and limits

- **Not fully independent.** On the last day, earlier candidate versions were run and graded on this held-out set.
  One candidate scored 1.33 against 1.51 for the original in that grading pass, and the revert to the original
  source filter and federal article choice (c0c4e48) was decided from those grades.
- **Grading noise.** The same original answers scored 1.51 in that earlier pass and 1.38 in this final pass, so
  single-pass AI grading noise is about ±0.1/3 on this set. The 1.38 vs 1.39 difference is within that noise.
- **Not measured here.** Later commits 9eb4d52 (fee tariff companions, tariff-item splitting, fee ordinances, CHF
  amount check, Lugano reader) and 3bef387 (conversation memory, cache clearing) were not run on this set. The fee
  changes were measured only on the 18 fee questions and a 20-question regression sample (`../FEES.md`).
- References and grades are AI-made; neither was checked by a lawyer.
