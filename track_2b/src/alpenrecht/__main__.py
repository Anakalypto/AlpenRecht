"""CLI: python -m alpenrecht {serve|ask} ..."""
import argparse
import json
import sys


def main(argv=None):
    ap = argparse.ArgumentParser(prog="alpenrecht")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve", help="web app on HOST:PORT (default 127.0.0.1:5055)")
    q = sub.add_parser("ask", help="answer one question in the terminal")
    q.add_argument("question")
    q.add_argument("--place", default="", help='e.g. "7000 Chur" or "@46.85,9.53"')
    q.add_argument("--lang", default="", choices=["", "de", "fr", "it", "rm", "en"])
    q.add_argument("--asof", default=None, help="federal law as of YYYY-MM-DD")
    q.add_argument("--json", action="store_true", help="print every pipeline event as JSON")
    a = ap.parse_args(argv)

    if a.cmd == "serve":
        from .app import main as serve
        serve()
        return
    from . import cache, pipeline
    for ev in cache.stream(pipeline.run(a.question, a.place, a.asof, a.lang, [])):
        if a.json:
            print(json.dumps(ev, ensure_ascii=False), flush=True)
        elif ev["type"] == "step" and ev["status"] != "running":
            print(f"· {ev['label']}", file=sys.stderr, flush=True)
        elif ev["type"] == "final":
            print(ev["text"])
        elif ev["type"] == "error":
            print(f"error: {ev['message']}", file=sys.stderr)


if __name__ == "__main__":
    main()
