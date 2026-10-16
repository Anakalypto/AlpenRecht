"""Communal regulations: no central collection exists, so users upload a PDF or point to a URL."""
import json
import uuid

import config
import sources

UPLOAD_DIR = config.CACHE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


def _save(name, text, url=""):
    doc_id = uuid.uuid4().hex[:12]
    doc = {"id": doc_id, "name": name, "url": url, "chars": len(text), "articles": sources.split_articles(text)}
    (UPLOAD_DIR / f"{doc_id}.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return doc


def add_file(name, raw):
    text = sources.pdf_or_html_text(raw) if raw[:5] == b"%PDF-" or name.lower().endswith((".htm", ".html")) \
        else raw.decode("utf-8", "replace")
    if len(text.strip()) < 50:
        raise ValueError("No readable text in this file (scanned PDF without OCR?).")
    return _save(name, text)


def add_url(url):
    if not url.startswith(("http://", "https://")):
        raise ValueError("URL must start with http:// or https://")
    raw = sources.http(url, timeout=60, cache=True)
    text = sources.pdf_or_html_text(raw)
    if len(text.strip()) < 50:
        raise ValueError("No readable text at this URL.")
    return _save(url.rsplit("/", 1)[-1][:80] or url, text, url)


def get(doc_id):
    if not doc_id.isalnum():
        return None
    path = UPLOAD_DIR / f"{doc_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
