"""Court decisions from entscheidsuche.ch, chosen by Apertus.

entscheidsuche.ch indexes Swiss federal and cantonal court decisions in one Elasticsearch index (public
`_search.php` endpoint). Published Federal Supreme Court decisions (BGE) carry a Regeste (headnote) in DE/FR/IT.

  1. Apertus writes search queries: statute citations as courts write them ("Art. 262 OR", "art. 262 CO") and
     keyword combinations, from the question and the articles already retrieved;
  2. each query searches the Federal Supreme Court (BGE + other BGer decisions) and the courts of the user's canton;
  3. Apertus reads the candidates (court, date, headnote, matching passages) and picks at most two that decide
     this question;
  4. the picked decisions become numbered sources like any statute, with their headnote and passages.
"""
import html
import json
import re

from . import apertus
from . import sources

SEARCH_URL = "https://entscheidsuche.ch/_search.php"
MAX_PICK = 2
MAX_CANDIDATES = 14

QUERY_PROMPT = """You search Swiss court decisions (Federal Supreme Court and cantonal courts) for a legal question.
Courts cite statutes like "Art. 262 OR", "art. 262 CO", "art. 262 CO" (Italian), "Art. 336c OR", "art. 18a LAT".

Question: {question}
Statutes already found: {statutes}

Write 4 search queries for a full-text search engine. Mix:
  - 2 queries that are a statute citation plus 1-2 topic words, in German and French (e.g. "\\"Art. 262 OR\\" Untermiete",
    "\\"art. 262 CO\\" sous-location"), using the statutes above when they fit;
  - 2 queries of 2-4 precise legal terms, in German and in French or Italian (e.g. "Untermiete Zustimmung verweigern").
Put statute citations in double quotes. Return ONLY JSON: {{"queries": ["...", "...", "...", "..."]}}"""

PICK_PROMPT = """Question: {question}

Swiss court decisions found (number · court · date · headnote / matching passages):
{listing}

Which decisions help answer THIS question, because they interpret the rule the question is about? Prefer
published Federal Supreme Court decisions (BGE / ATF / DTF) and recent ones. Skip decisions on other matters that
only share words. Return ONLY JSON: {{"pick": [numbers, best first, at most {n}], "why": "one short sentence"}}
Return {{"pick": []}} if none fits."""


def _clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def _court(c, lang):
    title = c.get("titles") or {}
    t = title.get(lang) or title.get("de") or next(iter(title.values()), "")
    # "Bundesgericht (BGE) Teil III 11.01.2000 BGE 126 III 69": drop the date and reference, keep the court.
    return re.sub(r"\s*\d{2}\.\d{2}\.\d{4}.*$", "", t).strip()


def search(query, hierarchies, size=8):
    """One full-text query, restricted to the given court hierarchies (e.g. CH_BGE, CH_BGer, ZH)."""
    body = {
        "size": size,
        "_source": ["date", "hierarchy", "title", "abstract", "reference", "attachment.content_url", "attachment.language"],
        "query": {"bool": {
            "must": {"simple_query_string": {"query": query, "default_operator": "and",
                                             "fields": ["attachment.content", "abstract.*", "title.*"]}},
            "filter": {"terms": {"hierarchy": hierarchies}}}},
        "highlight": {"fields": {"attachment.content": {"fragment_size": 280, "number_of_fragments": 3}}},
    }
    data = sources.http(SEARCH_URL, json.dumps(body).encode(), {"Content-Type": "application/json",
                                                               "Accept": "application/json"}, timeout=25, cache=True)
    out = []
    for hit in json.loads(data).get("hits", {}).get("hits", []):
        s = hit.get("_source", {})
        att = s.get("attachment") or {}
        out.append({
            "doc_id": hit["_id"], "score": hit.get("_score") or 0, "date": s.get("date", ""),
            "ref": ", ".join(s.get("reference") or []) or hit["_id"], "hierarchy": s.get("hierarchy") or [],
            "titles": s.get("title") or {}, "abstract": s.get("abstract") or {},
            "passages": [_clean(f) for f in (hit.get("highlight") or {}).get("attachment.content", [])],
            "url": att.get("content_url", ""), "lang": att.get("language", ""),
        })
    return out


def _headnote(c, lang):
    ab = c["abstract"]
    text = ab.get(lang) or ab.get(c["lang"]) or ab.get("de") or next(iter(ab.values()), "")
    return re.sub(r"^(Regeste|Regesto|Regeste)\s*", "", _clean(text))


