## Purpose and prototype

Alpenrecht AI helps users inspect Swiss legal information across federal, cantonal and communal levels. A question and a Swiss place lead to retrieved source texts and an Apertus-generated explanation structured by level. The project is a research prototype: its current evaluation does not establish reliability for legal decisions.

The interface supports DE, FR, IT, RM and EN. It resolves places through swisstopo, searches Fedlex and LexFind, discovers regulations on official commune websites, and allows communal PDF or URL uploads. It also retrieves selected published Federal Supreme Court decisions through entscheidsuche.ch.

Users can inspect citations in a side panel. Citation hovers highlight sentences using shared words and figures. This is a navigation aid; it does not prove that a cited passage supports the claim. Automated citation checks and model-based review can still miss substantive mistakes.

## Architecture

A Python package and Flask backend stream progress to a browser chat interface. An OpenAI-compatible client uses swiss-ai/Apertus-v1.5-70B by default for answers and checks, with the 8B model used for scanned-page transcription.

- **Locate and plan:** swisstopo resolves the commune and canton. Apertus identifies relevant levels and generates act names, article references and search terms.
- **Federal law:** Fedlex SPARQL discovers acts and consolidations valid on the requested date. Official HTML is split into articles with section context.
- **Cantonal law:** Apertus generates LexFind searches and selects acts and articles. Wildcard stems help with compound terms. Current cantonal texts are used.
- **Communal law:** a stored inventory maps 2,142 commune entries to websites. A crawler discovers regulation lists, with TLex support and dedicated readers for Zurich, Geneva, Basel, Lausanne, Bern and Lugano. Basel uses the cantonal collection. This inventory is not a coverage guarantee.
- **Documents:** extraction includes articles, annexes and tariff tables. Scanned or garbled PDFs can use image transcription. Caching, URL handling and rate-limit retries support retrieval.
- **Case law:** the system searches entscheidsuche.ch and selects up to two published Federal Supreme Court decisions with headnotes.
- **Answer and check:** rank evidence, draft a cited answer, validate citation identifiers and named articles, then run model-based claim checking and rewriting for three rounds.

## Final held-out evaluation

The final recorded comparison covers 100 held-out questions: 39 federal, 12 cantonal and 49 communal (46 DE, 34 FR, 12 IT, 8 EN). The questions and reference answers were drafted by AI agents (Claude, Anthropic) researching the official sources, and a second Claude agent re-checked each item (15 corrected, none dropped); none was written by a human or checked by a lawyer. The original prototype and the evaluated version (commit c0c4e48) answered the same questions, and Claude agents graded the answers blind and pairwise against the references on a 0-3 rubric. There was one AI grading pass and no human adjudication. These are internal prototype results, not independently validated accuracy.

- **Mean score (0-3):** original 1.38; evaluated 1.39.
- **Fully correct (score 3):** original 19/100; evaluated 21/100.
- **Usable under the rubric (score at least 2):** 46/100 for both versions. The recorded 95% interval is approximately 37-56%; it does not account for grading errors or dataset representativeness.
- **Answers flagged with a factual error:** original 53/100; evaluated 43/100.
- **Governing source cited:** original 58/100; evaluated 53/100.
- **Off-topic padding flagged:** original 36/100; evaluated 22/100.
- **Blind preference:** evaluated version preferred on 43 questions, original on 36, with 21 ties.

Mean scores of the evaluated version by level were 1.95/3 federal, 1.58/3 cantonal and 0.90/3 communal. Original means were 1.92, 1.92 and 0.82 respectively. The cantonal sample contains only 12 questions; its apparent decline needs further investigation.

The usable-answer rate was unchanged. Factual-error and padding flags were less frequent in this sample, but governing-source citation declined and communal performance remains weak. A usable rubric score is not an error-free-answer guarantee: correctness scores and factual-error flags were recorded separately.

## Measurement limits

Earlier development benchmarks measured retrieval or citation success, sometimes on hand-picked communes. They are not interchangeable with held-out answer correctness. The earlier 85/100 source-citation claim is therefore not presented as final accuracy. In the held-out run (15 answers in parallel on a shared endpoint), the evaluated version took 99 s per answer on average (median 96 s, 10-90% range 61-142 s, maximum 208 s), against 140 s for the original; OCR, networking and verification can materially affect response time.

The held-out set is not fully independent of development. On the last day, earlier candidate versions were run and graded on it; one candidate scored 1.33/3 against 1.51/3 for the original in that pass, and the decision to restore the original relevance filter and federal article choice (commit c0c4e48) was taken from those grades. The same original answers scored 1.51/3 in that earlier pass and 1.38/3 in the final pass, so single-pass AI grading noise is about ±0.1/3 on this set.

The final aggregate is recorded in eval/ACCURACY_heldout100.txt, with questions in eval/questions_heldout100.json and references in eval/heldout100_reference.json. The answers of both versions, the blind grades and the unblinding key are in eval/heldout/, where score.py recomputes the aggregate. Development runs remain under eval/. The held-out figures were measured on commit c0c4e48 (the same pipeline code as fdb96d8). Later commits 9eb4d52 (fee and tariff handling, CHF amount check, the Lugano reader) and 3bef387 (conversation memory, cache clearing) were not measured on the held-out set; the fee changes were checked only on 18 fee questions and a 20-question regression sample (eval/FEES.md).

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
- **Performance:** answers took about 100 s on average in the held-out run, and later commits have not been re-timed. Explore early stopping only if correctness is preserved.
- **Deployment:** assess a limited pilot with curated regulations and human oversight. On-premise hosting is an architectural possibility, not a completed deployment or privacy certification.

This is legal information for source discovery and inspection. Automated checking does not guarantee complete or correct legal answers. Demo video: https://youtu.be/cG-jVfxx4d8.
