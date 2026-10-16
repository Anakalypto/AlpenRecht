# Alpenrecht AI

**One legal question → every level of Swiss law.** Federal (Bund), cantonal (Kanton) and communal (Gemeinde)
rules, retrieved live from official sources and explained with citations by **Apertus**, the Swiss open LLM.

## Run it (judges)

```bash
export LLM_API_KEY=...                                  # CSCS / Apertus key
export LLM_BASE_URL=https://api.inference.cscs.ch/v1    # default
export LLM_NAME=swiss-ai/Apertus-v1.5-70B               # default
make run          # web app on http://localhost:5055
make test         # offline tests (no API calls)
make ask Q="Ab wann gilt in Chur die Nachtruhe?" PLACE="7000 Chur"
```

Without Docker (Python 3.12+):

```bash
python -m venv .venv && .venv/Scripts/python.exe -m pip install -r requirements.txt   # .venv/bin/python on macOS/Linux
cp .env.example .env                                    # paste LLM_API_KEY (APERTUS_* names also work)
PYTHONPATH=src .venv/Scripts/python.exe -m alpenrecht serve
```

`swiss-ai/Apertus-v1.5-8B` is about 2× faster. `LLM_BASE_URL` / `LLM_NAME` can point at any OpenAI-compatible
Apertus endpoint, including a local vLLM. Without a key, retrieval still runs and the app shows the sources only.

| Setting (env or `.env`) | Default | Effect |
|---|---|---|
| `HISTORY_MESSAGES` | `6` | Conversation memory: the planner sees this many earlier messages of the chat, so a follow-up ("and in Geneva?") is searched as the full question. `0` turns it off. |
| `KEEP_CACHE` | off | `cache/` (downloaded law texts, crawls) is emptied whenever no question is running; uploads are kept. `1` keeps it between questions (faster repeats). |

## How it works

```
question + place + date
   │
   ├─ swisstopo ─────────── address → commune, BFS no., canton, official languages
   ├─ Apertus (planner) ─── which levels? SR numbers, title/keyword terms per language
   ├─ Fedlex SPARQL ─────── in-force acts → consolidation valid on <date> → per-article HTML
   ├─ LexFind API ───────── cantonal law of that canton (26 collections, one API) → articles
   ├─ communal docs ─────── commune website crawl + readers for the 5 largest cities, uploads (PDF / URL)
   ├─ case law ──────────── entscheidsuche.ch: Apertus writes the queries, picks ≤ 2 leading cases (BGE)
   ├─ ranking ───────────── stemmed BM25-ish over articles, annexes and tariff tables + section breadcrumbs
   └─ Apertus (answer) ──── per level, every claim cited [n] → official source; fact-checked before display
```

| Path | Role |
|---|---|
| `src/alpenrecht/pipeline.py` | plan → retrieve (4 levels) → draft → 3 fact-check rounds, as server-sent events |
| `src/alpenrecht/sources.py` | swisstopo, Fedlex (articles + annexes), LexFind clients, article/annex splitting, ranking, disk cache |
| `src/alpenrecht/lexfind_agent.py` | Apertus-driven LexFind queries, act and article picking (also federal article picking) |
| `src/alpenrecht/communal.py`, `cities.py` | commune website crawler, TLex, readers for Zürich, Geneva, Basel, Lausanne, Bern |
| `src/alpenrecht/caselaw.py` | entscheidsuche.ch: Apertus-written queries, ≤ 2 leading cases (BGE) |
| `src/alpenrecht/verify.py`, `checks.py` | relevance filter, fact-check and rewrite, citation checks |
| `src/alpenrecht/apertus.py`, `config.py` | OpenAI-compatible client with retries; settings (`LLM_*` / `APERTUS_*`, `HISTORY_MESSAGES`, `KEEP_CACHE`) |
| `src/alpenrecht/cache.py` | empties `cache/` when the last running question finishes |
| `src/alpenrecht/app.py`, `web/` | Flask server and the UI (DE/FR/IT/RM/EN, citation hover, level map) |
| `data/` | commune → website table (2,142 communes, from Wikidata) |
| `eval/` | benchmarks: question sets, runner (`accuracy_run.py`), results |
| `tests/` | offline tests |

