"""Three-round verification of a drafted answer before the user sees it.

Each round:
  1. deterministic checks (citations exist, named articles are in the sources, no prose citations);
  2. source enrichment: articles the answer names, or the verifier asks for, are fetched from the
     already-loaded law texts or from Fedlex and added as real, numbered sources when they exist;
  3. an Apertus fact-check of every claim against the cited source (JSON report);
  4. a revision, only when the round found something to fix.
"""
import json
import re

from . import apertus
from . import checks
from . import config
from . import sources

MAX_SOURCES = 20

VERIFY_PROMPT = """You are a strict fact-checker for a Swiss legal answer. Compare the ANSWER with the numbered SOURCES.

Step 1 — go through the ANSWER sentence by sentence. For EVERY sentence that states a legal rule, add an entry to
"claims" and decide, by reading the cited source text, whether that source really says it:
  - supported: true only if the cited source text states it (numbers, deadlines, conditions must match);
  - supported: false if the citation is missing, points to the wrong source, or the source says something else.
  - supported: false if the cited source is about a different subject that merely shares a word with the claim
    (e.g. an article on driving licences cited for a residence permit, or a building permit for a work permit).
  - supported: false if a number, deadline, amount, age or authority name in the sentence is not in the cited source,
    also in the "next steps" part, or if the source's wording is changed in substance ("may" turned into "must",
    a rule for a special category presented as the general rule, per mille written as percent).
  - A sentence in "next steps" that gives a deadline, fee or authority without any citation counts as a claim too.
Step 2 — list sources that directly answer the question but are not used ("ignored_sources").
Step 3 — list federal articles a Swiss lawyer would clearly cite for this question that are NOT among the
sources ("missing_sources", SR number of the act + article number).

Return ONLY JSON:
{{"claims": [{{"quote": "max 12 words from the answer", "cited": [1], "supported": true, "problem": "", "fix": ""}}],
 "ignored_sources": [3],
 "missing_sources": [{{"sr": "<SR number>", "article": "<article>"}}]}}
"missing_sources" is usually empty; never copy this example.
Judge substance only, not style.

QUESTION
{question}

SOURCES
{sources}

ANSWER
{answer}"""

REVISE_SUFFIX = """

YOUR DRAFT
{draft}

VERIFICATION FINDINGS — fix every one of them
{findings}

Write the corrected final answer now. Same headings and rules. Keep every correct concrete detail (figures,
deadlines, conditions, authorities); remove or correct only what is not supported; cite newly added sources where
they answer the question. Do not make the answer vaguer or shorter than needed."""


RELEVANCE_PROMPT = """Question: {question}

Retrieved legal provisions (number · act · heading/first words):
{listing}

Which provisions help answer THIS question? Exclude provisions about other situations, even from the same act
(e.g. detention or removal rules for a question about obtaining a permit; court deposits for a question about rental
deposits). Always keep provisions that name the competent authority, the procedure, fees or deadlines for this matter,
at every level (federal, cantonal, communal), and a commune's fee, tariff or quiet-hours provision when the question
is about that fee or rule. Drop communal police or building provisions when the question is about another subject
(naturalisation, adoption, pensions, employment). Return ONLY a JSON list of the numbers to keep, e.g. [1, 2, 9]."""


def relevant_sources(question, evidence):
    """Apertus keeps the provisions that answer the question; the rest stay visible in the UI but out of the answer."""
    if len(evidence) <= 3:
        return evidence
    judged = evidence
    listing = "\n".join(f"[{e['id']}] {e['level'][:3]} {e['law'][:40]} {e['number']} · "
                        f"{re.sub(r'\s+', ' ', e['text'][len(e['number']):])[:160]}" for e in judged)
    try:
        raw = apertus.chat([{"role": "user", "content": RELEVANCE_PROMPT.format(question=question, listing=listing)}],
                           temperature=0.0, max_tokens=120)
    except apertus.ApertusError:
        return evidence
    m = re.search(r"\[[\d,\s]*\]", raw)
    keep = {int(x) for x in re.findall(r"\d+", m.group(0))} if m else set()
    # Each level's first picks are Apertus' own best choices from a reading of the act; the filter (judging only
    # 160-character snippets) once dropped every federal article on e-scooters, including LCR art. 43 on pavements.
    top = {e["id"] for lv in ("federal", "cantonal") for e in [x for x in evidence if x["level"] == lv][:2]}
    kept = [e for e in evidence if e["id"] in keep or e["id"] in top]
    return kept or evidence


