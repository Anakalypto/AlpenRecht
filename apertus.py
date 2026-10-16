"""Minimal client for an OpenAI-compatible Apertus endpoint."""
import json
import re
import urllib.error
import urllib.request

import config


class ApertusError(RuntimeError):
    pass


def _request(path, payload, stream=False):
    if not config.APERTUS_API_KEY:
        raise ApertusError("APERTUS_API_KEY is not set (put it in alpenrecht/.env).")
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
    try:
        return urllib.request.urlopen(req, timeout=180)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")[:500]
        raise ApertusError(f"Apertus API {e.code}: {body}") from None
    except urllib.error.URLError as e:
        raise ApertusError(f"Cannot reach Apertus API: {e.reason}") from None


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
    with _request("/chat/completions", payload) as r:
        data = json.load(r)
    return data["choices"][0]["message"]["content"] or ""


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