def _is_bge(c):
    return "CH_BGE" in c["hierarchy"]


def write_queries(question, statutes):
    raw = apertus.chat([{"role": "user", "content": QUERY_PROMPT.format(
        question=question, statutes="; ".join(statutes) or "none yet")}], temperature=0.0, max_tokens=250)
    m = re.search(r"\{.*\}", raw, re.S)
    queries = json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0))).get("queries", []) if m else []
    return [q.strip() for q in queries if isinstance(q, str) and 3 <= len(q.strip()) <= 120][:5]


def _fallback_queries(question, statutes):
    words = [w for w in re.findall(r"[^\W\d_]{5,}", question)][:3]
    out = [f'"{s}"' for s in statutes[:2]]
    if words:
        out.append(" ".join(words))
    return out


def candidates(queries, canton):
    """Run every query on the Federal Supreme Court and on the canton's courts; merge by decision."""
    scopes = [["CH_BGE"]]  # only published leading cases are shown (see retrieve); other courts were searched for nothing
    jobs = [(q, scope) for q in queries for scope in scopes]
    found = {}
    for hits in sources.parallel(lambda job: _safe_search(*job), jobs, workers=6):
        for c in hits:
            prev = found.get(c["doc_id"])
            if prev:
                prev["score"] += c["score"]
                prev["passages"] = list(dict.fromkeys(prev["passages"] + c["passages"]))[:4]
            else:
                found[c["doc_id"]] = c
    # BGE first (they carry headnotes and are the leading cases), then by accumulated relevance.
    return sorted(found.values(), key=lambda c: (-_is_bge(c), -c["score"]))[:MAX_CANDIDATES]


def _safe_search(query, scope):
    try:
        return search(query, scope, size=5)
    except Exception:
        return []


def pick(question, cands, lang):
    listing = "\n".join(
        f"[{i}] {c['ref']} · {_court(c, lang)} · {c['date']}\n    "
        + (_headnote(c, lang)[:420] or " … ".join(c["passages"])[:420])
        for i, c in enumerate(cands, 1))
    raw = apertus.chat([{"role": "user", "content": PICK_PROMPT.format(question=question, listing=listing, n=MAX_PICK)}],
                       temperature=0.0, max_tokens=200)
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        nums = json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0))).get("pick", []) if m else []
    except ValueError:
        nums = [int(x) for x in re.findall(r"\d+", (re.search(r'"pick"\s*:\s*\[([^\]]*)', raw) or [None, ""])[1])]
    out = []
    for n in nums:
        if isinstance(n, int) and 1 <= n <= len(cands) and cands[n - 1] not in out:
            out.append(cands[n - 1])
    return out[:MAX_PICK]


def evidence(c, lang):
    """A picked decision as a numbered source (headnote first, then the passages that matched)."""
    head = _headnote(c, lang)
    parts = [p for p in ([head] if head else []) + c["passages"] if p]
    text = "\n".join(parts)[:2200]
    court = _court(c, lang)
    return {"level": "case", "law": c["ref"], "title": court, "sr": c["doc_id"], "number": c["date"],
            "path": court, "text": text, "url": c["url"], "version": c["date"], "lang": c["lang"],
            "origin": "entscheidsuche.ch"}


def retrieve(question, statutes, canton, lang):
    """-> (queries, candidates, picked evidence dicts). Without Apertus: keyword queries, top BGE hits."""
    try:
        queries = write_queries(question, statutes) or _fallback_queries(question, statutes)
        ai = True
    except (apertus.ApertusError, ValueError):
        queries, ai = _fallback_queries(question, statutes), False
    cands = candidates(queries, canton)
    if not cands:
        return queries, [], []
    # Only published leading cases with an official headnote reach the answer: from bare passages of other decisions
    # the writer inferred outcomes that were wrong (a cantonal appeal that was upheld was cited as confirming the
    # revocation it overturned).
    cands = [c for c in cands if _is_bge(c) and _headnote(c, lang)]
    if not cands:
        return queries, [], []
    if ai:
        try:
            chosen = pick(question, cands, lang)
        except (apertus.ApertusError, ValueError):
            chosen = []
    else:
        chosen = []  # without the model there is no judgement of relevance: show no ruling rather than a random one
    return queries, cands, [evidence(c, lang) for c in chosen]