def source_block(evidence):
    """The numbered source list the model sees (trimmed excerpt + real act title)."""
    return "\n\n".join(
        f"[{e['id']}] {e['level'].upper()} · {e['law']}{' (SR ' + e['sr'] + ')' if e['sr'] and e['level'] == 'federal' else ''}"
        f" · {e['number']} · act: {e['title'][:160]}{' · section: ' + e['path'][-160:] if e['path'] else ''}"
        f" · version {e['version']}\n{e['text'][:3500]}"
        for e in evidence) or "(no sources retrieved)"


def federal_evidence(act, version, art):
    return {"level": "federal", "law": act["short"] or act["title"], "title": act["title"], "sr": act["sr"],
            "number": art["number"], "path": art["path"], "text": art["text"][:3500], "url": art["url"],
            "version": version["date"], "lang": version["lang"], "origin": "Fedlex"}


def cantonal_evidence(tol, art, canton, lang):
    return {"level": "cantonal", "law": f"{canton} {tol['sr']}", "title": tol["title"], "sr": tol["sr"],
            "number": art["number"], "path": tol.get("category", ""), "text": art["text"][:3500],
            "url": art["url"], "version": tol.get("since") or "current", "lang": lang, "origin": "LexFind"}


def _add(evidence, ev):
    """Append a source unless it is already there; returns the source (new or existing) or None if full."""
    for e in evidence:
        if e["sr"] == ev["sr"] and checks.art_key(e["number"]) == checks.art_key(ev["number"]):
            return e
    if len(evidence) >= MAX_SOURCES:
        return None
    ev["id"] = max((e["id"] for e in evidence), default=0) + 1
    ev["added"] = True
    evidence.append(ev)
    return ev


def _tokens(entry):
    """Names a law goes by in running text: short title (OR, CO, LAT…), SR number, canton + SR."""
    if entry["kind"] == "federal":
        act = entry["act"]
        return {t for t in (act["short"], act["sr"]) if t}
    tol = entry["tol"]
    return {tol["sr"], f"{entry['canton']} {tol['sr']}"} | set(re.findall(r"\b[A-ZÄÖÜ]{2,}[a-z]?\b", tol["title"]))


def enrich_from_mentions(text, evidence, library):
    """Articles the answer names but that aren't sources yet: add them if the named law has that article."""
    keys = {(e["sr"], checks.art_key(e["number"])) for e in evidence}
    added = []
    for m in checks._ART.finditer(text):
        key = checks.art_key(m.group(1))
        if checks._ALLOWED.search(text[m.start():m.end() + 12]):
            continue
        # Only a law name right next to the article counts ("Art. 18a LAT", "LAT Art. 18a", "art. 7 du CC"):
        # a wider window picked up unrelated laws named elsewhere in the sentence.
        after = re.sub(r"^\s*(?:(?:Abs|al|cpv|para|lit|let|Ziff|ch|n)\.?\s*\d+[a-z]?\s*)*(?:des|der|du|de la|de l'|della|del|of the|of)?\s*",
                       "", text[m.end():m.end() + 40])
        ctx = " " + sources.fold(text[max(0, m.start() - 14):m.start()] + " " + after[:18]) + " "
        for entry in library:
            if not any(re.search(rf"(?<![\w.]){re.escape(sources.fold(t))}(?![\w])", ctx) for t in _tokens(entry)):
                continue
            sr = entry["act"]["sr"] if entry["kind"] == "federal" else entry["tol"]["sr"]
            if (sr, key) in keys:
                break
            art = next((a for a in entry["arts"] if checks.art_key(a["number"]) == key), None)
            if art:
                ev = (federal_evidence(entry["act"], entry["version"], art) if entry["kind"] == "federal"
                      else cantonal_evidence(entry["tol"], art, entry["canton"], entry["lang"]))
                got = _add(evidence, ev)
                if got and got.get("added") and got not in added:
                    added.append(got)
                    keys.add((sr, key))
            break
    return added


