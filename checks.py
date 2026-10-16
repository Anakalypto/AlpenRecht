"""Post-checks on a generated answer: citation validity, article-number fidelity, prose-citation repair.

Used live (the UI shows the repaired text and any warnings) and by the benchmark.
"""
import re

import sources

# "Art. 257d", "art. 32abis", "Artikel 7", "article 18a", "articolo 3"
_ART = re.compile(r"\b(?:Art(?:ikel|icle|icolo)?\.?|art(?:icle|icolo)?\.?)\s*"
                  r"(\d+(?:[a-z]?\s?(?:bis|ter|quater|quinquies|sexies)|[a-z]{1,2})?)(?![a-z])")
_CITE = re.compile(r"\[(\d{1,2})\]")
# A parenthetical that cites an article instead of using [n]: "(Art. 7 Abs. 1 Hundegesetz BE)"
_PROSE = re.compile(r"\s?\(((?:[^()]*?\b)?(?:Art|art)(?:ikel|icle|icolo)?\.?\s*\d[^()]*)\)")
# Federal precedence is allowed without a source.
_ALLOWED = re.compile(r"(?:Art\.|art\.)\s*49\s*(?:BV|Cst|Cost)", re.I)


def art_key(number):
    """'Art. 257d' / 'art. 32 abis' / 'Art. 25 Auskunftsrecht' -> '257d' / '32abis' / '25'.
    Annexes and unstructured parts keep their kind ('Anhang 1' -> 'anhang1'), so they never pass for Art. 1."""
    a = re.match(r"\s*(anhang|annexe|annex|allegato|tarif\w*|teil|gebuhrentarif|gebührentarif)\s*(\d*)", number.lower())
    if a:
        return a.group(1)[:7] + a.group(2)
    m = re.search(r"(\d+)\s?((?:[a-z]?\s?(?:bis|ter|quater|quinquies|sexies))|[a-z]{1,2})?(?![a-z])", number.lower())
    return (m.group(1) + re.sub(r"\s+", "", m.group(2) or "")) if m else ""


def _law_tokens(ev):
    toks = {ev.get("law", ""), ev.get("sr", "")}
    toks |= {w for w in re.findall(r"[A-Za-zÀ-ÿ]{3,}", ev.get("title", "")) if w[0].isupper()}
    return {sources.fold(t) for t in toks if t}


def _match_source(paren, evidence):
    """Find the source a prose citation refers to (by article number, disambiguated by law name)."""
    m = _ART.search(paren)
    if not m:
        return None
    key = art_key(m.group(1))
    cands = [e for e in evidence if art_key(e["number"]) == key]
    if len(cands) == 1:
        return cands[0]
    folded = sources.fold(paren)
    named = [e for e in cands if any(tok and tok in folded for tok in _law_tokens(e))]
    return named[0] if len(named) == 1 else None


def repair(text, evidence):
    """Turn prose citations into [n] where the source is unambiguous."""
    fixed = 0

    def sub(m):
        nonlocal fixed
        if _ALLOWED.search(m.group(1)):
            return m.group(0)
        ev = _match_source(m.group(1), evidence)
        if not ev:
            return m.group(0)
        fixed += 1
        return f" [{ev['id']}]"

    text = _PROSE.sub(sub, text)

    # "[1, al. 2 let. a]" / "[1, al. 2; 2]": keep the paragraph detail as text, make each source a clickable [n].
    def pinpoint(m):
        parts = [p.strip() for p in m.group(1).split(";")]
        ids, details = [], []
        for p in parts:
            n = re.match(r"(\d{1,2})\b\s*,?\s*(.*)", p)
            if n:
                ids.append(n.group(1))
                if n.group(2):
                    details.append(n.group(2))
        if not ids:
            return m.group(0)
        return (f" ({'; '.join(details)}) " if details else " ") + "".join(f"[{i}]" for i in ids)

    text = re.sub(r"\s?\[(\d{1,2}\s*,[^\]]+|\d{1,2}\s*;[^\]]+)\]", pinpoint, text)
    # "[49 Cst]" / a bare "[49]" is federal precedence written as a citation, not a source.
    text = re.sub(r"\[(?:Art\.?\s*)?49\s*(BV|Cst|Cost)\.?\]", r"(Art. 49 \1)", text, flags=re.I)
    if not any(e["id"] == 49 for e in evidence):
        text = re.sub(r"\s?\[49\]", "", text)
    # Collapse doubled citations created by the repair: "[9] [9]" -> "[9]"
    text = re.sub(r"\[(\d+)\](?:\s*\[\1\])+", r"[\1]", text)
    return text, fixed


def check(text, evidence):
    ids = {e["id"] for e in evidence}
    keys = {art_key(e["number"]) for e in evidence}
    cited = [int(n) for n in _CITE.findall(text)]
    invalid = sorted({n for n in cited if n not in ids})
    prose = [m.group(1) for m in _PROSE.finditer(text) if not _ALLOWED.search(m.group(1))]
    unsupported = []
    for m in _ART.finditer(text):
        window = text[m.start():m.end() + 12]
        if _ALLOWED.search(window):
            continue
        if art_key(m.group(1)) not in keys:
            unsupported.append(m.group(0).strip())
    return {
        "words": len(text.split()),
        "citations": len(cited),
        "cited_ids": sorted(set(cited) & ids),
        "invalid_citations": invalid,
        "prose_citations": len(prose),
        "unsupported_articles": sorted(set(unsupported)),
    }
