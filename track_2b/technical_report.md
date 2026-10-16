# Technical report — Alpenrecht AI

A deeper write-up than the README: what we built, how it works, and what the numbers say.
PDF version: [`RedPandas_Report.pdf`](RedPandas_Report.pdf) (source: [`tools/report.html`](tools/report.html)).

- **Track:** Track 2B — Alpenrecht AI: one legal question → every level of Swiss law
- **Event:** Online
- **Team:** RedPandas — Christopher Yazigi, Giovanni Yazbeck, Alfredo Pio Yazbeck
- **Demo:** [video (1:36)](https://youtu.be/cG-jVfxx4d8) · run locally with `make run` (http://localhost:5055) · screenshots in [`docs/`](docs)

## 1. Summary

In Switzerland the answer to "Must my dog be on a leash?" or "When does night-time quiet start?" depends on where you
live. The rule can sit in federal law, in one of 26 cantonal legal systems or in the regulation of one of more than
2,000 communes, in four languages and on different websites. Alpenrecht AI takes a question and a place and returns
one answer covering all three levels. It retrieves the federal (Fedlex), cantonal (LexFind) and communal (the
commune's own website) rules live and adds leading court decisions (entscheidsuche.ch). Apertus-v1.5-70B then writes
an answer per level, with every claim cited to the official text and fact-checked three times before display. It
answers in DE / FR / IT / RM / EN and as of any date for federal law.

On 100 held-out questions (49 communal), graded blind by AI agents (Claude) against reference answers, the evaluated
version scores 1.39/3 against 1.38/3 for the original prototype, a tie within grading noise. Both give 46/100 usable
answers. The evaluated version makes fewer factual errors (43 vs 53) and is preferred head-to-head 43–36, but cites
the governing source less often (53 vs 58), and communal questions remain the hardest (0.90/3). This set also guided
the last day's choice between versions, so it is not fully independent (§5 d). On the 100-question development
benchmark used for tuning, 85/100 answers cite a gold source (67 at baseline), and cantonal retrieval rises from 11/32
to 29/32.

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

Screenshots: [start page](docs/screenshot_home.png) · [answer for Chur](docs/screenshot_answer.png) ·
[answer with the 3× check badge and sources](docs/screenshot_answer_checked.png).

### Target architecture (mandatory)

**(a) On-premise, or (c) sovereign Swiss cloud.** The app is one Docker container (Flask, Python 3.13). It talks to
any OpenAI-compatible Apertus endpoint set by `LLM_BASE_URL`:
- **On-premise:** a canton's or commune's own vLLM server.
- **Swiss cloud:** the CSCS inference service in Lugano, under Swiss jurisdiction and with Swiss data residency.

Full questions and answers go only to that endpoint. The public sources receive the place and search terms derived
from the question, never the full question. Questions are not logged: the server's access log records only request
paths and place look-ups.

Alpenrecht is **not air-gapped**: it reads public legal sources live.
- **Build time:** PyPI packages only (`requirements.txt`, `python:3.13-slim`).
- **Runtime:**
  - the Apertus endpoint;
  - Fedlex, LexFind, swisstopo, Wikidata (only for communes missing from `data/communes.json`), commune websites and
    TLex, and entscheidsuche.ch;
  - in the browser: swisstopo map tiles, Leaflet (cdnjs.cloudflare.com) and Google Fonts; Leaflet and the fonts can be
    self-hosted for an on-premise install.

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
  any vLLM serving Apertus. OCR uses `OCR_MODEL` (default `swiss-ai/Apertus-v1.5-8B`) on the same endpoint; on a
  single-model server, set `OCR_MODEL` to the same value as `LLM_NAME` in `.env`.
- **Prompts** are in `src/alpenrecht/pipeline.py`, `lexfind_agent.py`, `communal.py`, `caselaw.py` and `verify.py`.
  Answers run at temperature 0.2, planning and checks at 0.
- **Other models (evaluation only):**
  - AI agents (Claude, Anthropic) drafted the 100 held-out questions and their reference answers from the official
    sources, and a second Claude agent re-checked each item. Claude agents also graded the answers in §5 (b) and (d).
  - Claude is not open-weights. It was used offline only: it is not part of the product, never sees user questions
    and is not needed for `make run`.

## 4. Data

- **Live public sources only:** Fedlex (SPARQL + HTML), LexFind (all 26 cantons), swisstopo (geocoding), the
  communes' own websites and TLex collections, and entscheidsuche.ch. These are official public legal texts.
- **`data/communes.json`:** commune → official website for 2,142 communes, built once from Wikidata (CC0), 80 KB.
- **`data/wikidata_raw.json`:** the raw Wikidata SPARQL export (BFS number → official website, CC0, 400 KB) from which
  `communes.json` was built; kept for provenance, not read at runtime.
- **Evaluation sets in `eval/`:**
  - 14 questions (first rounds);
  - 100 questions with gold sources (68 federal, 32 cantonal). Federal gold articles were checked programmatically to
    exist on Fedlex; cantonal gold acts were chosen automatically from LexFind title matches;
  - 100 graded test questions;
  - 21 communal questions, three sets of 10 random communes, and 18 fee questions;
  - 100 held-out questions with reference answers (`questions_heldout100.json`, `heldout100_reference.json`), with
    both runs' answers, the blind key and the per-question grades in `eval/heldout/`.
- **No personal data:** questions are not stored, the crawl and law-text cache is emptied after each question, and
  uploaded regulations stay local. There are no human subjects.

## 5. Evaluation

**(a) Gold-source benchmark** (100 development questions, live retrieval, `eval/BENCHMARK100.md`):

| Setup | Answer cites a gold source | Cantonal gold act retrieved | Answers naming an article that is not a source |
|---|---|---|---|
| Baseline (keyword LexFind, single pass) | 67/100 | 11/32 | 13/100 |
| Ours (Apertus LexFind agent + 3× verification) | 85/100 | 29/32 | 0/100 |

The last column checks article numbers only, not which law they belong to.

**(b) Graded 0–3 by an AI grading agent (Claude) with a lawyer's rubric** (development questions, real pipeline, 70B,
three verification rounds):

| Run | Questions | Average /3 | Fully correct |
|---|---|---|---|
| v1 | 100 | 1.55 | 12 |
| v2 (federal article picking, planner examples, no-invented-figures rules, city readers) | 100 | 1.72 | 21 |

**(c) Communal law and figures:**
- 19/21 communal questions (8 communes) find and cite the commune's own regulation.
- Random communes (`eval/random10*.json`, results in `eval/results/random10*.json`): 2/10 cite the commune's
  regulation on a first random set before the crawler fixes. The fixes were tuned on a second set (5/10 → 6/10). On a
  fresh third set, 6/10 cite a communal regulation, 4 of them the correct, readable one.
- Fee questions state an amount from a source in 17/18 cases in the full run and 18/18 after a targeted re-run of
  the one miss (6/18 before), see `eval/FEES.md`.

**(d) Held-out check** (`eval/ACCURACY_heldout100.txt`, per-question data in `eval/heldout/`):
- 100 new questions, separate from the development sets: 49 communal, 12 cantonal and 39 federal; DE 46 / FR 34 /
  IT 12 / EN 8.
- AI agents (Claude) drafted the questions and reference answers from the official sources, and a second Claude agent
  re-checked each item (15 corrected, 0 dropped). They were not written by people or checked by a lawyer.
- Both versions answered the same questions. Claude agents graded them single-pass, blind and in pairs against the
  reference answers (0–3).
- The evaluated version is commit `c0c4e48` (the same pipeline code as `fdb96d8`, after the move into `track_2b/`).
  The later commits `9eb4d52` and `3bef387` (fee tariff companions, tariff-item splitting, fee ordinances, CHF amount
  check, Lugano reader, conversation memory, cache clearing) were not measured on this set; the fee changes were
  measured only on the 18 fee questions and a 20-question regression sample (`eval/FEES.md`).

| Setup | Average /3 | Usable (≥ 2) | Fully correct | Factual error | Governing source cited | Off-topic padding |
|---|---|---|---|---|---|---|
| Baseline (original prototype) | 1.38 | 46 | 19 | 53 | 58 | 36 |
| Ours (evaluated version, `c0c4e48`) | 1.39 | 46 | 21 | 43 | 53 | 22 |

On these questions:
- Head-to-head preference: 43 for ours, 36 for the original, 21 ties.
- Fewer factual errors (43 vs 53) and much less padding (22 vs 36).
- **Not** more often usable (46 vs 46), about as often fully right (21 vs 19), and the governing source is cited
  less often (53 vs 58).
- By level (original → evaluated): federal 1.92 → 1.95, cantonal 1.92 → 1.58 (12 questions only), communal
  0.82 → 0.90.

**Not fully independent.** On the last day, earlier candidate versions were also run and graded on this set. In that
grading pass one candidate scored 1.33/3 against 1.51/3 for the original, and the revert to the original source filter
and federal article choice (`c0c4e48`) was decided from those grades; an earlier change (`9bfe4d7`) was decided from a
partial grading of 66 of these questions. The same original answers scored 1.51/3 in that earlier pass and 1.38/3 in
the final one, so single-pass AI grading varies by about ±0.1/3 on this set.

The development figures in (a)–(c) were measured on questions used during tuning and overstate accuracy on new
questions. All grading was automatic and single-pass, not done by lawyers.

## 6. Limitations

- **Accuracy:** about half of the answers to new questions are usable, and about 4 in 10 contain a factual error.
  Most errors come from fetching a neighbouring article, or from misreading a figure in a correctly retrieved one.
  This is legal information, not legal advice.
- **Communal coverage** depends on each commune's website. JavaScript apps, bot blocking, or the lack of a linked
  regulations page defeat the crawler, and the app then asks for an upload.
- **Answer time:** about 100 s on average, because of the three verification rounds. On the held-out set the
  evaluated version took 99 s on average (median 96 s, 80% between 61 and 142 s, maximum 208 s; 15 answers in
  parallel on a shared endpoint), against 140 s for the original prototype; the v2 development run averaged 121 s.
  The UI streams every step meanwhile.
- **Scope:**
  - Cantonal law is the current version only.
  - Case law covers published BGE with an official headnote only.
  - Article splitting of cantonal PDFs is heuristic.
- **Not tested:** human grading on the held-out set, the later commits (`9eb4d52`, `3bef387`) on the held-out set,
  and air-gapped operation.

## 7. Reproducibility

- **Hardware and runtime:** any x86-64 machine with Docker; no GPU, because inference runs on the hosted CSCS Apertus
  endpoint (or your own vLLM). The image is `python:3.13-slim`.
- `make run`: Docker starts the web app on http://localhost:5055. It needs `LLM_API_KEY`; `LLM_BASE_URL` and
  `LLM_NAME` are optional.
- `make test`: offline tests (no network, no API).
- `make ask Q="…" PLACE="…"`: one answer in the terminal.
- `make eval SET=eval/questions_heldout100.json`: re-runs a question set live through the real pipeline and writes
  `eval/runs/questions_heldout100.jsonl` (one file per set).
- Held-out scores, offline from the stored blind grades (Python 3, standard library only):
  `cd eval/heldout && python score.py grades_blind.json blind_key.json original evaluated ../questions_heldout100.json`
  prints the figures of `eval/ACCURACY_heldout100.txt`. `make_packets.py` shows how the blind A/B pairs were built;
  details in [`eval/heldout/README.md`](eval/heldout/README.md).
- **Seeds:** none. Answers are sampled at temperature 0.2, planning and checks at 0. Retrieval is live and Apertus is
  not perfectly deterministic, so a re-run can differ slightly.
- **Commit:** the held-out numbers (§5 d) were measured at `c0c4e48`; to re-run that version in this layout, use
  `fdb96d8` (the same pipeline code). The later commits `9eb4d52` and `3bef387` were not measured on the held-out set.
- Stored runs keep their answers, sources and verification logs in `eval/results/` (development) and `eval/heldout/`
  (held-out answers, blind key and per-question grades).

## 8. Next steps

- **Faster answers:** fact-checking with the 8B model and streaming the final answer.
- **Point-in-time cantonal law** from LexFind's version history.
- **More city platforms** and cantonal court decisions next to the statutes.
- **An on-premise pilot with a canton or commune** for its citizen help desk, with its own regulations loaded.

## License

Following the Hack Apertus Terms & Conditions, §6:
- **Code:** Apache-2.0 ([`LICENSE`](../LICENSE)).
- **Documentation** (this report, the READMEs, `docs/`): Creative Commons Attribution 4.0 (CC-BY-4.0).
- **Datasets** (evaluation sets, reference answers and grades in `eval/`, and `data/`): CDLA-Permissive-2.0.
  `data/communes.json` is derived from Wikidata (CC0); `data/wikidata_raw.json` is the raw Wikidata export, kept for
  provenance.
- The law texts the app retrieves are official enactments and decisions, which Swiss copyright law does not protect
  (Art. 5 para. 1 URG).

## References

1. Fedlex, publication platform for federal law: https://www.fedlex.admin.ch
2. LexFind, cantonal law collections: https://www.lexfind.ch
3. swisstopo geocoding API: https://api3.geo.admin.ch
4. entscheidsuche.ch, Swiss court decisions: https://entscheidsuche.ch
5. Swiss AI Initiative, Apertus: https://huggingface.co/swiss-ai