def fetch_missing(missing, evidence, library, asof, fed_lang, question_hint=""):
    """Federal articles the verifier says are needed: load the act if necessary, add the article if it exists."""
    added = []
    for item in (missing or [])[:3]:
        if not isinstance(item, dict):
            continue
        sr, key = str(item.get("sr", "")).strip(), checks.art_key(str(item.get("article", "")))
        if (sr, key) == ("220", "266c") and "266c" not in question_hint:
            continue  # the prompt's old example, copied into permit and naturalisation answers
        if not re.fullmatch(r"\d+(?:\.\d+)*", sr) or not key:
            continue
        entry = next((e for e in library if e["kind"] == "federal" and e["act"]["sr"] == sr), None)
        if entry is None:
            acts = sources.fedlex_find_acts([sr], [], fed_lang, limit=1)
            if not acts:
                continue
            version, arts = sources.fedlex_articles(acts[0], asof, fed_lang)
            if not version:
                continue
            entry = {"kind": "federal", "act": acts[0], "version": version, "arts": arts}
            library.append(entry)
        art = next((a for a in entry["arts"] if checks.art_key(a["number"]) == key), None)
        if art:
            got = _add(evidence, federal_evidence(entry["act"], entry["version"], art))
            if got and got.get("added") and got not in added:
                added.append(got)
    return added


def _parse_report(raw):
    m = re.search(r"\{.*\}", raw, re.S)
    if m:
        try:
            return json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0)))
        except ValueError:
            pass
    # Salvage claim objects one by one (long reports are where Apertus' JSON breaks).
    claims = []
    for obj in re.findall(r"\{[^{}]*\"quote\"[^{}]*\}", raw):
        try:
            claims.append(json.loads(re.sub(r",\s*([}\]])", r"\1", obj)))
        except ValueError:
            continue
    missing = [{"sr": s, "article": a} for s, a in re.findall(r'"sr"\s*:\s*"([\d.]+)"\s*,\s*"article"\s*:\s*"([^"]+)"', raw)]
    return {"claims": claims, "missing_sources": missing, "ignored_sources": []} if claims or missing else None


def fact_check(question, text, evidence):
    raw = apertus.chat([{"role": "user", "content": VERIFY_PROMPT.format(
        question=question, sources=source_block(evidence), answer=text)}], temperature=0.0, max_tokens=2400,
        model=config.VERIFY_MODEL)
    report = _parse_report(raw) or {"claims": [], "unreadable": True}
    if not report.get("claims") and len(text) > 300:
        # "claims": [] on a full answer is a lazy pass, not a verdict (it let a wrong authority through): ask again.
        raw = apertus.chat([{"role": "user", "content": VERIFY_PROMPT.format(
            question=question, sources=source_block(evidence), answer=text)},
            {"role": "assistant", "content": raw},
            {"role": "user", "content": "You listed no claims. List EVERY sentence of the answer that states a legal rule, "
                                        "with its verdict, as JSON."}],
            temperature=0.2, max_tokens=2400, model=config.VERIFY_MODEL)
        report = _parse_report(raw) or report
    report["raw_chars"] = len(raw)
    ids = {e["id"] for e in evidence}
    claims = [c for c in report.get("claims") or [] if isinstance(c, dict)]
    report["claims_checked"] = len(claims)
    report["issues"] = [{"quote": c.get("quote", ""), "problem": c.get("problem") or "not supported by the cited source",
                         "fix": c.get("fix", "")} for c in claims if c.get("supported") is False][:8]
    report["ignored_sources"] = [n for n in report.get("ignored_sources") or [] if isinstance(n, int) and n in ids][:4]
    report["missing_sources"] = report.get("missing_sources") or []
    return report


def findings(det, report, added, first_round=True):
    """Plain-language list of what the revision must fix (empty: nothing to fix, no revision)."""
    out = []
    for a in det["unsupported_articles"]:
        out.append(f"- \"{a}\" is not among the sources: remove it, or cite the source that contains it.")
    for n in det["invalid_citations"]:
        out.append(f"- Citation [{n}] does not exist: use only numbers from the source list.")
    if det["prose_citations"]:
        out.append("- Some citations are written in prose like \"(Art. …)\": write the rule, then [n].")
    for i in report["issues"]:
        quote = f"\"{i.get('quote', '')}\": " if i.get("quote") else ""
        out.append(f"- {quote}{i['problem']}" + (f" → {i['fix']}" if i.get("fix") else ""))
    if report["ignored_sources"] and first_round:
        out.append(f"- Sources {', '.join(f'[{n}]' for n in report['ignored_sources'])} answer the question but are not used.")
    for e in added:
        out.append(f"- New source [{e['id']}] {e['law']} {e['number']} was added: use it where relevant.")
    return "\n".join(out)
