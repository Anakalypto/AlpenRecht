"""Readers for the law collections of Switzerland's five largest cities, and Lugano.

Their collections are JavaScript apps or paged databases the generic crawler can't list, but each has a plain
source underneath:
  Zürich   — Amtliche Sammlung: sitemap → subcategory pages carry "<number> <title>" cards → act page links the PDF;
  Geneva   — "Règlements municipaux": a paged Drupal list, each entry a direct PDF link;
  Basel    — the canton legislates for the city (no separate municipal collection): the TLex JSON index of
             gesetzessammlung.bs.ch;
  Lausanne — "Recueil systématique du droit communal": one page with number, title and PDF for every regulation;
  Bern     — stadtrecht.bern.ch (LexWork): the sitemap lists every act and each act has a PDF whose first lines
             hold its title;
  Lugano   — "Legislazione": one page of /law/<id> links (each serves the PDF), titled with their number.
Each reader returns [{title, url}] like communal.find_documents; communal.load_document reads the PDFs.
"""
import html
import json
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from . import config
from . import sources

CACHE = config.CACHE_DIR / "communes"
CACHE.mkdir(exist_ok=True)
WEEK = 7 * 24 * 3600


def _get(url, timeout=30):
    return sources.http(url, timeout=timeout, cache=False)


def _text(raw):
    return html.unescape(raw.decode("utf-8", "replace"))


def zurich():
    base = "https://www.stadt-zuerich.ch"
    sitemap = _text(_get(f"{base}/de.sitemap.xml", timeout=60))
    groups = sorted(set(re.findall(r"<loc>([^<]*/amtliche-sammlung/\d+/\d+\.html)</loc>", sitemap)))

    def cards(url):
        try:
            page = _text(_get(url))
        except Exception:
            return []
        return [{"title": re.sub(r"\s+", " ", t).strip(), "url": urllib.parse.urljoin(base, h)}
                for t, h in re.findall(r'heading="([^"]+)"\s+href="([^"]*/amtliche-sammlung/\d+/\d+/\d+\.html)"', page)]

    with ThreadPoolExecutor(4) as ex:
        return [d for found in ex.map(cards, groups) for d in found]


def zurich_pdf(page_url):
    """Zürich act page → its consolidated PDF (the link sits inside a web component's JSON attribute)."""
    page = _text(_get(page_url))
    pdfs = re.findall(r'(/dam/web/[^"<>\s\\]+?\.pdf)', page)
    return urllib.parse.urljoin("https://www.stadt-zuerich.ch", pdfs[0]) if pdfs else None


def geneva():
    base = "https://www.geneve.ch"
    out, seen = [], set()
    for page in range(40):
        try:
            raw = _text(_get(f"{base}/autorites-administration/administration-municipale/reglements-municipaux?page={page}"))
        except Exception:
            break
        items = re.findall(r'<a href="(/administration-municipale/reglements-municipaux/[^"]+)" class="lien"[^>]*>\s*'
                           r'<span class="lien__extension"\s*>[^<]*</span>\s*([^<]+)</a>', raw)
        new = [(h, t) for h, t in items if h not in seen]
        if not new:
            break
        for h, t in new:
            seen.add(h)
            out.append({"title": "LC " + re.sub(r"\s+", " ", t).strip(), "url": base + h})
    return out


def basel():
    from . import communal  # local import: communal imports this module
    # The collection also holds Riehen's ("RiE", "RiB") and Bettingen's ("BeE", "BeB") own acts: not Basel's law
    # (a Basel dog-tax answer quoted Riehen's Fr. 150).
    return [d for d in communal.tlex_documents("www.gesetzessammlung.bs.ch")
            if not re.match(r"(?:Ri|Be)[EB]\s", d["title"])]


