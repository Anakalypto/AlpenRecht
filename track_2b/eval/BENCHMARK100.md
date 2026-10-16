# Alpenrecht AI: 100-question benchmark

100 everyday legal questions: 68 federal and 32 cantonal, in DE 46 / FR 30 / IT 15 / EN 9, asked from 15 cantons.
Every gold source was verified live before the run:
- **Federal:** each gold article was fetched from Fedlex and its heading checked against the question,
  e.g. OR 257e "Sicherheiten durch den Mieter", StGB 179quater, SVG 91a, BV 136.
- **Cantonal:** each question is pinned to the canton's main act on LexFind (dog, tax, building and school laws).

Model: `swiss-ai/Apertus-v1.5-70B` on the Hack Apertus CSCS endpoint. Retrieval is live (Fedlex, LexFind, swisstopo).

```bash
.venv/Scripts/python.exe bench/build_set100.py        # rebuild + re-verify the gold set
.venv/Scripts/python.exe bench/bench.py --set questions100.json --tag s100-final --workers 5
```

## Result

| | Baseline | **Final** |
|---|---|---|
| | keyword LexFind, single pass | Apertus LexFind agent + 3× verification |
| **Answer cites a gold source** | 67/100 | **85/100** |
| · federal questions | 56/68 | 57/68 |
| · cantonal questions | 11/32 | **28/32** |
| Cantonal gold act retrieved | 11/32 | **29/32** |
| Federal act / gold article retrieved | 61/68 · 56/68 | 63/68 · 57/68 |
| Answers naming an article that is not a source | 13/100 | **0/100** |
| Invalid citations [n] | 0 | 0 |
| Prose citations left unconverted | 18 | **0** |
| Right language · all headings · disclaimer | 99 · 99 · 99 | 99 · 99 · 99 |
| Avg words | 212 | 223 |
| Total time per answer (avg · median · p90) | 15 s | 51 s · 47 s · 70 s |
| Errors | 0 | 0 |

The verification loop checked about 10 claims per answer. It revised 1.5 times per answer on average and added
0.4 real sources per answer: articles the draft named, or the verifier asked for, are fetched and added only if
they exist. 2 questions answered correctly in the baseline lost their gold citation in the final run
(F03 subletting, F45 marriage). Both come from federal article selection, which varies between runs.

## What changed between the two runs

1. **Apertus-powered LexFind** (`lexfind_agent.py`)
   - **Query writing:** Apertus names the canton's likely acts ("Planungs- und Baugesetz", "Loi sur les
     constructions…", "Legge tributaria") and wildcard title stems. This runs in parallel with federal retrieval.
   - **Act selection:** Apertus picks the 3 most relevant acts from up to 25 LexFind candidates.
   - **Article selection:** Apertus reads the article headings of those acts and picks the provisions that answer.
   - **Fallbacks:** each step falls back to keywords. LexFind matches whole words, so the keyword search now uses
     wildcard stems ("\*steue\*" finds "Steuergesetz"), and main acts rank above directives and agreements.
   - **Speed:** the extracted text of large cantonal PDFs is cached, so a cantonal step drops from ~13 s to ~3 s.
2. **Three verification rounds before the user sees anything** (`verify.py`), each round:
   - deterministic checks: every [n] exists, every named article is a source, no prose citations;
   - source enrichment: articles the answer names, or the verifier requests, are fetched from Fedlex or LexFind;
   - an Apertus fact-check that lists every claim with a supported / unsupported verdict;
   - a revision only when the round found something.
   - The UI shows the rounds live and a "✓ 3× geprüft · N Aussagen · corrections · sources added" badge.

## Remaining misses (15)

- **Federal article selection (11):** the planner names the right act but the wrong article, e.g. termination
  articles instead of OR 262 (subletting), 264 (early return) or 335c (employment notice), or ZGB 96–99 instead
  of 94. Or it names the wrong act: DSG instead of OR 328b, the Federal Constitution instead of ZGB 14, the
  Civil Code instead of StGB 144, SVG instead of VRV 4a. **Next step:** apply the LexFind-style
  "Apertus reads headings and picks articles" step to Fedlex too.
- **Cantonal (4):** BE capital gains and TI deductions, where the federal search drifted into a double-tax
  treaty and the federal income-tax act; LU tax return deadline, where the act was found but not the right
  article; GE compulsory education, where the planner chose another act.

## Trade-off

Verification triples latency (15 s → ~50 s). The answer appears all at once after the checks, while the UI
shows each step live. For a faster demo, set `VERIFY_MODEL=swiss-ai/Apertus-v1.5-8B` in `.env` to fact-check
with the 8B model, or lower `VERIFY_ROUNDS` in `pipeline.py`.

All 100 answers, with their sources and verification logs, are in `bench/results/Apertus-v1.5-70B-s100-final.json`.
The baseline answers are in `…-s100-a.json`.
