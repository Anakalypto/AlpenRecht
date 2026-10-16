"""Live Swiss legal sources: swisstopo (location), Fedlex (federal), LexFind (cantonal)."""
import hashlib
import html
import io
import json
import logging
import math
import time
import threading
import os
import re
import ssl
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import config

logging.getLogger("pypdf").setLevel(logging.ERROR)  # cantonal PDFs trigger harmless font warnings

BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36 "
              + config.USER_AGENT)

# Some commune sites (e.g. stadt-zuerich.ch) send incomplete chains that Windows' Python store can't verify.
try:
    import certifi
    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

# --------------------------------------------------------------------------- http + cache


def _cache_path(key, ext):
    return config.CACHE_DIR / f"{hashlib.sha1(key.encode()).hexdigest()[:20]}.{ext}"


def http(url, data=None, headers=None, timeout=60, cache=False):
    """GET/POST returning bytes. With cache=True the body is kept on disk (law texts are immutable per version)."""
    if cache:
        path = _cache_path(url + (data.decode() if data else ""), "bin")
        # One download per URL at a time: parallel questions used to read a half-written 2.6 MB Fedlex file.
        with _url_lock(str(path)):
            if path.exists():
                return path.read_bytes()
            body = http(url, data, headers, timeout, cache=False)
            tmp = path.with_suffix(f".{threading.get_ident()}.tmp")
            tmp.write_bytes(body)
            os.replace(tmp, path)  # atomic: readers see the whole file or none of it
            return body
    # "reglement-über-…" breaks urllib (ASCII only): percent-encode anything outside ASCII, keep the rest.
    url = urllib.parse.quote(url, safe=":/?&=%#+,;@!$'()*~[]")
    base = {"User-Agent": config.USER_AGENT, "Accept": "text/html,application/xhtml+xml,application/json,application/pdf,*/*;q=0.8",
            "Accept-Language": "de-CH,de;q=0.9,fr;q=0.8,it;q=0.7"}
    try:
        req = urllib.request.Request(url, data=data, headers={**base, **(headers or {})})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as r:
                    body = r.read()
                break
            except urllib.error.HTTPError:
                raise
            except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
                # A dropped connection or TLS handshake timeout (busy line, busy server) used to cost a whole level:
                # one failed swisstopo lookup meant no canton and no commune at all. Retry twice, then give up.
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
    except urllib.error.HTTPError as e:
        if e.code not in (403, 406):
            raise
        # Some commune sites refuse unknown clients; retry once as a browser that still names itself.
        req = urllib.request.Request(url, data=data, headers={**base, "User-Agent": BROWSER_UA, **(headers or {})})
        with urllib.request.urlopen(req, timeout=timeout, context=SSL_CONTEXT) as r:
            body = r.read()
    return body


_LOCKS = {}
_LOCKS_GUARD = threading.Lock()


def _url_lock(key):
    with _LOCKS_GUARD:
        return _LOCKS.setdefault(key, threading.Lock())


