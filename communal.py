"""Communal law, found automatically: there is no central collection of Swiss municipal regulations.

  1. website  — Wikidata maps the commune's BFS number (from swisstopo) to its official website;
  2. index    — find the commune's regulations page (homepage links, common CMS paths, sitemap);
  3. documents— list regulation titles + links; many communes run a CMS that embeds the list as JSON;
  4. pick     — Apertus chooses the regulations that answer the question, then the articles inside them.

Crawls are cached per commune for a week; every request identifies itself and stays on the commune's own site.
"""
import html
import json
import re
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

import apertus
import cities
import config
import lexfind_agent
import sources

CACHE = config.CACHE_DIR / "communes"
CACHE.mkdir(exist_ok=True)
WEEK = 7 * 24 * 3600
MAX_DOCS = 3

# Words that mark regulation index pages and regulation titles, in the four national languages.
INDEX_WORDS = re.compile(
    r"reglement|rechtssammlung|gesetzessammlung|erlass|rechtserlass|verordnungen|rechtsgrundlag|vorschriften|"
    r"règlement|reglements|recueil|bases?[ -]l[ée]gales?|textes? l[ée]gaux|"
    r"regolament|raccolta|basi legali|leggi e regolamenti|ordinanz", re.I)
DOC_WORDS = re.compile(
    r"reglement|verordnung|ordnung|statut|tarif|gesetz|vorschrift|richtlinie|weisung|"
    r"règlement|ordonnance|statuts|directive|arrêté|tarif|"
    r"regolamento|ordinanza|statuto|direttiva|tariffa", re.I)
COMMON_PATHS = ["/reglemente", "/rechtssammlung", "/gesetzessammlung", "/erlasse", "/rechtserlasse", "/_rtr/reglemente",
                "/reglements", "/reglement", "/reglements-communaux", "/regolamenti", "/politik-verwaltung/reglemente"]
NAV_WORDS = re.compile(
    r"politik|verwaltung|recht|stadtrecht|gemeinde|behörde|officiel|administration|autorités|politique|"
    r"amministrazione|politica|istituzion|legal|reglement|règlement|regolament", re.I)
SKIP = re.compile(r"\.(?:jpe?g|png|gif|svg|zip|docx?|xlsx?|mp4)(?:$|\?)|mailto:|tel:|javascript:|facebook|instagram|"
                  r"linkedin|twitter|youtube|/login|/jobs|stellen|emploi|lavoro", re.I)

PICK_PROMPT = """Question from a resident of {commune} (canton {canton}): {question}

Regulations published by the commune of {commune}:
{listing}

Which of these communal regulations most likely contain rules that answer the question?
Know where Swiss communes put things: the general police regulation (Polizeireglement / Polizeiverordnung /
règlement (général) de police / regolamento di polizia) covers quiet hours, noise, dogs in public, public order
and use of public space; waste rules sit in the waste regulation (Abfallreglement / règlement sur la gestion des
déchets); fees in fee or tariff regulations (Gebührenreglement / tarif); building rules in the building and zoning
regulation (Baureglement / règlement communal sur les constructions / regolamento edilizio); graves in the burial
regulation (Bestattungs- und Friedhofreglement / règlement des inhumations et cimetières).
A regulation on the police FORCE (règlement du corps de police, Dienstreglement der Stadtpolizei, its charter or ethics
committee) is about the police staff, not rules for residents: prefer the general police regulation.
Pick a regulation only if its title fits the question's topic; an unrelated fee or building regulation is worse than none.
Return ONLY a JSON list of up to {n} titles copied exactly from the list, best first,
e.g. ["Règlement de police", "Tarif des émoluments"]. Return [] if none fits."""


# --------------------------------------------------------------------------- website (Wikidata)

_SITES = None


def _best(sites):
    # Prefer the bare homepage over language variants (".../fr", ".../en").
    return sorted(sites, key=lambda s: (bool(re.search(r"/(?:de|fr|it|en)/?$", s)), len(s)))[0] if sites else None


