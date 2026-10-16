# Alpenrecht AI — Hack Apertus 2026 · Track 2B · Own project

**Team RedPandas** — Christopher Yazigi, Giovanni Yazbeck, Alfredo Pio Yazbeck

**One legal question → every level of Swiss law.** Ask a question for a Swiss place; Alpenrecht retrieves the
federal (Fedlex), cantonal (LexFind) and communal (the commune's own website) rules live, adds leading court
decisions (entscheidsuche.ch), and **Apertus** writes one answer per level with every claim cited to the official
text and fact-checked before display. DE / FR / IT / RM / EN.

➡ **Project:** [`track_2b/`](track_2b) · [README](track_2b/README.md) · [submission text](track_2b/docs/SUBMISSION.md)
· [evaluation](track_2b/eval)

```bash
cd track_2b && make run      # needs LLM_API_KEY (and optionally LLM_BASE_URL / LLM_NAME) → http://localhost:5055
```

Without Docker: `cd track_2b && python -m venv .venv && .venv/Scripts/pip install -r requirements.txt`, then
`PYTHONPATH=src .venv/Scripts/python -m alpenrecht serve` (Python 3.12+).

Licence: Apache-2.0 (see [LICENSE](LICENSE)).