def http_json(url, payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Accept": "application/json"}
    if data:
        headers["Content-Type"] = "application/json"
    return json.loads(http(url, data, headers, timeout))


# --------------------------------------------------------------------------- cantons

# abbreviation -> (name, official languages, LexFind entity id)
CANTONS = {
    "ZH": ("Zürich", ["de"], 26), "BE": ("Bern / Berne", ["de", "fr"], 4), "LU": ("Luzern", ["de"], 12),
    "UR": ("Uri", ["de"], 22), "SZ": ("Schwyz", ["de"], 19), "OW": ("Obwalden", ["de"], 15),
    "NW": ("Nidwalden", ["de"], 14), "GL": ("Glarus", ["de"], 9), "ZG": ("Zug", ["de"], 25),
    "FR": ("Fribourg / Freiburg", ["fr", "de"], 7), "SO": ("Solothurn", ["de"], 18),
    "BS": ("Basel-Stadt", ["de"], 6), "BL": ("Basel-Landschaft", ["de"], 5),
    "SH": ("Schaffhausen", ["de"], 17), "AR": ("Appenzell Ausserrhoden", ["de"], 3),
    "AI": ("Appenzell Innerrhoden", ["de"], 2), "SG": ("St. Gallen", ["de"], 16),
    "GR": ("Graubünden / Grischun / Grigioni", ["de", "rm", "it"], 10), "AG": ("Aargau", ["de"], 1),
    "TG": ("Thurgau", ["de"], 20), "TI": ("Ticino", ["it"], 21), "VD": ("Vaud", ["fr"], 23),
    "VS": ("Valais / Wallis", ["fr", "de"], 24), "NE": ("Neuchâtel", ["fr"], 13),
    "GE": ("Genève", ["fr"], 8), "JU": ("Jura", ["fr"], 11),
}

# --------------------------------------------------------------------------- location (swisstopo)

GEO = "https://api3.geo.admin.ch/rest/services/api"


_POINT = re.compile(r"^\s*@?\s*(-?\d{1,2}\.\d+)\s*,\s*(-?\d{1,2}\.\d+)\s*$")


def commune_at(lat, lon, geometry=False):
    """A point picked on the map (WGS84) -> commune, BFS number, canton (optionally its boundary as GeoJSON)."""
    q = urllib.parse.urlencode({
        "geometryType": "esriGeometryPoint", "geometry": f"{lon},{lat}", "sr": 4326, "tolerance": 0,
        "layers": "all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill",
        "returnGeometry": "true" if geometry else "false", "geometryFormat": "geojson"})
    feats = http_json(f"{GEO}/MapServer/identify?{q}").get("results", [])
    if not feats:
        return None  # outside Switzerland (or on a lake without a commune)
    feat = max(feats, key=lambda f: (f.get("attributes", f.get("properties", {})).get("is_current_jahr", False),
                                     f.get("attributes", f.get("properties", {})).get("jahr", 0)))
    attr = feat.get("attributes") or feat.get("properties")
    name, langs, _ = CANTONS[attr["kanton"]]
    label = attr["gemname"] if "(" in attr["gemname"] else f"{attr['gemname']} ({attr['kanton']})"  # "Ecublens (VD)"
    out = {"label": label, "commune": attr["gemname"], "bfs": attr["gde_nr"],
           "canton": attr["kanton"], "canton_name": name, "canton_languages": langs, "lat": lat, "lon": lon}
    if geometry and feat.get("geometry"):
        out["geometry"] = feat["geometry"]
    return out


def resolve_location(text):
    """Map point ("@46.53,6.57"), address, place, postcode or commune name -> commune, BFS number, canton."""
    point = _POINT.match(text or "")
    if point:
        return commune_at(float(point.group(1)), float(point.group(2)))
    hits = []
    # "1950 Sion": a postcode's centre point can lie in a neighbouring commune (Grimisuat), so when the text
    # names a commune, resolve the commune itself first. Street addresses keep the precise address match.
    name = re.sub(r"\b\d{4}\b|,", " ", text).strip()
    if name and not re.search(r"\d", name):
        q = urllib.parse.urlencode({"searchText": name, "type": "locations", "limit": 3, "sr": 2056, "origins": "gg25"})
        target = fold(name.split("(")[0].strip())
        hits = [h for h in http_json(f"{GEO}/SearchServer?{q}").get("results", [])
                if fold(re.sub(r"<[^>]+>|\s*\([A-Z]{2}\)", "", h["attrs"].get("label", ""))).strip() == target][:1]
    if not hits:
        q = urllib.parse.urlencode({"searchText": text, "type": "locations", "limit": 1, "sr": 2056,
                                    "origins": "address,gg25,zipcode,gazetteer"})
        hits = http_json(f"{GEO}/SearchServer?{q}").get("results", [])
    if not hits:
        return None
    a = hits[0]["attrs"]
    east, north = a["y"], a["x"]  # swisstopo swaps x/y in LV95 search results
    q = urllib.parse.urlencode({
        "geometryType": "esriGeometryPoint", "geometry": f"{east},{north}", "sr": 2056, "tolerance": 0,
        "layers": "all:ch.swisstopo.swissboundaries3d-gemeinde-flaeche.fill", "returnGeometry": "false"})
    feats = http_json(f"{GEO}/MapServer/identify?{q}").get("results", [])
    if not feats:
        return None
    feat = max(feats, key=lambda f: (f["attributes"].get("is_current_jahr", False), f["attributes"].get("jahr", 0)))
    attr = feat["attributes"]
    canton = attr["kanton"]
    name, langs, _ = CANTONS[canton]
    return {
        "label": re.sub(r"<[^>]+>", "", a.get("label", text)),
        "commune": attr["gemname"], "bfs": attr["gde_nr"],
        "canton": canton, "canton_name": name, "canton_languages": langs,
        "lat": a.get("lat"), "lon": a.get("lon"),
    }


def suggest_locations(text, limit=6):
    q = urllib.parse.urlencode({"searchText": text, "type": "locations", "limit": limit,
                                "origins": "address,gg25,zipcode"})
    return [re.sub(r"<[^>]+>", "", h["attrs"]["label"]) for h in http_json(f"{GEO}/SearchServer?{q}").get("results", [])]


# --------------------------------------------------------------------------- text helpers


def fold(s):
    """Lowercase, strip accents: 'Kündigung' -> 'kundigung'."""
    return "".join(c for c in unicodedata.normalize("NFKD", s.lower()) if not unicodedata.combining(c))


def strip_tags(fragment):
    fragment = re.sub(r"<sup>\s*<a[^>]*>.*?</a>\s*</sup>", "", fragment, flags=re.S)  # footnote markers
    fragment = re.sub(r"<(br|/p|/div|/li|/h\d)[^>]*>", "\n", fragment)
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", text)).strip()


# --------------------------------------------------------------------------- Fedlex (federal law)

SPARQL = "https://fedlex.data.admin.ch/sparqlendpoint"
LANG_URI = {"de": "DEU", "fr": "FRA", "it": "ITA", "rm": "ROH", "en": "ENG"}
PREFIX = """PREFIX jolux: <http://data.legilux.public.lu/resource/ontology/jolux#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
"""
IN_FORCE = "<https://fedlex.data.admin.ch/vocabulary/enforcement-status/0>"


def sparql(query):
    body = urllib.parse.urlencode({"query": PREFIX + query}).encode()
    data = http(SPARQL, body, {"Accept": "application/sparql-results+json",
                               "Content-Type": "application/x-www-form-urlencoded"}, timeout=60)
    return [{k: v["value"] for k, v in row.items()} for row in json.loads(data)["results"]["bindings"]]


def _lang_literal(lang):
    return f"<http://publications.europa.eu/resource/authority/language/{LANG_URI.get(lang, 'DEU')}>"


def fedlex_find_acts(sr_numbers=(), title_terms=(), lang="de", limit=10):
    """In-force federal acts by SR number and/or title words."""
    conds = []
    if sr_numbers:
        conds.append("STR(?sr) IN (" + ", ".join(json.dumps(s) for s in sr_numbers) + ")")
    for t in title_terms:
        # Word-start match: "hund" finds "Hundegesetz" but "meinen" no longer finds "Allgemeinen".
        t = re.sub(r"[^\w\s-]", "", t.strip().lower())
        if len(t) >= 3:
            conds.append(f'REGEX(STR(?title), "(^|[ (/-]){t}", "i")')
    if not conds:
        return []
    rows = sparql(f"""
SELECT DISTINCT ?act ?sr ?title ?short WHERE {{
  ?act a jolux:ConsolidationAbstract ; jolux:inForceStatus {IN_FORCE} ;
       jolux:classifiedByTaxonomyEntry/skos:notation ?sr ; jolux:isRealizedBy ?e .
  ?e jolux:language {_lang_literal(lang)} ; jolux:title ?title .
  OPTIONAL {{ ?e jolux:titleShort ?short }}
  FILTER({" || ".join(conds)})
}} LIMIT 60""")
    seen, acts = set(), []
    for r in rows:
        if r["act"] in seen:
            continue
        seen.add(r["act"])
        acts.append({"act": r["act"], "sr": r["sr"], "title": r["title"], "short": r.get("short", "")})

    # Explicit SR hits first, then main laws (short SR numbers) before departmental ordinances.
    def rank(a):
        hit = a["sr"] in sr_numbers
        terms_hit = sum(fold(t) in fold(a["title"]) for t in title_terms)
        return (not hit, -terms_hit, len(a["sr"]), a["sr"])

    return sorted(acts, key=rank)[:limit]


def fedlex_version(act, asof, lang="de"):
    """The consolidation applicable on `asof` (YYYY-MM-DD) and its HTML file."""
    for try_lang in dict.fromkeys([lang, "de", "fr", "it"]):
        rows = sparql(f"""
SELECT ?c ?d ?file WHERE {{
  ?c jolux:isMemberOf <{act}> ; jolux:dateApplicability ?d ; jolux:isRealizedBy ?e .
  FILTER(?d <= "{asof}"^^xsd:date)
  ?e jolux:language {_lang_literal(try_lang)} ; jolux:isEmbodiedBy ?m .
  ?m jolux:isExemplifiedBy ?file .
  FILTER(CONTAINS(STR(?m), "/html"))
}} ORDER BY DESC(?d) LIMIT 1""")
        if rows:
            r = rows[0]
            return {"consolidation": r["c"], "date": r["d"], "file": r["file"], "lang": try_lang}
    return None


_ARTICLE = re.compile(r'<article id="(art_[^"]+)">(.*?)</article>', re.S)
_HEADING = re.compile(r'<(div|h[1-6]) class="heading" role="heading" aria-level="(\d+)">(.*?)</\1>', re.S)


def parse_fedlex_html(raw):
    """Split a Fedlex consolidation into articles, each with its section breadcrumb."""
    doc = raw.decode("utf-8", "replace")
    headings = [(m.start(), int(m.group(2)), re.sub(r"\s+", " ", strip_tags(m.group(3))))
                for m in _HEADING.finditer(doc)]
    articles, stack, hi = [], {}, 0
    for m in _ARTICLE.finditer(doc):
        while hi < len(headings) and headings[hi][0] < m.start():
            _, level, title = headings[hi]
            stack = {k: v for k, v in stack.items() if k < level}
            stack[level] = title
            hi += 1
        body = m.group(2)
        h = re.search(r"<h6[^>]*>(.*?)</h6>", body, re.S)
        number = strip_tags(h.group(1)) if h else m.group(1)
        text = strip_tags(re.sub(r"<h6[^>]*>.*?</h6>", "", body, count=1, flags=re.S))
        if not text or text.startswith("Aufgehoben") or text.startswith("Abrogé") or text.startswith("Abrogato"):
            continue
        articles.append({"anchor": m.group(1), "number": number, "path": " › ".join(stack[k] for k in sorted(stack)),
                         "text": text})
    # Annexes (<section id="annex_N">) hold tariffs, fee tables and lists; they were never parsed, so a federal fee
    # ordinance contributed its articles but not a single amount. Long annexes are kept in parts.
    marks = [(m.start(), m.group(1)) for m in re.finditer(r'<section id="annex_(\d+)">', doc)]
    for i, (start, n) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(doc)
        text = re.sub(r"[ \t]+", " ", strip_tags(doc[start:end])).strip()
        text = re.sub(r"\n\s*\n+", "\n", text)
        if len(text) < 40:
            continue
        head = re.match(r"(Anhang|Annexe|Allegato|Annex)\s*\d*", text)
        number = head.group(0) if head else f"Anhang {n}"
        for j in range(0, len(text), ART_MAX - 300):
            # Parts need their own anchor (candidates are de-duplicated by anchor); the link drops the "~k" again.
            articles.append({"anchor": f"annex_{n}" + (f"~{j}" if j else ""), "number": number if j == 0 else f"{number} ({j // (ART_MAX - 300) + 1})",
                             "path": number, "text": text[j:j + ART_MAX]})
            if j + ART_MAX >= len(text):
                break
    return articles


def fedlex_articles(act_info, asof, lang):
    version = None
    for attempt in range(3):  # the SPARQL endpoint occasionally fails under parallel load
        try:
            version = fedlex_version(act_info["act"], asof, lang)
            break
        except Exception:
            time.sleep(1.5 * (attempt + 1))
    if not version:
        return None, []
    raw = http(version["file"], timeout=90, cache=True)
    eli = act_info["act"].replace("https://fedlex.data.admin.ch/", "")
    base = f"https://www.fedlex.admin.ch/{eli}/{version['lang']}"
    arts = parse_fedlex_html(raw)
    for a in arts:
        a["url"] = f"{base}#{a['anchor'].split('~')[0]}"
    return version, arts


# --------------------------------------------------------------------------- LexFind (cantonal law)

LEXFIND = "https://www.lexfind.ch"


def lexfind_search(text, canton, lang="de", content=False, limit=8):
    entity = CANTONS[canton][2]
    search = {"search_text": text, "active_only": True, "search_in_systematic_number": False,
              "search_in_title": True, "search_in_keywords": True, "search_in_content": content,
              "entity_filter": [entity], "systematic_filter": [], "category_filter": [],
              "use_global_systematics": False, "direct_search": False}
    created = http_json(f"{LEXFIND}/api/frontend/v1/{lang}/fulltext-search", search)
    q = urllib.parse.urlencode({"session_id": created["session_id"], "page_no": 1,
                                "results_per_page": limit, "result_lang": lang})
    res = http_json(f"{LEXFIND}/api/frontend/v1/{lang}/fulltext-search/{created['id']}?{q}")
    out = []
    for tol in res.get("texts_of_law_with_matches", []):
        match = (tol.get("matches") or [{}])[0]
        urls = {u["language"]: u for u in tol.get("dta_urls", [])}
        out.append({
            "tol_id": tol["id"], "sr": tol.get("systematic_number", ""), "title": match.get("title", ""),
            "category": (match.get("category") or {}).get("name", ""),
            "since": match.get("version_active_since"), "urls": urls,
            "snippet": strip_tags(match.get("snippet") or ""),
        })
    return out


_ART_START = re.compile(
    r"^\s*(?:§\s*\d+[a-z]?|Art(?:\.|icle|icolo)?\s*\d+[a-z]*(?:\s*(?:bis|ter|quater))?)\b", re.M | re.I)


_ART_INLINE = re.compile(
    r"(?:^|(?<=[.:;)]\s))"
    r"((?:§\s*\d+[a-z]?|Art(?:\.|icle|icolo)?\s*\d+[a-z]*)(?=\s+[A-ZÄÖÜÉÈ]))")


_ANNEX_START = re.compile(
    r"^\s*(?:Anhang|Anh[äa]nge|Annexe|Annexes|Allegato|Allegati|Tarif(?:ordnung|e)?|Geb[üu]hrentarif|Taxordnung|Tabelle|"
    r"Bar[èe]me|Tariffa|Tariffario)\b[^\n]{0,80}$", re.M | re.I)
ART_MAX = 3500


def _annexes(text):
    """Fee amounts mostly sit in annexes and tariff tables after the last article. Before, they were glued to the last
    article and cut off at 2,500 characters, so 'Hundetaxe CHF 120' never reached the model. -> [(start, label)]"""
    out = []
    for m in _ANNEX_START.finditer(text):
        label = re.sub(r"\s+", " ", m.group(0)).strip()[:60]
        # A reference like "Tarif gemäss Art. 5" inside an article is not a heading: require a short line.
        if len(label) <= 60 and not re.search(r"\b(?:gem[äa]ss|selon|secondo|nach|gestützt)\b", label, re.I):
            out.append((m.start(), label))
    return out


def split_articles(text):
    """Cantonal/communal texts come as PDFs: cut at 'Art. 12', 'Article 3', '§ 5' line starts, and at annex/tariff
    headings. Long pieces (tariff tables) are kept in several parts instead of being truncated."""
    arts = _split_articles(text)
    out = []
    for a in arts:
        body = a["text"]
        if len(body) <= ART_MAX:
            out.append(a)
            continue
        for i in range(0, len(body), ART_MAX - 300):
            part = body[i:i + ART_MAX]
            out.append({"number": a["number"] if i == 0 else f"{a['number']} ({i // (ART_MAX - 300) + 1})",
                        "path": a["path"], "text": part if i == 0 else f"{a['number']} (…) {part}"})
            if i + ART_MAX >= len(body):
                break
    return out


def _split_articles(text):
    text = re.sub(r"[ \t]+", " ", text.replace("\xa0", " "))
    starts = [m.start() for m in _ART_START.finditer(text)]
    # PDFs that lost their line breaks put headings inline: "… zu bringen. § 3 Vollzug 1 Sowohl …".
    # A marker right after a sentence end and before a capitalised heading is a new article;
    # references ("gestützt auf § 35 des …") are followed by lowercase words and stay put.
    inline = [m.start(1) for m in _ART_INLINE.finditer(text)]
    if len(inline) > 2 * max(len(starts), 1):
        # Chapter headings end a section too: "III. Finanzielle § 13 Gebühren" -> "III. Finanzielle. § 13 Gebühren"
        text = re.sub(r"(\b[IVX]{1,4}\.\s+[A-ZÄÖÜ][^.§\n]{0,60}?)\s(§\s*\d|Art\.\s*\d)", r"\1. \2", text)
        starts = [m.start() for m in _ART_START.finditer(text)]
        inline = [m.start(1) for m in _ART_INLINE.finditer(text)]
        starts = sorted(set(starts) | set(inline))
    if len(starts) < 3:  # no usable structure: fixed-size chunks
        chunks = [text[i:i + 1400] for i in range(0, len(text), 1200)]
        # "Teil 1", not "§1": a made-up section number was cited as if the regulation had a § 1.
        return [{"number": f"Teil {i + 1}", "path": "", "text": c.strip()} for i, c in enumerate(chunks) if c.strip()]
    # Annexes only count after the first article (a table of contents or preamble can mention "Anhang").
    annex = [(p, lb) for p, lb in _annexes(text) if p > starts[0]]
    labels = dict(annex)
    starts = sorted(set(starts) | {p for p, _ in annex})
    arts = []
    for i, s in enumerate(starts):
        chunk = text[s:starts[i + 1] if i + 1 < len(starts) else len(text)].strip()
        if s in labels:
            number = labels[s]
        else:
            m = _ART_START.match(chunk) or re.match(r"§\s*\d+[a-z]?|Art(?:\.|icle|icolo)?\s*\d+[a-z]*", chunk)
            number = m.group(0).strip() if m else chunk[:8]
        if re.search(r"\.{5,}|…{2,}|(?:\. ){4,}", chunk[:200]) and len(chunk) < 250:
            continue  # table-of-contents line ("Art. 35 Grabesruhe ........ 12"), the real article comes later
        arts.append({"number": number, "path": "", "text": chunk[:12000]})
    return arts


def pdf_or_html_text(raw, ocr=True):
    if raw[:5] == b"%PDF-":
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        if ocr and (len(text.strip()) < 40 * len(reader.pages) or _garbled(text)):
            # Scanned document without a text layer, or a broken font encoding that extracts as "# $) (.$*!":
            # either way Apertus reads the page images instead.
            text = ocr_pdf(raw) or text
        elif _articles_broken(text):
            # Two-column layouts (article label in the margin) come out as a block of "Art. N" labels
            # followed by the text; layout mode keeps each label on the line of its article.
            layout = "\n".join((p.extract_text(extraction_mode="layout") or "") for p in reader.pages)
            layout = re.sub(r"[ \t]{2,}", " ", layout)
            if not _articles_broken(layout):
                text = layout
        # Re-join words hyphenated across lines ("bestosse -\nne" -> "bestossene"), keep "Jagd- und".
        return re.sub(r"(\w) ?- ?\n\s*([a-zäöüéèàç])", r"\1\2", text)
    return strip_tags(raw.decode("utf-8", "replace"))


def _garbled(text):
    """True when extracted text is mostly symbols rather than words (PDFs with unmapped font encodings)."""
    sample = text[:20000]
    visible = [c for c in sample if not c.isspace()]
    if len(visible) < 500:
        return False
    letters = sum(c.isalpha() for c in visible)
    words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", sample)
    vowelled = sum(bool(re.search(r"[aeiouyäöüéèàâêîôû]", w, re.I)) for w in words)
    return letters / len(visible) < 0.6 or (len(words) > 20 and vowelled / len(words) < 0.7)


def _articles_broken(text):
    """True when most articles split out of a text are empty labels (typical of two-column PDFs)."""
    arts = split_articles(text)
    if len(arts) < 6:
        return False
    empty = sum(len(a["text"]) - len(a["number"]) < 30 for a in arts)
    return empty / len(arts) > 0.4


OCR_PROMPT = ("Transcribe all text on this scanned page of a Swiss regulation exactly, preserving article numbers "
              "(Art. 12, § 3) at the start of their lines and the line breaks. Output only the text.")


def ocr_pdf(raw, max_pages=40):
    """Scanned regulations (common for older communal law): Apertus reads the page images."""
    try:
        import base64
        import pypdfium2 as pdfium
        import apertus
    except ImportError:
        return ""
    # PDFium is not thread-safe: render every page image first, then transcribe them in parallel.
    pdf = pdfium.PdfDocument(raw)
    images = []
    for i in range(min(len(pdf), max_pages)):
        buf = io.BytesIO()
        pdf[i].render(scale=1.6).to_pil().convert("L").save(buf, format="JPEG", quality=70)
        images.append("data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode())
    pdf.close()

    def page_text(url):
        try:
            return apertus.chat([{"role": "user", "content": [{"type": "text", "text": OCR_PROMPT},
                                                              {"type": "image_url", "image_url": {"url": url}}]}],
                                temperature=0.0, max_tokens=1800, model=config.OCR_MODEL)
        except Exception:
            return ""

    return "\n".join(parallel(page_text, images, workers=6))


def lexfind_articles(tol, lang):
    pick = tol["urls"].get(lang) or next(iter(tol["urls"].values()), None)
    if not pick:
        return []
    # Parsing a 200-page tax act with pypdf takes ~10 s, so keep the extracted text too, not just the PDF.
    txt_cache = _cache_path(LEXFIND + pick["url"], "txt")
    if txt_cache.exists():
        text = txt_cache.read_text(encoding="utf-8")
    else:
        text = pdf_or_html_text(http(LEXFIND + pick["url"], timeout=90, cache=True))
        txt_cache.write_text(text, encoding="utf-8")
    arts = split_articles(text)
    for a in arts:
        a["url"] = pick.get("original_url") or LEXFIND + pick["url"]
    return arts


# --------------------------------------------------------------------------- ranking


def _stem(term):
    t = fold(term)
    return t[:max(5, len(t) - 2)] if len(t) > 6 else t


def rank_articles(articles, terms, top=6):
    """Light BM25-ish scoring with prefix stems, so 'Kündigung' also hits 'Kündigungsfrist'."""
    stems = list(dict.fromkeys(_stem(t) for t in terms if len(t) >= 3))
    if not stems or not articles:
        return []
    docs = [fold(a["text"]) for a in articles]
    paths = [fold(a.get("path", "")) for a in articles]
    n = len(docs)
    df = {s: sum(s in d or s in p for d, p in zip(docs, paths)) for s in stems}
    scored = []
    for a, d, p in zip(articles, docs, paths):
        score = 0.0
        for s in stems:
            if not df[s]:
                continue
            idf = math.log(1 + n / df[s])
            tf = d.count(s)
            score += idf * (math.log(1 + tf) + (1.5 if s in p else 0))
        if score > 0:
            scored.append((score / (1 + len(d) / 4000), a))
    scored.sort(key=lambda x: -x[0])
    return [dict(a, score=round(sc, 2)) for sc, a in scored[:top]]


def parallel(fn, items, workers=4):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, items))
