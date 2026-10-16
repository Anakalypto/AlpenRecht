"""Alpenrecht AI — Swiss multi-level legal research on Apertus."""
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from . import apertus
from . import config
from . import pipeline
from . import sources
from . import uploads

WEB = str(Path(__file__).resolve().parent / "web")
app = Flask(__name__, static_folder=WEB, static_url_path="/static")
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


@app.get("/")
def index():
    return send_from_directory(WEB, "index.html")


@app.get("/api/health")
def health():
    info = {"model": config.APERTUS_MODEL, "base_url": config.APERTUS_BASE_URL,
            "key_set": bool(config.APERTUS_API_KEY)}
    if request.args.get("check") and config.APERTUS_API_KEY:
        try:
            info["models"] = apertus.list_models()
            info["ok"] = True
        except apertus.ApertusError as e:
            info["ok"], info["error"] = False, str(e)
    return jsonify(info)


@app.get("/api/locate")
def locate():
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    try:
        return jsonify(sources.suggest_locations(q))
    except Exception:
        return jsonify([])


@app.get("/api/reverse")
def reverse():
    """Commune at a point the user picked on the map."""
    try:
        lat, lon = float(request.args["lat"]), float(request.args["lon"])
    except (KeyError, ValueError):
        return jsonify({"error": "lat and lon required"}), 400
    try:
        loc = sources.commune_at(lat, lon, geometry=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 502
    return jsonify(loc or {"error": "outside Switzerland"}), (200 if loc else 404)


@app.post("/api/ask")
def ask():
    body = request.get_json(force=True)
    question = (body.get("question") or "").strip()
    if not question:
        return jsonify({"error": "empty question"}), 400
    events = pipeline.run(question, body.get("location", ""), body.get("asof") or None,
                          body.get("lang", ""), body.get("uploads", []))
    return Response(pipeline.sse(events), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/upload")
def upload():
    try:
        if request.files.get("file"):
            f = request.files["file"]
            doc = uploads.add_file(f.filename, f.read())
        else:
            doc = uploads.add_url((request.get_json(force=True) or {}).get("url", "").strip())
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    return jsonify({"id": doc["id"], "name": doc["name"], "articles": len(doc["articles"]), "chars": doc["chars"]})


def main():
    app.run(host=config.HOST, port=config.PORT, debug=False, threaded=True)
