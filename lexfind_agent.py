"""Apertus-powered cantonal law search on LexFind.

Three steps, each with a keyword fallback so LexFind keeps working if the model is unavailable:
  1. queries   — Apertus names the canton's likely acts and title stems, in the canton's language;
  2. acts      — Apertus picks the most relevant acts among the candidates LexFind returns;
  3. articles  — Apertus reads the article headings of those acts and picks the provisions that answer.
"""
import json
import re

import apertus
import sources

MAX_TEXTS = 3
MAX_ARTICLES = 6

QUERY_PROMPT = """You help search LexFind, the collection of Swiss cantonal law.
Canton: {canton} (official language for titles: {lang}). Question: {question}

1. "titles": 1-4 likely exact titles of THIS canton's acts that contain the answer, in {lang}
   (e.g. "Steuergesetz", "Planungs- und Baugesetz", "Hundegesetz", "Volksschulgesetz",
   "Loi sur les constructions et les installations diverses", "Loi sur les chiens", "Legge tributaria").
2. "stems": 2-4 lowercase word stems that appear inside such titles (e.g. "steuer", "bau", "hund", "schul",
   "impôt", "construction", "chien", "tribut", "ediliz").
Return ONLY JSON: {{"titles": [...], "stems": [...]}}"""

ACT_PROMPT = """Question from a resident of the canton of {canton}: {question}

Cantonal acts found in the canton's law collection:
{listing}

Which acts most likely contain the rules that answer the question? Prefer the canton's main law on the topic
(e.g. its tax act, building act, dog act, school act) and its main implementing ordinance.
Return ONLY a JSON list of up to {n} numbers from the list above, best first, e.g. [4, 1]."""

ARTICLE_PROMPT = """Question: {question}

Articles of the acts selected for this question, as [label] heading/first words:
{listing}

Which articles most directly answer the question? For amounts, fees, taxes, rates or times, include the
article or annex/tariff part (Anhang, Annexe, Allegato, Tarif) that lists the figures. Return ONLY a JSON list of up to {n} labels copied exactly
from the brackets, most relevant first, e.g. ["{example}"]. Return [] if none of them answers the question."""


def _json(raw, default):
    m = re.search(r"[\[{].*[\]}]", raw, re.S)
    if not m:
        return default
    try:
        return json.loads(re.sub(r",\s*([}\]])", r"\1", m.group(0)))
    except ValueError:
        return default


def write_queries(question, canton_name, lang_name):
    """Step 1 — runs in parallel with federal retrieval; returns LexFind query strings."""
    try:
        raw = apertus.chat([{"role": "user", "content": QUERY_PROMPT.format(
            canton=canton_name, lang=lang_name, question=question)}], temperature=0.0, max_tokens=200)
    except apertus.ApertusError:
        return []
    data = _json(raw, {})
    if not isinstance(data, dict):
        return []
    titles = [t.strip() for t in data.get("titles") or [] if isinstance(t, str) and len(t.strip()) >= 4][:4]
    stems = [re.sub(r"[^\wäöüàâçéèêëîïôûù-]", "", s.lower()) for s in data.get("stems") or [] if isinstance(s, str)]
    stems = [s for s in stems if len(s) >= 3][:4]
    return titles + [q for s in stems for q in (f"{s}*", f"*{s}*")]


def pick_acts(question, canton_name, candidates):
    """Step 2 — Apertus chooses among candidate titles; the heuristic order fills any gaps."""
    if len(candidates) <= MAX_TEXTS:
        return candidates
    listing = "\n".join(f"{i}. {t['sr']} — {t['title'][:140]} ({t.get('category', '')})" for i, t in enumerate(candidates, 1))
    try:
        raw = apertus.chat([{"role": "user", "content": ACT_PROMPT.format(
            canton=canton_name, question=question, listing=listing, n=MAX_TEXTS)}], temperature=0.0, max_tokens=60)
    except apertus.ApertusError:
        return None
    picks = _json(raw, [])
    if not isinstance(picks, list):
        picks = [int(x) for x in re.findall(r"\d+", raw)]
    chosen = [candidates[i - 1] for i in dict.fromkeys(p for p in picks if isinstance(p, int)) if 1 <= i <= len(candidates)]
    if not chosen:
        return None
    return (chosen[:MAX_TEXTS] + [c for c in candidates if c not in chosen])[:MAX_TEXTS]


def _heading(art):
    """'Art. 7 Leinen- und Maulkorbpflicht 1 Wer …' -> 'Leinen- und Maulkorbpflicht 1 Wer …' (first ~90 chars)."""
    body = art["text"][len(art["number"]):] if art["text"].startswith(art["number"]) else art["text"]
    return re.sub(r"\s+", " ", body).strip(" *")[:130]