def website(bfs):
    """Official website of a commune by BFS number: shipped table first (data/communes.json), live Wikidata second."""
    global _SITES
    if _SITES is None:
        path = config.ROOT / "data" / "communes.json"
        # 33 keys are zero-padded ("0198" Uster) while swisstopo BFS numbers aren't: normalise both sides.
        _SITES = {str(int(k)) if k.isdigit() else k: v for k, v in
                  (json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}).items()}
    if str(bfs) in _SITES:
        return _SITES[str(bfs)]
    q = f'SELECT ?site WHERE {{ ?item wdt:P771 "{int(bfs)}" ; wdt:P856 ?site . }}'
    url = "https://query.wikidata.org/sparql?" + urllib.parse.urlencode({"query": q, "format": "json"})
    try:
        rows = json.loads(sources.http(url, headers={"Accept": "application/sparql-results+json"}, timeout=20))
    except Exception:
        return None  # rate-limited or down: try again next time, never cache the failure
    site = _best([b["site"]["value"] for b in rows["results"]["bindings"]])
    _SITES[str(bfs)] = site
    return site


# --------------------------------------------------------------------------- crawling

_LAST_HIT = {}
_HIT_LOCK = threading.Lock()
MIN_INTERVAL = 0.6  # seconds between requests to the same commune site


def _get(url):
    """Polite fetch: one request per ~0.6 s per host, and one patient retry when the site says 429."""
    host = urllib.parse.urlparse(url).netloc.lower()
    for attempt in range(2):
        with _HIT_LOCK:
            wait = _LAST_HIT.get(host, 0) + MIN_INTERVAL - time.time()
            _LAST_HIT[host] = time.time() + max(wait, 0)
        if wait > 0:
            time.sleep(wait)
        try:
            return sources.http(url, headers={"Accept-Language": "de,fr,it;q=0.8"}, timeout=25)
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt:
                raise
            retry = e.headers.get("Retry-After", "3")
            time.sleep(min(float(retry) if retry.replace(".", "").isdigit() else 3.0, 5.0))


def _links(base, raw):
    """Anchors from the page, including anchors embedded as escaped HTML inside JSON attributes (CMS lists)."""
    page = raw.decode("utf-8", "replace")
    # Relative links resolve against <base href> when the page declares one (else e.g. Rickenbach's PDFs 404).
    declared = re.search(r'<base\b[^>]*href="([^"]+)"', page, re.I)
    if declared:
        base = urllib.parse.urljoin(base, html.unescape(declared.group(1)))
    expanded = html.unescape(page).replace("\\/", "/").replace('\\"', '"')
    expanded = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), expanded)
    out, seen = [], set()
    for src in (page, expanded):
        for m in re.finditer(r'<a\b[^>]*?href="([^"#]+)"[^>]*>(.*?)</a>', src, re.S | re.I):
            href = urllib.parse.urljoin(base, html.unescape(m.group(1)).strip())
            text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", m.group(2)))).strip()
            if href not in seen and not SKIP.search(href):
                seen.add(href)
                out.append((href, text))
    return out


def _same_site(url, host):
    h = urllib.parse.urlparse(url).netloc.lower()
    return h == host or h.endswith("." + host.split("www.", 1)[-1])


def _is_doc_link(url):
    u = url.lower()
    path = urllib.parse.urlparse(u).path  # ".pdf?fp=1" still a PDF
    return path.endswith(".pdf") or "/_doc/" in u or "/_docn/" in u or "/_rte/publikation/" in u or "download" in u


def _sitemap_urls(root, limit=4000):
    """URLs from /sitemap.xml (one level of nested sitemaps)."""
    loc = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>")
    try:
        xml = _get(root + "/sitemap.xml").decode("utf-8", "replace")
    except Exception:
        return []
    locs = loc.findall(xml)
    if "<sitemapindex" not in xml:
        return locs[:limit]
    out = []
    for sub in locs[:4]:
        try:
            out += loc.findall(_get(sub).decode("utf-8", "replace"))
        except Exception:
            continue
    return out[:limit]