## Why it matters

- **Multi-level by design**: shows how federal, cantonal and communal rules fit together (Art. 3 / 49 BV).
- **Multilingual**: DE/FR/IT federal texts are equally authentic, so Alpenrecht reads the version in your language.
  Cantonal law is read in the canton's language.
- **Point in time**: federal law is answered as of any date (Fedlex consolidations).
- **Grounded**: answers cite retrieved articles only, and the UI flags any citation that isn't in the sources.
- **Sovereign**: open model and public data, so it can run on-prem for a canton or commune.

## Communal law (automatic)

There is no central collection of Swiss municipal regulations, so Alpenrecht finds them itself (`src/alpenrecht/communal.py`):

1. **Website:** swisstopo gives the commune's BFS number, and `data/communes.json` maps it to the official
   website. This table was built once from Wikidata and covers 2,142 communes.
2. **Index pages:** the crawler looks for the regulations page on the homepage, one navigation level down
   ("Politik & Verwaltung", "Officiel"…), in the sitemap and at common CMS paths. It also reads regulation
   lists that the widespread commune CMS embeds as JSON.
3. **Apertus picks** the regulations that fit the question, using domain hints (police regulation → noise,
   quiet hours, dogs; waste, fee, building and burial regulations), and then the articles that answer it.
   If nothing fits, nothing is added.
4. **Scanned PDFs** (common for older regulations) are read by Apertus itself: v1.5 takes images, and each
   page is transcribed with the 8B model, about 20 s for a 24-page regulation. The text is cached.

Crawls are cached per commune for a week. Uploading a PDF or URL still works and adds to what was found.

Also handled:
- **TLex** collections (`<commune>.tlex.ch`, e.g. Cham and Aarau) are read through their JSON API.
- **Garbled or scanned PDFs:** PDFs whose fonts extract as gibberish go through Apertus OCR, like scanned ones.
- **Two-column layouts** are re-extracted in layout mode, and **headings that lost their line breaks**
  ("… zu bringen. § 3 Vollzug") are split inline. **Table-of-contents lines** are dropped.
- **Polite crawling:** about 0.6 s between requests per site, with one patient retry on HTTP 429.
  `<base href>`, non-ASCII URLs and PDFs listed in sitemaps or linked directly are all supported.

Results:
- **Hand-picked benchmark:** 21 communal questions in 8 communes that publish readable lists. 19/21 find and
  cite the commune's own regulation, e.g. Chur's Polizeigesetz Art. 30 "Nachtruhe 23.00–07.00".
- **Random communes**, an honest measure of coverage. The first 10 random communes went from 2/10 before
  these fixes to 6/10 after re-tuning on a second set. On a fresh, unseen set of 10, 4 were answered from the
  correct regulation and 2 cited the wrong or unreadable text. Bubikon's unreadable text has since been fixed
  by OCR, Ufhusen's wrong pick has not. The rest are communes with no rule on the topic or no readable list.
- **Remaining limits:** sites that are JavaScript apps or block bots (e.g. Hersberg via the BL canton portal,
  Bern's stadtrecht.bern.ch), sites without a linked regulations page, and occasional wrong regulation picks.
  In those cases the app says so and asks for an upload.

## Citations you can check

Hover a citation chip to see the cited article with the sentence that supports the claim highlighted (shared words
and figures decide the match). Clicking opens the full article in the side panel, scrolled to that sentence.

## Figures (fees, taxes, emoluments)

Amounts usually sit in annexes and tariff tables at the end of a regulation. Fedlex annexes (`<section id="annex_N">`)
and the Anhang / Annexe / Allegato / Tarif sections of cantonal and communal PDFs are indexed as sources of their own,
in parts when long, instead of being cut off after the last article.

## Known limits

- Cantonal law is the current version only. LexFind does have version history, which is a possible next step.
- Case law covers published Federal Supreme Court decisions (BGE) with an official headnote only.
- Article splitting of cantonal PDFs is heuristic (`Art.` / `Article` / `§`).
- Legal information, not legal advice.
