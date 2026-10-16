"""Minimal client for an OpenAI-compatible Apertus endpoint."""
import json
import re
import time
import urllib.error
import urllib.request

import config


class ApertusError(RuntimeError):
    pass


RETRY_CODES = (429, 500, 502, 503, 504)
RETRIES = 2


def _request(path, payload, stream=False):
    if not config.APERTUS_API_KEY:
        raise ApertusError("APERTUS_API_KEY is not set (put it in .env).")
    req = urllib.request.Request(
        f"{config.APERTUS_BASE_URL}{path}",
        data=json.dumps(payload).encode() if payload is not None else None,
        headers={
            "Authorization": f"Bearer {config.APERTUS_API_KEY}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream" if stream else "application/json",
            "User-Agent": config.USER_AGENT,
        },
        method="POST" if payload is not None else "GET",
    )
    # Rate limits and overloaded replicas are transient: without a retry, one 429 silently swapped a whole
    # retrieval step for its keyword fallback.
    for attempt in range(RETRIES + 1):
        try:
            return urllib.request.urlopen(req, timeout=180)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:500]
            if e.code in RETRY_CODES and attempt < RETRIES:
                wait = e.headers.get("Retry-After", "")
                time.sleep(min(float(wait), 30) if wait.replace(".", "", 1).isdigit() else 3 * (attempt + 1))
                continue
            raise ApertusError(f"Apertus API {e.code}: {body}") from None
        except urllib.error.URLError as e:
            if attempt < RETRIES:
                time.sleep(3 * (attempt + 1))
                continue
            raise ApertusError(f"Cannot reach Apertus API: {e.reason}") from None
        except (TimeoutError, OSError) as e:
            # urlopen only wraps connection errors: a reply slower than the timeout raised a bare TimeoutError
            # that ended the answer stream without a word. Not retried: the server may still be generating, and
            # three 180 s waits would stall the answer for nine minutes.
            raise ApertusError(f"Apertus API timed out or failed: {type(e).__name__}") from None


def list_models():
    with _request("/models", None) as r:
        data = json.load(r)
    return [m.get("id") for m in data.get("data", [])]


def chat(messages, temperature=0.2, max_tokens=1500, model=None):
    payload = {
        "model": model or config.APERTUS_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    try:
        with _request("/chat/completions", payload) as r:
            data = json.load(r)
        return data["choices"][0]["message"]["content"] or ""
    except ApertusError:
        raise
    except (ValueError, KeyError, IndexError, TypeError, TimeoutError, OSError) as e:
        # A malformed 200 reply or a timeout while reading the body: callers only handle ApertusError.
        raise ApertusError(f"Unusable Apertus reply: {type(e).__name__}") from None


def chat_stream(messages, temperature=0.2, max_tokens=2500):
    """Yield text deltas as they arrive (server-sent events)."""
    payload = {
        "model": config.APERTUS_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    with _request("/chat/completions", payload, stream=True) as r:
        for raw in r:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                delta = json.loads(chunk)["choices"][0].get("delta", {})
            except (ValueError, KeyError, IndexError):
                continue
            if delta.get("content"):
                yield delta["content"]


def chat_json(messages, max_tokens=900):
    """Ask for a JSON object and parse it leniently (models wrap JSON in prose or fences)."""
    text = chat(messages, temperature=0.0, max_tokens=max_tokens)
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ApertusError(f"Model did not return JSON: {text[:200]}")
    blob = match.group(0)
    try:
        return json.loads(blob)
    except ValueError:
        # Trailing commas are the usual culprit.
        return json.loads(re.sub(r",\s*([}\]])", r"\1", blob))