def tlex_documents(host):
    """Communes on TLex (<commune>.tlex.ch, the vendor behind LexFind) expose their whole collection as JSON."""
    for lang in ("de", "fr", "it"):
        try:
            index = json.loads(sources.http(f"https://{host}/api/{lang}/texts_of_law/lightweight_index?show_abrogated=false",
                                            headers={"Accept": "application/json"}, timeout=20))
        except Exception:
            continue
        docs = [{"title": f"{t.get('systematic_number', '')} {t.get('title', '')}".strip(),
                 "url": f"https://{host}/api/{lang}/texts_of_law/{urllib.parse.quote(t['systematic_number'])}/show_as_json"}
                for group in (index.values() if isinstance(index, dict) else [index]) for t in group
                if isinstance(t, dict) and t.get("systematic_number") and not t.get("abrogated")]
        if docs:
            return docs
    return []


def _tlex_hosts(site, links):
    """TLex hosts linked from the site, plus the usual guess <commune>.tlex.ch."""
    hosts = {urllib.parse.urlparse(u).netloc.lower() for u, _ in links if ".tlex.ch" in u.lower()}
    base = urllib.parse.urlparse(site).netloc.lower().removeprefix("www.").split(".")[0]
    hosts.add(f"{base}.tlex.ch")
    return sorted(hosts)


def find_documents(site):
    """Crawl the commune's site for its regulations: [{title, url}]. Cached for a week.

    Index pages are found on the homepage, one navigation level down ("Politik & Verwaltung", "Officiel"…),
    in the sitemap and at common CMS paths; legal-collection subdomains (stadtrecht.bern.ch) count as the site.
    """
    host = urllib.parse.urlparse(site).netloc.lower()
    cache = CACHE / f"docs-{host}.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < WEEK:
        return json.loads(cache.read_text(encoding="utf-8"))

    try:
        home = _get(site)
    except Exception:
        return []  # site down: don't cache, try again next time
    root = f"{urllib.parse.urlparse(site).scheme}://{host}"
    path_of = lambda u: urllib.parse.urlparse(u).path  # noqa: E731
    all_links = _links(site, home)
    links = [(u, t) for u, t in all_links if _same_site(u, host)]
    index = [u for u, t in links if INDEX_WORDS.search(t + " " + path_of(u)) and not _is_doc_link(u)]
    # Only go one level deeper when the homepage doesn't already link the collection (fewer requests, no 429s).
    nav = [] if index else [u for u, t in links if NAV_WORDS.search(t + " " + path_of(u)) and u not in index][:6]
    for u in nav:  # second level: the legal collection usually sits under politics / administration
        try:
            level2 = _links(u, _get(u))
        except Exception:
            continue
        all_links += level2
        index += [v for v, t in level2 if _same_site(v, host) and INDEX_WORDS.search(t + " " + path_of(v))
                  and not _is_doc_link(v)]
    # Pages titled "Rechtssammlung" often just redirect to a TLex collection: follow them to find it.
    for u in [u for u in index if re.search(r"rechtssammlung|gesetzessammlung|erlass", u, re.I)][:2]:
        try:
            req = urllib.request.Request(u, headers={"User-Agent": config.USER_AGENT})
            with urllib.request.urlopen(req, timeout=15, context=sources.SSL_CONTEXT) as r:
                all_links.append((r.geturl(), ""))
                all_links += _links(r.geturl(), r.read(2_000_000))
        except Exception:
            continue
    tlex = []
    for th in _tlex_hosts(site, all_links):
        tlex = tlex_documents(th)
        if tlex:
            break
    sitemap = _sitemap_urls(root)
    # Sitemaps often list the regulation PDFs themselves: use those as documents, titled from the file name.
    sitemap_docs = [{"title": _title_from_url(u), "url": u} for u in sitemap
                    if _is_doc_link(u) and DOC_WORDS.search(urllib.parse.unquote(path_of(u)))][:200]
    index += [u for u in sitemap if INDEX_WORDS.search(path_of(u)) and not _is_doc_link(u)][:10]
    index += [root + p for p in COMMON_PATHS]
    # Keep discovery order (homepage → navigation → sitemap → common paths): the commune's own link to its
    # collection is the best lead; sorting by URL shape sent the crawl into sub-pages first.
    index = list(dict.fromkeys(index))

    docs, seen, visited = [], set(), 0
    for url in index:
        if visited >= 8 or len(docs) >= 400:
            break
        try:
            raw = _get(url)
        except Exception:
            continue
        visited += 1
        for href, text in _links(url, raw):
            if not text or len(text) < 6 or href in seen or href == url:
                continue
            titled = DOC_WORDS.search(text)
            if (_is_doc_link(href) and (titled or DOC_WORDS.search(href))) or \
               (titled and _same_site(href, host) and len(text) > 12):
                seen.add(href)
                docs.append({"title": text[:160], "url": href})
    # A TLex collection is complete and structured: list it first, crawled documents after it.
    # Regulation PDFs linked straight from the homepage or navigation pages are documents too.
    direct = [{"title": t or _title_from_url(u), "url": u} for u, t in all_links
              if _same_site(u, host) and _is_doc_link(u) and DOC_WORDS.search(t + " " + urllib.parse.unquote(path_of(u)))]
    known = {d["url"] for d in docs}
    for d in sitemap_docs + direct:
        if d["url"] not in known:
            known.add(d["url"])
            docs.append(d)
    docs = tlex + [d for d in docs if d["url"] not in {t["url"] for t in tlex}]
    for d in docs:
        d["title"] = clean_title(d["title"])
    cache.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
    return docs