def pick_articles(question, loaded, fallback_terms, topup=True):
    """Step 3 — Apertus reads article headings of the chosen acts; keyword ranking is the fallback."""
    items, index = [], {}
    for tol, arts in loaded:
        for art in arts[:150]:
            key = (tol["sr"], re.sub(r"\s+", "", art["number"]))
            # PDF splitting can repeat a heading (a contents page, or "§ 20" quoted inside another §):
            # keep the occurrence with the most text, which is the article itself.
            if key in index:
                if len(art["text"]) > len(items[index[key]][1]["text"]):
                    items[index[key]] = (tol, art)
                continue
            index[key] = len(items)
            items.append((tol, art))
    if not items:
        return []
    # Labels, not positions: on long lists the model's item numbers drift by one.
    def label(tol, art):
        return f"{tol['sr']} {re.sub(r'\s+', ' ', art['number'])}"

    def norm(x):
        return re.sub(r"[\s.]+", "", str(x)).lower()

    by_label = {norm(label(t, a)): (t, a) for t, a in items}
    listing = "\n".join(f"[{label(t, a)}] {_heading(a)}" for t, a in items)
    chosen = []
    answered = False  # did Apertus give a usable verdict (possibly "none of them")?
    try:
        raw = apertus.chat([{"role": "user", "content": ARTICLE_PROMPT.format(
            question=question, listing=listing[:24000], n=MAX_ARTICLES, example=label(*items[0]))}],
            temperature=0.0, max_tokens=200)
        picks = _json(raw, None)
        if not isinstance(picks, list):
            picks = re.findall(r'"([^"]+)"', raw)
        else:
            answered = True
        for p in picks:
            if isinstance(p, str):
                hit = by_label.get(norm(p))
            else:
                hit = items[p - 1] if isinstance(p, int) and 1 <= p <= len(items) else None
            if hit and hit not in chosen:
                chosen.append(hit)
        answered = answered and (bool(chosen) or not picks)
    except apertus.ApertusError:
        pass
    # Keyword top-up only when the model failed. When it read the headings and chose few (or none), padding
    # with keyword hits put unrelated cantonal provisions into answers (Opferhilfe for a slap, river law for damage).
    if topup and not answered and len(chosen) < MAX_ARTICLES:  # top up with keyword ranking
        have = {id(a) for _, a in chosen}
        pool = []
        for tol, arts in loaded:
            pool += [(tol, a) for a in sources.rank_articles(arts, fallback_terms, top=3)]
        pool.sort(key=lambda x: -x[1].get("score", 0))
        chosen += [(t, a) for t, a in pool if id(a) not in have and not any(a["number"] == c["number"] and t is ct for ct, c in chosen)]
    out, seen = [], set()
    for tol, art in chosen:
        if (tol["sr"], art["number"]) not in seen:
            seen.add((tol["sr"], art["number"]))
            out.append((tol, art))
    return out[:MAX_ARTICLES]


FED_PROMPT = """Question: {question}

Candidate articles of Swiss federal acts, as [label] heading/first words:
{listing}

Pick the articles a Swiss lawyer would cite to answer THIS question: the provision that states the governing rule
(conditions, figures, deadlines, authority), plus at most a few that add exceptions or procedure. Skip articles
about other situations, even from the same act, and skip acts on another subject that only share a word
(a mountain guide is not a driving "guida"; a building permit is not a residence permit).
Return ONLY a JSON list of up to {n} labels copied exactly from the brackets, most relevant first,
e.g. ["{example}"]. Return [] if none of them answers the question."""


def pick_federal(question, candidates, n=8):
    """Apertus chooses the governing federal articles among keyword- and planner-proposed candidates.

    candidates: [(act, version, art)], already deduplicated. Returns the chosen subset (best first) or None
    when the model is unavailable or picks nothing usable, so the caller keeps its keyword ranking.
    """
    if not candidates:
        return None

    def label(act, art):
        return f"{act['short'] or 'SR ' + act['sr']} art. {_artno(art['number'])}"

    by_label, lines = {}, []
    for c in candidates:
        lb = label(c[0], c[2])
        if re.sub(r"[\s.]+", "", lb).lower() in by_label:
            continue
        by_label[re.sub(r"[\s.]+", "", lb).lower()] = c
        lines.append(f"[{lb}] {re.sub(r'\s+', ' ', c[2]['number'])[:70]} · {_heading(c[2])[:80]}")
    try:
        raw = apertus.chat([{"role": "user", "content": FED_PROMPT.format(
            question=question, listing="\n".join(lines)[:22000], n=n,
            example=label(candidates[0][0], candidates[0][2]))}], temperature=0.0, max_tokens=160)
    except apertus.ApertusError:
        return None
    picks = _json(raw, None)
    if not isinstance(picks, list):
        picks = re.findall(r'"([^"]+)"', raw)
        if not picks:
            return None  # unreadable reply: the caller falls back to keyword ranking
    chosen = []
    for p in picks:
        hit = by_label.get(re.sub(r"[\s.]+", "", str(p)).lower())
        if hit and hit not in chosen:
            chosen.append(hit)
    if picks and not chosen:
        return None  # labels didn't match anything: treat as a failed pick, not as "nothing relevant"
    # [] is a verdict ("none of these answers it"), not a failure: keyword hits would only add noise.
    return chosen[:n]


def _artno(number):
    """'Art. 27 Contrôles médicaux' -> '27'; 'Art. 32abis' -> '32abis'."""
    m = re.match(r"(?i)\s*art\.?\s*(\d+\s?[a-z]{0,2}(?:bis|ter|quater|quinquies|sexies)?)", number)
    return re.sub(r"\s+", "", m.group(1)) if m else number.split(" ")[0]
