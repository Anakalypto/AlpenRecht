# Alpenrecht AI benchmark

14 everyday legal questions in DE/FR/IT/EN, asked from 9 cantons (ZH, BE, VD, GE, TI, BS, NE, SG, FR).
Each question has gold sources checked on Fedlex or LexFind: federal articles (OR 266c/257d/321c/329a/335b/336c,
LAT 18a / OAT 32a, DSG 25, ZGB 471, SVG 91) and cantonal acts (dog laws of BE, ZH, GE, TI, plus Vaud's RLATC).
Everything runs live against Fedlex, LexFind and swisstopo, with Apertus on the Hack Apertus CSCS endpoint.

```bash
# from track_2b/
python eval/bench.py --model swiss-ai/Apertus-v1.5-70B --tag v5
```

## Result (final round, v5)

| | Apertus v1.5 70B | Apertus v1.5 8B |
|---|---|---|
| **answer cites a gold source** | **13/14** | **13/14** |
| federal act / gold article retrieved | 10/10 · 9/10 | 10/10 · 9/10 |
| cantonal gold act retrieved | 5/5 | 4/5 |
| answers with an invalid citation [n] | 0/14 | 0/14 |
| answers naming an article not in the sources (flagged in UI) | 2/14 | 4/14 |
| right language / all headings / disclaimer | 14/14 · 14/14 · 14/14 | 14/14 · 14/14 · 14/14 |
| avg length (target < 230 words) | 239 | 204 |
| avg time to first token · total | 7.8 s · 14.8 s | 6.9 s · 9.6 s |

## How we got there

| model · round | planner ok | fed act | fed gold art. | cant. gold | **gold cited** | invalid [n] | unsupported art. | right lang. | disclaimer | words | TTFT s | total s |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| v1.5-70B · v1 | 14/14 | 5/10 | 3/10 | 4/5 | 6/14 | 0/14 | 5/14 | 13/14 | 9/14 | 221.8 | 6.6 | 13.3 |
| v1.5-70B · v2 | 9/14 | 8/10 | 6/10 | 3/5 | 9/14 | 4/14 | 1/14 | 13/14 | 8/14 | 200.6 | 10.3 | 16.6 |
| v1.5-70B · v3 | 14/14 | 9/10 | 7/10 | 5/5 | 12/14 | 2/14 | 2/14 | 13/14 | 13/14 | 240.1 | 7.1 | 14.4 |
| v1.5-70B · v4 | 14/14 | 10/10 | 9/10 | 5/5 | 13/14 | 3/14 | 2/14 | 13/14 | 13/14 | 238.1 | 6.8 | 13.7 |
| v1.5-70B · v5 | 14/14 | 10/10 | 9/10 | 5/5 | 13/14 | 0/14 | 2/14 | 14/14 | 14/14 | 239.1 | 7.8 | 14.8 |
| v1.5-8B · v1 | 14/14 | 6/10 | 3/10 | 5/5 | 7/14 | 2/14 | 8/14 | 13/14 | 11/14 | 211.7 | 4.3 | 7.0 |
| v1.5-8B · v5 | 14/14 | 10/10 | 9/10 | 4/5 | 13/14 | 0/14 | 4/14 | 14/14 | 14/14 | 204.2 | 6.9 | 9.6 |

What each round changed:

- **v1 → v2**: the planner now returns `federal_refs: [{sr, articles}]` and those articles are looked up exactly.
  In v1 it put article numbers in the SR field (e.g. "321c"), so the Code of Obligations was never loaded.
  An answer checker was added: it validates citations, flags article numbers the sources don't contain, and
  turns prose citations like "(Art. 7 Hundegesetz BE)" into clickable [n].
- **v2 → v3**: a fault-tolerant planner parser. 70B sometimes emits malformed JSON or runaway article lists,
  which caused 5 of the 14 fallbacks in v2. The prompt no longer contains article ranges ("319-362"), which
  had led the model to use "362" as an SR number. The disclaimer is now appended server-side if missing.
  French and Italian questions now feed their own words into the cantonal search.
- **v3 → v4**: fixed article-number parsing for acts whose articles carry a title in the number field
  ("Art. 25 Auskunftsrecht"), which broke exact lookup in the DSG and LAT. When the planner names no
  federal act, ZGB and OR are searched too: 70B believed the compulsory share is cantonal law.
- **v4 → v5**: the answer language is detected from the question's function words. The planner drifted
  towards the canton's language and answered an English question about Zürich in German. A stray "[49]"
  (Art. 49 BV precedence written as a citation) is removed.

## Remaining weaknesses

- **Unsupported article numbers** (70B 2/14, 8B 4/14): the model sometimes names a related article from memory,
  e.g. "art. 22" LAT next to the retrieved art. 18a. The UI flags these under the answer.
- **Length**: 70B averages about 240 words against the 230 target. The French rent and drink-driving answers run 350–370.
- **inheritance (70B)**: ZGB is now searched, but keyword ranking picks other ZGB articles than art. 471.
  70B also still says the topic is cantonal. 8B gets it right.
- **8B cantonal**: misses Vaud's building regulation for the solar question in some runs (title-term variance).
- **Sample size**: 14 questions, so one question is about 7 points. Runs vary because the planner's terms
  change between runs. Treat differences of 1–2 questions as noise.

## Recommendation

**70B for quality, 8B for demos.** Both reach 13/14 gold citations. 8B answers about 35% faster in total
(9.6 s vs 14.8 s) and is shorter, but names more unsupported articles (4/14 vs 2/14). The default stays 70B.
Set `LLM_NAME=swiss-ai/Apertus-v1.5-8B` in `.env` for a snappier live demo.

Raw per-question results of the final round, including the full answers and sources, are in
`eval/results/Apertus-v1.5-70B-v5.json` and `eval/results/Apertus-v1.5-8B-v5.json`. Earlier rounds are summarised
in the table above and in `eval/progression.md` (which also has the 8B v2–v4 rounds); their raw files are not kept.
