# Technical report — Alpenrecht AI

A deeper write-up than the README: what we built, how it works, and what the numbers say.
PDF version: [`RedPandas_Report.pdf`](RedPandas_Report.pdf) (source: [`tools/report.html`](tools/report.html)).

- **Track:** Track 2B — Alpenrecht AI: one legal question → every level of Swiss law
- **Event:** Online
- **Team:** RedPandas — Christopher Yazigi, Giovanni Yazbeck, Alfredo Pio Yazbeck
- **Demo:** `link to video` · run locally with `make run` (http://localhost:5055) · screenshots in [`docs/`](docs)

## 1. Summary

In Switzerland the answer to "Must my dog be on a leash?" or "When does night-time quiet start?" depends on where you
live. The rule can sit in federal law, in one of 26 cantonal legal systems or in the regulation of one of more than
2,000 communes, in four languages and on different websites. Alpenrecht AI takes a question and a place and returns
one answer covering all three levels. It retrieves the federal (Fedlex), cantonal (LexFind) and communal (the
commune's own website) rules live and adds leading court decisions (entscheidsuche.ch). Apertus-v1.5-70B then writes
an answer per level, with every claim cited to the official text and fact-checked three times before display. It
answers in DE / FR / IT / RM / EN and as of any date for federal law.

On a 100-question development benchmark, 85/100 answers cite a gold source (67 at baseline). Cantonal retrieval rises
from 11/32 to 29/32. On 100 new held-out questions (49 communal), the submitted version is preferred head-to-head
43–36 and makes fewer factual errors (43 vs 53). It has the same share of usable answers, 46/100, and communal
questions remain the hardest.

## 2. Architecture

```
question + place + date (+ the last 6 chat messages)
   │
   ├─ swisstopo ─────────── address → commune, BFS no., canton, official languages
   ├─ Apertus (planner) ─── standalone question, levels, SR numbers + articles, title / keyword terms per language
   ├─ Fedlex SPARQL ─────── acts in force → consolidation valid on <date> → articles + annexes (tariffs)
   ├─ LexFind API ───────── Apertus writes the queries, picks the acts, then the articles (26 cantons, one API)
   ├─ communal docs ─────── commune website crawl (2,142 communes) · TLex · readers for 6 large cities · uploads
   ├─ case law ──────────── entscheidsuche.ch: Apertus writes the queries, ≤ 2 leading cases (BGE) with headnotes
   ├─ ranking + filter ──── stemmed BM25 over articles, annexes and tariff tables; Apertus relevance filter
   └─ Apertus (answer) ──── per level, every claim cited [n] ──► 3 verification rounds ──► answer + sources (SSE)
```

- **Apertus steers, code looks up.** Apertus names the likely acts and articles, and the code fetches exactly those
  from the official source, so an invented article number simply finds nothing.
- **Three verification rounds** (`verify.py`, `checks.py`). Each round runs deterministic checks: every `[n]` exists,
  every named article is a source, there are no prose citations, and every CHF amount appears in a source. It then
  fetches the articles the draft names or the verifier asks for. Apertus fact-checks every claim, and the answer is
  rewritten only when the round found something.
- **Communal law without a central collection** (`communal.py`, `cities.py`). The BFS number leads to the commune's
  official website (Wikidata table), then to its regulations page (navigation, sitemap, CMS paths, embedded JSON,
  TLex). Apertus then picks the regulation and the articles. Readers cover Zürich, Geneva, Basel, Lausanne, Bern and
  Lugano. Scanned PDFs are transcribed by Apertus itself (image input, 8B).
- **Figures.** Annexes and tariff tables ("Anhang", "Annexe", "Tarif") are indexed as sources. For fee questions, the
  tariff belonging to the chosen regulation or act is loaded too.
- **App.** Flask streams server-sent events to a single-page UI in five languages. Hovering a citation shows the
  supporting sentence of the article. A CLI (`python -m alpenrecht ask`) answers in the terminal.

### Target architecture (mandatory)

**(a) On-premise, or (c) sovereign Swiss cloud.** The app is one Docker container (Flask, Python 3.13). It talks to
any OpenAI-compatible Apertus endpoint set by `LLM_BASE_URL`:
- **On-premise:** a canton's or commune's own vLLM server.
- **Swiss cloud:** the CSCS inference service in Lugano, under Swiss jurisdiction and with Swiss data residency.

Questions and answers stay between the container and that endpoint, and nothing is logged.

Alpenrecht is **not air-gapped**: it reads public legal sources live.
- **Build time:** PyPI packages only (`requirements.txt`, `python:3.13-slim`).
- **Runtime:**
  - the Apertus endpoint;
  - Fedlex, LexFind, swisstopo, commune websites and entscheidsuche.ch;
  - in the browser: map tiles, Leaflet and fonts.

An air-gapped deployment would need a local mirror of those sources.

## 3. Use of Apertus

- **Models:**
  - `swiss-ai/Apertus-v1.5-70B` for planning, retrieval steering, answers and fact-checks.
  - `swiss-ai/Apertus-v1.5-8B` for reading scanned pages (OCR via image input).
- **How it is used:** inference with agents / tool use (Apertus drives the retrieval steps). This is prompting only:
  JSON where structure is needed, a tolerant parser, and retries on transient API errors.
  1. **Planner:** language, a clarified standalone question, levels, SR numbers and articles, search terms.
  2. **LexFind agent:** act titles and wildcard stems, the act choice, and the article choice from headings. The same
     heading-based choice is used for Fedlex.
  3. **Communal:** the regulation and article choice, and OCR of scanned or garbled PDFs.
  4. **Case law:** the search queries and the choice of at most two leading decisions.
  5. **Answer:** the relevance filter, then the answer writer (strict citation style, one section per level).
  6. **Fact-checker:** a verdict on every claim, the missing sources, then a rewrite.
- **Where it runs:** the hosted CSCS OpenAI-compatible endpoint (`LLM_NAME` / `LLM_BASE_URL` / `LLM_API_KEY`), or
  any vLLM serving Apertus.
- **Prompts** are in `src/alpenrecht/pipeline.py`, `lexfind_agent.py`, `communal.py`, `caselaw.py` and `verify.py`.
  Answers run at temperature 0.2, planning and checks at 0.
- **Other models (evaluation only):**
  - Answer grading in §5 (b) and (d), and the drafting and checking of the held-out reference answers, were done by
    automatic grading agents (Claude, Anthropic). They checked against the official law text.
  - They are not part of the product and never see user questions.

## 4. Data

- **Live public sources only:** Fedlex (SPARQL + HTML), LexFind (all 26 cantons), swisstopo (geocoding), the
  communes' own websites and TLex collections, and entscheidsuche.ch. These are official public legal texts.
- **`data/communes.json`:** commune → official website for 2,142 communes, built once from Wikidata (CC0), 80 KB.
- **Evaluation sets in `eval/`:**
  - 14 questions (first rounds);
  - 100 questions with gold sources (68 federal, 32 cantonal);
  - 100 graded test questions;
  - 21 communal questions, random-commune sets and 18 fee questions;
  - 100 held-out questions with reference answers (`questions_heldout100.json`, `heldout100_reference.json`).
- **No personal data:** questions are not logged, the crawl and law-text cache is emptied after each question, and
  uploaded regulations stay local. There are no human subjects.

## 5. Evaluation

**(a) Gold-source benchmark** (100 development questions, live retrieval, `eval/BENCHMARK100.md`):

| Setup | Answer cites a gold source | Cantonal gold act retrieved | Answers naming an article that is not a source |
|---|---|---|---|
| Baseline (keyword LexFind, single pass) | 67/100 | 11/32 | 13/100 |
| Ours (Apertus LexFind agent + 3× verification) | 85/100 | 29/32 | 0/100 |

**(b) Graded 0–3 like a lawyer** (real pipeline, 70B, three verification rounds):

| Run | Questions | Average /3 | Fully correct |
|---|---|---|---|
| v1 | 100 | 1.55 | 12 |
| v2 (federal article picking, planner examples, no-invented-figures rules, city readers) | 100 | 1.72 | 21 |

**(c) Communal law and figures:**
- 19/21 communal questions find and cite the commune's own regulation.
- Random communes improved from 2/10 to 6/10.
- Fee questions state an amount from a source in 18/18 cases (6/18 before), see `eval/FEES.md`.

**(d) Independent held-out check** (`eval/ACCURACY_heldout100.txt`):
- 100 new questions, written after development, each with a reference answer checked against the official text.
- 49 communal, 12 cantonal and 39 federal questions, in DE/FR/IT/EN.
- Both versions answered the same questions and were graded blind and in pairs.

| Setup | Average /3 | Usable (≥ 2) | Fully correct | Factual error | Off-topic padding |
|---|---|---|---|---|---|
| Baseline (original prototype) | 1.38 | 46 | 19 | 53 | 36 |
| Ours (submitted version) | 1.39 | 46 | 21 | 43 | 22 |

On unseen questions:
- Head-to-head preference: 43 for ours, 36 for the original, 21 ties.
- Fewer factual errors (43 vs 53) and much less padding.
- **Not** more often fully right.
- By level: federal 1.95, cantonal 1.58, communal 0.90.

The development figures in (a)–(c) were measured on questions used during tuning and overstate accuracy on new
questions. The grading was automatic and single-pass, not done by lawyers.

## 6. Limitations

- **Accuracy:** about half of the answers to new questions are usable, and about 4 in 10 contain a factual error.
  Most errors come from fetching a neighbouring article, or from misreading a figure in a correctly retrieved one.
  This is legal information, not legal advice.
- **Communal coverage** depends on each commune's website. JavaScript apps, bot blocking, or the lack of a linked
  regulations page defeat the crawler, and the app then asks for an upload.
- **Answer time:** roughly 50–120 s, because of the three verification rounds. The UI streams every step meanwhile.
- **Scope:**
  - Cantonal law is the current version only.
  - Case law covers published BGE with an official headnote only.
  - Article splitting of cantonal PDFs is heuristic.
- **Not tested:** human grading on the held-out set, and air-gapped operation.

## 7. Reproducibility

- `make run`: Docker (`python:3.13-slim`) starts the web app on http://localhost:5055. It needs `LLM_API_KEY`;
  `LLM_BASE_URL` and `LLM_NAME` are optional.
- `make test`: offline tests (no network, no API).
- `make ask Q="…" PLACE="…"`: one answer in the terminal.
- `make eval SET=eval/questions_heldout100.json`: re-runs a question set live through the real pipeline.
- Retrieval is live and Apertus is not perfectly deterministic, so a re-run can differ slightly. Stored runs keep
  their answers, sources and verification logs in `eval/`.
