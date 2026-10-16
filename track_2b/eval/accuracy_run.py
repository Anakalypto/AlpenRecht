"""Run a question set through the real pipeline and save everything a grader needs, one JSON line per question.

    python eval/accuracy_run.py --set eval/questions_dev60.json --out eval/runs/dev-base.jsonl
        [--root <checkout to import the app from>] [--workers 4]

Unlike bench.py, a crash in one question is recorded instead of killing the run, results are written as they
finish (re-running resumes), and every Apertus API error is logged next to the output (<out>.api_errors.jsonl)
so a rate-limit storm can't silently pass for bad answers.
"""
import argparse
import json
import os
import pathlib
import sys
import threading
import time
import traceback
from concurrent.futures import ThreadPoolExecutor

HERE = pathlib.Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")


def load_env(path):
    """Copy KEY=VALUE lines into os.environ (never printed), so a checkout without its own .env can run."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            if v.strip():
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--set", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--root", default=str(HERE.parent))
    ap.add_argument("--env", default=str(HERE.parent / ".env"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--only", default="")
    ap.add_argument("--net-retry", action="store_true", help="add the current code's network retry to an older checkout")
    args = ap.parse_args()

    load_env(pathlib.Path(args.env))
    root = pathlib.Path(args.root).resolve()
    if (root / "src" / "alpenrecht").is_dir():  # current layout: track_2b/src/alpenrecht
        sys.path.insert(0, str(root / "src"))
        from alpenrecht import apertus, config, pipeline, sources  # noqa: E402
    else:  # the original flat checkout (eabfc3b), used as the baseline
        sys.path.insert(0, str(root))
        import apertus, config, pipeline, sources  # noqa: E402,E401

    if not config.APERTUS_API_KEY:
        sys.exit("API key is empty: set LLM_API_KEY (APERTUS_API_KEY for the original eabfc3b checkout) in .env first.")

    out = pathlib.Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    err_log = out.with_suffix(".api_errors.jsonl")
    lock = threading.Lock()

    real_request = apertus._request

    def logged_request(path, payload, stream=False):
        try:
            return real_request(path, payload, stream)
        except Exception as e:  # logged, then re-raised unchanged so app behaviour is identical
            with lock, err_log.open("a", encoding="utf-8") as f:
                f.write(json.dumps({"t": round(time.time(), 1), "type": type(e).__name__,
                                    "msg": str(e)[:200]}, ensure_ascii=False) + "\n")
            raise

    apertus._request = logged_request

    if args.net_retry:
        # Give an older checkout the same network patience as the current code (3 attempts on dropped
        # connections), so a busy line doesn't count as a quality difference between versions.
        import urllib.error
        orig_http = sources.http

        def http_retry(url, data=None, headers=None, timeout=60, cache=False):
            if cache:
                return orig_http(url, data, headers, timeout, cache=True)  # its inner download comes back here
            for attempt in range(3):
                try:
                    return orig_http(url, data, headers, timeout, cache=False)
                except urllib.error.HTTPError:
                    raise
                except (urllib.error.URLError, TimeoutError, ConnectionError):
                    if attempt == 2:
                        raise
                    time.sleep(2 * (attempt + 1))

        sources.http = http_retry

    items = json.loads(pathlib.Path(args.set).read_text(encoding="utf-8"))
    if args.only:
        keep = set(args.only.split(","))
        items = [i for i in items if i["id"] in keep]
    done = set()
    if out.exists():
        done = {json.loads(line)["id"] for line in out.read_text(encoding="utf-8").splitlines() if line.strip()}
    todo = [i for i in items if i["id"] not in done]
    print(f"{len(todo)} to run ({len(done)} already done) with model {config.APERTUS_MODEL} from {args.root}", flush=True)

    def run_one(item):
        t0 = time.time()
        res = {"id": item["id"], "lang": item["lang"], "loc": item["loc"], "q": item["q"],
               "steps": [], "plan": None, "sources": [], "answer": None, "check": None, "verification": None,
               "error_event": None, "exception": None}
        try:
            for ev in pipeline.run(item["q"], item["loc"], None, item["lang"], []):
                t = ev["type"]
                if t == "step" and ev.get("status") in ("done", "warn", "error"):
                    res["steps"].append(f"{ev['key']}:{ev['status']}:{ev.get('label', '')}"[:300])
                elif t == "plan":
                    res["plan"] = ev.get("plan")
                elif t == "sources":
                    res["sources"] = [{k: e.get(k) for k in ("id", "level", "law", "sr", "number", "title", "url")}
                                      | {"excerpt": (e.get("text") or "")[:700]} for e in ev["sources"]]
                elif t == "final":
                    res["answer"], res["check"] = ev["text"], ev.get("check")
                    res["verification"] = ev.get("verification")
                elif t == "error":
                    res["error_event"] = ev.get("message")
        except Exception as e:
            res["exception"] = f"{type(e).__name__}: {e}"[:500]
            res["traceback"] = traceback.format_exc()[-1500:]
        res["seconds"] = round(time.time() - t0, 1)
        with lock, out.open("a", encoding="utf-8") as f:
            f.write(json.dumps(res, ensure_ascii=False) + "\n")
        status = "EXC" if res["exception"] else ("no-answer" if not res["answer"] else "ok")
        print(f"{item['id']} {status} {res['seconds']}s", flush=True)

    with ThreadPoolExecutor(args.workers) as ex:
        list(ex.map(run_one, todo))
    print("done", flush=True)


if __name__ == "__main__":
    main()
