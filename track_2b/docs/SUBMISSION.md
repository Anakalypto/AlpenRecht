## Purpose and prototype

Alpenrecht AI helps users inspect Swiss legal information across federal, cantonal and communal levels. A question and a Swiss place lead to retrieved source texts and an Apertus-generated explanation structured by level. The project is a research prototype: its current evaluation does not establish reliability for legal decisions.

The interface supports DE, FR, IT, RM and EN. It resolves places through swisstopo, searches Fedlex and LexFind, discovers regulations on official commune websites, and allows communal PDF or URL uploads. It also retrieves selected published Federal Supreme Court decisions through entscheidsuche.ch.

Users can inspect citations in a side panel. Citation hovers highlight sentences using shared words and figures. This is a navigation aid; it does not prove that a cited passage supports the claim. Automated citation checks and model-based review can still miss substantive mistakes.

## Architecture

A Python package and Flask backend stream progress to a browser chat interface. An OpenAI-compatible client uses swiss-ai/Apertus-v1.5-70B by default for answers and checks, with the 8B model used for scanned-page transcription.

- **Locate and plan:** swisstopo resolves the commune and canton. Apertus identifies relevant levels and generates act names, article references and search terms.
- **Federal law:** Fedlex SPARQL discovers acts and consolidations valid on the requested date. Official HTML is split into articles with section context.
- **Cantonal law:** Apertus generates LexFind searches and selects acts and articles. Wildcard stems help with compound terms. Current cantonal texts are used.
- **Communal law:** a stored inventory maps 2,142 commune entries to websites. A crawler discovers regulation lists, with TLex support and dedicated readers for Zurich, Geneva, Basel, Lausanne and Bern. Basel uses the cantonal collection. This inventory is not a coverage guarantee.
- **Documents:** extraction includes articles, annexes and tariff tables. Scanned or garbled PDFs can use image transcription. Caching, URL handling and rate-limit retries support retrieval.
- **Case law:** the system searches entscheidsuche.ch and selects up to two published Federal Supreme Court decisions with headnotes.
- **Answer and check:** rank evidence, draft a cited answer, validate citation identifiers and named articles, then run model-based claim checking and rewriting for up to three rounds.

<!-- PAGE -->

## Final held-out evaluation

The final recorded comparison covers 100 held-out questions: 39 federal, 12 cantonal and 49 communal. Answers were graded blind by AI against references and official-law text. There was one AI grading pass and no human adjudication. These are internal prototype results, not independently validated accuracy.

- **Mean score (0-3):** original 1.38; current 1.39.
- **Fully correct (score 3):** original 19/100; current 21/100.
- **Usable under the rubric (score at least 2):** 46/100 for both versions. The recorded 95% interval is approximately 37-56%; it does not account for grading errors or dataset representativeness.
- **Answers flagged with a factual error:** original 53/100; current 43/100.
- **Governing source cited:** original 58/100; current 53/100.
- **Off-topic padding flagged:** original 36/100; current 22/100.
- **Blind preference:** current preferred on 43 questions, original on 36, with 21 ties.

Current mean scores by level were 1.95/3 federal, 1.58/3 cantonal and 0.90/3 communal. Original means were 1.92, 1.92 and 0.82 respectively. The cantonal sample contains only 12 questions; its apparent decline needs further investigation.

The usable-answer rate was unchanged. Factual-error and padding flags were less frequent in this sample, but governing-source citation declined and communal performance remains weak. A usable rubric score is not an error-free-answer guarantee: correctness scores and factual-error flags were recorded separately.

## Measurement limits

Earlier development benchmarks measured retrieval or citation success, sometimes on hand-picked communes. They are not interchangeable with held-out answer correctness. The earlier 85/100 source-citation claim is therefore not presented as final accuracy. No supported current end-to-end latency estimate is claimed here; OCR, networking and verification can materially affect response time.

The final aggregate is recorded in eval/ACCURACY_heldout100.txt, with questions in eval/questions_heldout100.json and references in eval/heldout100_reference.json. Development runs remain under eval/. This report documents repository checkpoint 2a7f9fb.

<!-- PAGE -->

## Implementation and review

Repository: https://github.com/Anakalypto/AlpenRecht

The root contains a README and Apache-2.0 licence. Implementation is under track_2b/, including src/alpenrecht/, data/, docs/, eval/ and tests/, alongside the Dockerfile, Makefile and .env.example.

- **Configure:** set LLM_API_KEY, optionally LLM_BASE_URL and LLM_NAME. Defaults target the CSCS endpoint and Apertus v1.5 70B. APERTUS_* names remain supported. Keep credentials outside version control.
- **Run:** from track_2b/, use make run with Docker installed, then open http://localhost:5055. Alternative Python setup is in the project README.
- **Check:** make test builds the image and runs offline tests. Parsing and citation tests do not establish legal accuracy.
- **Inspect:** ask a question for a Swiss place, follow retrieval progress and open cited passages to assess the answer against the evidence.

## Challenges and lessons

Communal sources vary from structured lists to JavaScript collections, old scans, two-column PDFs and broken fonts. Dedicated readers, OCR fallbacks, layout-aware extraction and fee-table indexing address parts of this problem, without establishing complete coverage.

A related but incorrect provision can yield a fluent answer with valid citation identifiers and incorrect legal content. Retrieval quality and answer correctness must be evaluated separately. Testing unfamiliar communes exposed failures that hand-picked examples missed.

## Next steps and limitations

- **Communal coverage:** improve discovery failures, wrong regulation choices and unreadable texts. City readers and uploads already exist; general coverage remains incomplete.
- **Correctness:** investigate wrong provisions, missed exceptions, authority names and deadlines with fresh held-out questions and human legal review.
- **Temporal coverage:** extend point-in-time retrieval to cantonal law, which currently uses current texts.
- **Case law:** evaluate coverage and relevance beyond the current published BGE/headnote subset before expanding it.
- **Performance:** measure current end-to-end latency before making speed claims. Explore early stopping only if correctness is preserved.
- **Deployment:** assess a limited pilot with curated regulations and human oversight. On-premise hosting is an architectural possibility, not a completed deployment or privacy certification.

This is legal information for source discovery and inspection. Automated checking does not guarantee complete or correct legal answers. The hackathon form and demo video remain separate submission items.