def lausanne():
    base = "https://www.lausanne.ch/apps/actualites/"
    raw = _text(_get(base + "index_recueil.php", timeout=60))
    out = []
    for block in re.split(r'<li class="cd-accordion" id="document-', raw)[1:]:
        num = re.search(r'actus-muni-item-numero">\s*([^<]+?)\s*<', block)
        title = re.search(r'actus-muni-item-title">\s*([^<]+?)\s*<', block)
        pdf = re.search(r'href="(Next/serve\.php\?id=\d+&kind=recueil)"', block)
        if title and pdf:
            out.append({"title": f"{num.group(1) if num else ''} {title.group(1)}".strip(), "url": base + pdf.group(1)})
    return out


def lugano():
    """lugano.ch "Legislazione": every regulation is a /law/<id>/<slug> link that serves the PDF, titled by number."""
    base = "https://www.lugano.ch"
    raw = _text(_get(f"{base}/la-mia-citta/amministrazione/legislazione.html", timeout=60))
    out, seen = [], set()
    for href, title in re.findall(r'<a[^>]+href="(/law/\d+/[^"]+)"[^>]*title="([^"]+)"', raw):
        if href not in seen:
            seen.add(href)
            out.append({"title": re.sub(r"\s+", " ", title).strip(), "url": base + href})
    return out


def _bern_title(pdf_url):
    """First lines of a Bern act PDF: '551.2 / 4. November 2010 (Stand …) / Reglement / über … (Videoreglement; VR)'."""
    try:
        text = sources.pdf_or_html_text(sources.http(pdf_url, timeout=60, cache=True))
    except Exception:
        return ""
    lines = [l.strip() for l in text[:900].splitlines() if l.strip()]
    title = []
    for line in lines[1:]:
        if re.match(r"(?:Der|Die|Das)\s+(?:Stadtrat|Gemeinderat|Gemeinde|stimmberechtigt|Direktion)|gestützt|beschliesst|Art\.\s*1\b",
                    line, re.I):
            break
        if re.search(r"\(Stand:|\d{4}\s*$", line) and not title:
            continue  # the date line
        title.append(line)
    return re.sub(r"\s+", " ", " ".join(title))[:200]


def bern():
    base = "https://stadtrecht.bern.ch"
    sitemap = _text(_get(f"{base}/sitemap.xml", timeout=60))
    # Acts appear as "lex-551_2" (95 of them) and as "dgn-lex_551_2" (all ~240); "000_*" are index pages.
    ids = set(re.findall(r"<loc>https://stadtrecht\.bern\.ch/lex-(\d+(?:_\d+)*)</loc>", sitemap))
    ids |= set(re.findall(r"<loc>https://stadtrecht\.bern\.ch/dgn-lex_(\d+(?:_\d+)*)</loc>", sitemap))
    ids = sorted(i for i in ids if not i.startswith("000"))

    def doc(i):
        pdf = f"{base}/lexoverview-home/lex-{i}/lex-{i}.pdf"
        title = _bern_title(pdf)
        return {"title": f"{i.replace('_', '.')} {title}".strip(), "url": pdf} if title else None

    with ThreadPoolExecutor(4) as ex:
        return [d for d in ex.map(doc, ids) if d]


READERS = {261: zurich, 6621: geneva, 2701: basel, 5586: lausanne, 351: bern, 5192: lugano}
LABELS = {261: "stadt-zuerich.ch (Amtliche Sammlung)", 6621: "geneve.ch (règlements municipaux)",
          2701: "gesetzessammlung.bs.ch (the canton legislates for the city)",
          5586: "lausanne.ch (recueil systématique)", 351: "stadtrecht.bern.ch",
          5192: "lugano.ch (legislazione)"}


def documents(bfs):
    """[{title, url}] for a big city, cached for a week; None for any other commune."""
    reader = READERS.get(int(bfs))
    if not reader:
        return None
    cache = CACHE / f"city-{bfs}.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < WEEK:
        return json.loads(cache.read_text(encoding="utf-8"))
    try:
        docs = reader()
    except Exception:
        return []
    # Repealed acts stay listed in some collections ("(Aufgehoben)", "(Ausser Kraft)", "abrogé").
    docs = [d for d in docs if not re.search(r"aufgehoben|ausser kraft|abrog", d["title"], re.I)]
    if docs:
        cache.write_text(json.dumps(docs, ensure_ascii=False), encoding="utf-8")
    return docs
