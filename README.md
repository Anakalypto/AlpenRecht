# Alpenrecht AI

**One legal question → every level of Swiss law.** Federal (Bund), cantonal (Kanton) and communal (Gemeinde)
rules, retrieved live from official sources and explained with citations by **Apertus**, the Swiss open LLM.

## Run

```bash
cp .env.example .env        # then paste your APERTUS_API_KEY
.venv/Scripts/python.exe app.py   # http://127.0.0.1:5055
```

Defaults target the Hack Apertus CSCS inference endpoint (`https://api.inference.cscs.ch/v1`) with
`swiss-ai/Apertus-v1.5-70B`. Hackathon keys only cover the v1.5 models, and `swiss-ai/Apertus-v1.5-8B` is about 2× faster.
`APERTUS_BASE_URL` / `APERTUS_MODEL` can point at any OpenAI-compatible Apertus endpoint, including a local vLLM
for air-gapped use. Without a key, retrieval still runs and the app shows the sources only.

## How it works

```
question + place + date
   │
   ├─ swisstopo ─────────── address → commune, BFS no., canton, official languages
   ├─ Apertus (planner) ─── which levels? SR numbers, title/keyword terms per language
   ├─ Fedlex SPARQL ─────── in-force acts → consolidation valid on <date> → per-article HTML
   ├─ LexFind API ───────── cantonal law of that canton (26 collections, one API) → articles
   ├─ communal docs ─────── uploaded PDF / URL (no central collection exists)
   ├─ ranking ───────────── stemmed BM25-ish over articles + section breadcrumbs
   └─ Apertus (answer) ──── streamed, per-level, every claim cited [n] → official source link
```

| File | Role |
|---|---|
| `sources.py` | swisstopo, Fedlex, LexFind clients, article splitting, ranking, disk cache |
| `pipeline.py` | plan → retrieve → answer, emitted as server-sent events |
| `apertus.py` | OpenAI-compatible client (JSON + streaming) |
| `uploads.py` | communal regulations (PDF/HTML/text or URL) |
| `static/` | UI (DE/FR/IT/RM/EN), live pipeline, level map, citation chips |

## Why it matters

- **Multi-level by design**: shows how federal, cantonal and communal rules fit together (Art. 3 / 49 BV).
- **Multilingual**: DE/FR/IT federal texts are equally authentic, so Alpenrecht reads the version in your language.
  Cantonal law is read in the canton's language.
- **Point in time**: federal law is answered as of any date (Fedlex consolidations).
- **Grounded**: answers cite retrieved articles only, and the UI flags any citation that isn't in the sources.
- **Sovereign**: open model and public data, so it can run on-prem for a canton or commune.

## Communal law (automatic)

There is no central collection of Swiss municipal regulations, so Alpenrecht finds them itself (`communal.py`):

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

## Known limits

- Cantonal law is the current version only. LexFind does have version history, which is a possible next step.
- Communal law has to be uploaded. A crawler for commune websites is the natural next step.
- Article splitting of cantonal PDFs is heuristic (`Art.` / `Article` / `§`).
- Legal information, not legal advice.
