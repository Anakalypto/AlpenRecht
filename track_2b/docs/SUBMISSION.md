## Inspiration

In Switzerland, the answer to a simple question like "Must my dog be on a leash?" or "When does night-time quiet start?" depends on where you live. The rule can sit in federal law, in one of 26 cantonal legal systems, or in the regulation of one of more than 2,000 communes, in four languages and on different websites. No single place answers across all three levels. Commercial legal AI tools focus on federal law, and general chatbots happily invent article numbers. We wanted a tool that answers the way Swiss law is actually built: by level, in your language, and with a source for every claim.

## What it does

Alpenrecht AI takes a legal question and an address and returns one answer covering all three levels of Swiss law.

- **Finds your commune and canton** from the address (swisstopo).
- **Searches all three levels live:** federal law on Fedlex, cantonal law on LexFind, and communal regulations on your commune's own website, including old scanned PDFs.
- **Writes a short answer with Apertus,** structured by level (Bund / Kanton / Gemeinde), explaining how the levels fit together and what to do next, in DE, FR, IT, Romansh or EN.
- **Checks every answer three times before you see it.** Each claim is compared with its source, missing articles are fetched, and anything unsupported is corrected.
- **Cites everything:** each statement links to the official article, and you can read the full text in a side panel.
- **Answers as of a date** for federal law, and lets you upload a communal regulation if one can't be found online.

Example: "Ab wann gilt in Chur die Nachtruhe?" gives "23.00–07.00 Uhr", cited to Art. 30 of Chur's Polizeigesetz, next to what the canton of Graubünden and the Confederation say.

## How we built it

- **Model:** Apertus v1.5 (70B for answers and checks, 8B for reading scanned pages) on the Hack Apertus CSCS endpoint, via its OpenAI-compatible API.
- **Federal law:** Fedlex's SPARQL endpoint finds acts in force and the version valid on a given date. We split the official HTML into articles with their section headings. Apertus names the likely acts and articles, and we fetch those exactly, so an invented article number simply finds nothing.
- **Cantonal law:** an Apertus-driven LexFind agent. Apertus writes the search queries (likely act titles and wildcard stems), picks the most relevant acts, then picks the articles from their headings.
- **Communal law:**
  - Wikidata gave us the official websites of 2,142 communes.
  - A polite crawler finds each commune's regulations page; we also read TLex collections through their API.
  - Apertus chooses the right regulation and article.
  - Scanned or garbled PDFs are transcribed by Apertus's image input.
- **Verification:** deterministic checks (every citation exists, every article named is in the sources), then an Apertus fact-check of each claim, then a rewrite where needed. This runs three rounds.
- **App:** Python and Flask on the backend, streaming progress to a single-page chat UI. It supports five languages and light and dark mode, and works on phones.
- **Evaluation:** a 100-question benchmark (68 federal, 32 cantonal) with sources we verified by hand, plus random-commune tests.

## Challenges we ran into

- **Three very different sources.** Fedlex is structured linked data, LexFind is a search API over PDFs, and communes publish however they like: CMS lists, JavaScript apps, two-column PDFs, 1980s scans, broken fonts.
- **Model errors that look plausible.** Apertus put article numbers where law numbers belong, produced broken JSON, called inheritance shares "cantonal", and cited articles from memory. Each became a fix: a new plan format, a tolerant parser, fallback searches, and the verification loop.
- **Search quirks.** LexFind matches whole words only, so "Steuern" never finds "Steuergesetz". Wildcard stems plus Apertus-written queries took cantonal retrieval from 11/32 to 28/32.
- **The open web.** Rate limits (HTTP 429), bot blocking, relative links behind `<base href>`, non-ASCII URLs, and table-of-contents pages that look like articles.
- **Honest measurement.** Our first communal benchmark looked great at 19/21, but a fresh set of random communes gave 4/10. We kept testing on communes the system had never seen.
- **Speed versus trust.** Three verification rounds roughly triple the answer time, to about 50 seconds.

## Accomplishments that we're proud of

- **85/100** answers cite the correct legal source on our verified benchmark, up from 67 at baseline, and answers naming an article that isn't in the sources fell from **13 to 0**.
- **Cantonal retrieval went from 11/32 to 29/32** once Apertus drove the LexFind search.
- **Communal law from the commune's own website,** across many different site setups, including scanned regulations that Apertus reads itself.
- **One answer covering all three levels** of Swiss law, in five languages, with every claim cited and checked.
- **Open and sovereign:** an open Swiss model and public data, so a canton or commune could host it on its own servers.

## What we learned

- **Retrieval decides the quality.** Most wrong answers came from fetching the wrong article, not from bad writing. The biggest gains came from letting Apertus *steer* retrieval (queries, act choice, article choice) while code does the exact lookups.
- **Ask a model to be specific.** "List every claim with a verdict" catches far more than "find problems", and "return the titles" is more robust than "return the numbers".
- **Deterministic checks beat hope.** A simple check that every named article exists in the sources removed a whole class of invented references.
- **Benchmarks must include data the system hasn't seen.** Our hand-picked communal test overstated coverage; random communes told us the truth.
- **Swiss law is a data problem as much as an AI problem.** The legal texts are public, but they are scattered across levels, formats and languages.

## What's next for Alpenrecht

- **Big-city law platforms:** readers for the JavaScript-based collections of Bern, Zürich, Geneva, Lausanne and Lugano, so the largest communes are covered.
- **Apertus article picking for Fedlex,** to fix most of the remaining federal misses.
- **Faster answers:** fact-checking with the 8B model, streaming the final answer, and skipping rounds once an answer is clean.
- **Case law:** adding Federal Supreme Court and cantonal court decisions (entscheidsuche.ch) next to the statutes.
- **Point-in-time answers for cantonal law,** using LexFind's version history.
- **Deployment with a canton or commune:** an on-premise pilot for their citizen help desk, with their own regulations loaded and kept current.