_TITLE_NOISE = [r"^(?:path|pdf|download|dokument|document|datei|fichier|file)\s+", r"\.pdf\b", r"\(\s*pdf[^)]*\)",
                r"\b\d+(?:[.,]\d+)?\s?(?:kb|mb|ko|mo)\b", r"\bjpe?g\b", r"\btéléchargement\b",
                r"\bherunterladen\b", r"\s{2,}"]


def _title_from_url(url):
    """'/Reglemente/19-baureglement-2019.pdf' -> 'baureglement 2019'."""
    name = urllib.parse.unquote(urllib.parse.urlparse(url).path.rsplit("/", 1)[-1])
    name = re.sub(r"\.pdf$", "", name, flags=re.I)
    name = re.sub(r"^\d{1,3}[-_ ]+", "", name)
    return re.sub(r"[-_]+", " ", name).strip()


def clean_title(title):
    """'Path Abfallreglement V7 def.pdf (PDF, 120 KB)' -> 'Abfallreglement V7 def'."""
    t = title
    for pat in _TITLE_NOISE:
        t = re.sub(pat, " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip(" -–|·") or title


def _resolve(url):
    """A document link may be the PDF itself or a detail page that links to it: return (text, final_url)."""
    if "/show_as_json" in url:  # TLex law: metadata JSON with a PDF link
        data = json.loads(sources.http(url, timeout=60, cache=True))
        tol = data.get("text_of_law", {})
        version = tol.get("selected_version") or {}
        pdf = version.get("pdf_link_tol") or tol.get("pdf_link")
        page = tol.get("canonical_link") or url
        if pdf:
            return sources.pdf_or_html_text(sources.http(pdf, timeout=90, cache=True)), page
        return "", page
    if "stadt-zuerich.ch/" in url and "/amtliche-sammlung/" in url:  # act page → consolidated PDF
        pdf = cities.zurich_pdf(url)
        if pdf:
            return sources.pdf_or_html_text(sources.http(pdf, timeout=90, cache=True)), pdf
    raw = sources.http(url, timeout=60, cache=True)
    if raw[:5] == b"%PDF-":
        return sources.pdf_or_html_text(raw), url
    for href, _ in _links(url, raw):
        u = href.lower()
        if u.endswith(".pdf") or "/_doc/" in u or "/_docn/" in u:
            try:
                inner = sources.http(href, timeout=60, cache=True)
                if inner[:5] == b"%PDF-":
                    return sources.pdf_or_html_text(inner), href
            except Exception:
                continue
    return sources.pdf_or_html_text(raw), url


def load_document(doc):
    cache = sources._cache_path(doc["url"], "txt")
    meta = sources._cache_path(doc["url"], "url")
    if cache.exists() and meta.exists():
        return cache.read_text(encoding="utf-8"), meta.read_text(encoding="utf-8")
    text, final = _resolve(doc["url"])
    if len(text.strip()) >= 200:  # never cache a failed extraction
        cache.write_text(text, encoding="utf-8")
        meta.write_text(final, encoding="utf-8")
    return text, final


# --------------------------------------------------------------------------- Apertus selection

def pick_documents(question, commune, canton, docs):
    if not docs:
        return []
    listing = "\n".join(f"{i}. {d['title']}" for i, d in enumerate(docs[:150], 1))
    try:
        raw = apertus.chat([{"role": "user", "content": PICK_PROMPT.format(
            commune=commune, canton=canton, question=question, listing=listing, n=MAX_DOCS)}],
            temperature=0.0, max_tokens=60)
    except apertus.ApertusError:
        return []
    picks = lexfind_agent._json(raw, [])
    if not isinstance(picks, list):
        picks = re.findall(r'"([^"]+)"', raw)
    # Titles, not positions: on long lists the model's numbers drift by one.
    by_title = {sources.fold(d["title"]).strip(): d for d in docs[:150]}
    chosen = []
    for p in picks:
        if isinstance(p, int) and 1 <= p <= min(len(docs), 150):
            d = docs[p - 1]
        elif isinstance(p, str):
            key = sources.fold(p).strip()
            d = by_title.get(key) or next((v for k, v in by_title.items() if k.startswith(key[:40]) or key.startswith(k[:40])), None)
        else:
            d = None
        if d and d not in chosen:
            chosen.append(d)
    if not chosen:
        chosen = _topic_fallback(question, docs)
    # Quiet hours, noise, dogs in public and signs are in the general police regulation; Apertus sometimes takes the
    # police-force regulation instead (Lausanne 510.1 over 500.1), so the general one always goes first.
    if re.search(r"larm|ruhe|nacht|bruit|repos|nuit|rumor|quiete|hund|chien|cane|leine|laisse|reklame|affich|insegn",
                 sources.fold(question)):
        general = next((d for d in docs if re.search(
            r"general de police|generale di polizia|allgemeine polizei|polizeiverordnung|polizeireglement|"
            r"reglement de police|regolamento di polizia|police de la commune", sources.fold(d["title"]))), None)
        if general:
            chosen = [general] + [d for d in chosen if d is not general]
    return chosen[:MAX_DOCS]


# Question words -> words in the titles of the regulations that hold the answer (DE/FR/IT).
TOPIC_HINTS = [
    (r"abfall|kehricht|entsorg|müll|dechet|ordure|rifiut", r"abfall|kehricht|entsorg|dechet|rifiut"),
    (r"larm|ruhe|nacht|bruit|repos|nuit|rumor|quiete|nott", r"polizei|police|polizia|larm|ruhe|bruit"),
    (r"hund|chien|cane|cani", r"hund|chien|cani|polizei|police"),
    (r"grab|friedhof|bestatt|tombe|cimeti|inhum|sepolt|cimit|tomba", r"friedhof|bestatt|cimeti|inhum|sepolt|cimit"),
    (r"bau|schuppen|zonen|construct|permis|ediliz|costruz", r"bau|zon|construct|ediliz"),
    (r"park|parkier|stationn|parcage|posteggi|parchegg", r"park|stationn|parcage|posteggi|parchegg"),
    (r"wasser|abwasser|eaux?|acqua", r"wasser|eaux?|acqua"),
    (r"plakat|reklame|affich|insegn", r"plakat|reklame|affich|insegn|polizei|police"),
]


def _topic_fallback(question, docs):
    """When Apertus declines but a title plainly matches the question's topic, take up to two such titles."""
    q = sources.fold(question)
    for qpat, tpat in TOPIC_HINTS:
        if re.search(qpat, q):
            hits = [d for d in docs[:300] if re.search(tpat, sources.fold(d["title"]))]
            # Main regulations before fee tariffs and annexes.
            hits.sort(key=lambda d: (bool(re.search(r"tarif|gebuhr|annex|anhang|formular|gesuch", sources.fold(d["title"]))),
                                     len(d["title"])))
            if hits:
                return hits[:2]
    return []


def _shortlist(question, terms, docs, limit=150):
    """Apertus sees at most 150 titles: on longer lists (city collections hold 200-800 acts) titles that share a
    word stem with the question go first, in their original (systematic) order."""
    if len(docs) <= limit:
        return docs
    stems = {sources.fold(w)[:5] for w in re.findall(r"[^\W\d_]{4,}", question) + list(terms) if len(w) >= 4}
    for qpat, tpat in TOPIC_HINTS:  # "Hundetaxe" should also surface "Hundegesetz" and police regulations
        if re.search(qpat, sources.fold(question)):
            stems |= set(tpat.split("|"))

    def score(d):
        title = sources.fold(d["title"])
        return sum(1 for st in stems if st and st in title)
    ranked = sorted(range(len(docs)), key=lambda i: (-score(docs[i]), i))
    return [docs[i] for i in ranked[:limit]]


def retrieve(question, location, terms):
    """Full communal step. Returns (site, docs_found, chosen_docs, [(doc_meta, article)])."""
    site = website(location["bfs"])
    city = cities.documents(location["bfs"])  # the five largest cities have dedicated readers
    if city is not None:
        site = "https://" + cities.LABELS[int(location["bfs"])]
        docs = city
    elif not site:
        return None, [], [], []
    else:
        docs = find_documents(site)
    docs = _shortlist(question, terms, docs)
    chosen = pick_documents(question, location["commune"], location["canton_name"], docs)
    loaded = []
    for i, d in enumerate(chosen, 1):
        try:
            text, final = load_document(d)
        except Exception:
            continue
        if len(text.strip()) < 200:
            continue
        arts = sources.split_articles(text)
        for a in arts:
            a["url"] = final
        meta = {"sr": f"G{i}", "title": d["title"], "url": final}
        loaded.append((meta, arts))
    # No keyword top-up here: a commune without a rule on the topic should contribute nothing.
    picked = lexfind_agent.pick_articles(question, loaded, terms, topup=False) if loaded else []
    hint = next((t for q, t in TOPIC_HINTS if re.search(q, sources.fold(question))), None)
    if loaded and not picked and hint and re.search(hint, sources.fold(loaded[0][0]["title"])):
        # A regulation that plainly covers the topic (noise question, police regulation) but whose headings convinced
        # no one (Lausanne's bare "Art. 31 –"): its two best keyword matches. Never for other topics — on adoption or
        # pension questions this used to add police-regulation articles.
        meta, arts = loaded[0]
        words = [w for w in re.findall(r"[^\W\d_]{4,}", question)] + list(terms)
        picked = [(meta, a) for a in sources.rank_articles(arts, words, top=2) if a.get("score", 0) >= 2]
    return site, docs, chosen, picked
