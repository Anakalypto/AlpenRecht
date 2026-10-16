"""Run a question set through the real pipeline and save everything a grader needs, one JSON line per question.

    .venv/Scripts/python.exe bench/accuracy_run.py --set bench/questions_dev60.json --out bench/runs/dev-base.jsonl
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
    args = ap.parse_args()

    load_env(pathlib.Path(args.env))
    sys.path.insert(0, str(pathlib.Path(args.root).resolve()))
    import apertus  # noqa: E402
    import config  # noqa: E402
    import pipeline  # noqa: E402

    if not config.APERTUS_API_KEY:
        sys.exit("APERTUS_API_KEY is empty: put the key in .env first.")

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
