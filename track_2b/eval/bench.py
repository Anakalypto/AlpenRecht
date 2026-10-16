"""Alpenrecht AI benchmark: retrieval recall, citation fidelity, language/format, latency.

    .venv/Scripts/python.exe bench/bench.py [--model swiss-ai/Apertus-v1.5-8B] [--only id1,id2] [--workers 3]

Writes bench/results/<model>.json and prints a summary table.
"""
import argparse
import json
import pathlib
import sys
import time
from concurrent.futures import ThreadPoolExecutor

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from alpenrecht import checks  # noqa: E402
from alpenrecht import config  # noqa: E402
from alpenrecht import pipeline  # noqa: E402

HERE = pathlib.Path(__file__).resolve().parent
sys.stdout.reconfigure(encoding="utf-8")  # the summary's ✓/✗ crashed the cp1252 Windows console


def _hit(evidence, level, gold):
    """Gold is [[sr, article|None], ...]; returns (act_hit, article_hit, matching ids)."""
    act = art = False
    ids = set()
    for sr, article in gold:
        for e in evidence:
            if e["level"] != level or e["sr"] != sr:
                continue
            act = True
            if article is None or checks.art_key(e["number"]) == article:
                art = True
                ids.add(e["id"])
    return act, art, ids


def run_one(item):
    t0 = time.time()
    marks, evidence, final, error, plan = {}, [], None, "", {}
    first_token = None
    for ev in pipeline.run(item["q"], item["loc"], None, item["lang"], []):
        now = time.time() - t0
        if ev["type"] == "step":
            marks[f"{ev['key']}_{ev['status']}"] = now
        elif ev["type"] == "plan":
            plan = ev["plan"]
        elif ev["type"] == "sources":
            evidence = ev["sources"]
        elif ev["type"] == "token" and first_token is None:
            first_token = now
        elif ev["type"] == "final":
            final = ev
        elif ev["type"] == "error":
            error = ev["message"]
    total = time.time() - t0

    res = {"id": item["id"], "lang": item["lang"], "loc": item["loc"], "error": error,
           "planner_ok": not plan.get("fallback") and bool(plan),
           "n_sources": len(evidence), "total_s": round(total, 1),
           "plan_s": round(marks.get("plan_done", marks.get("plan_warn", 0)) - marks.get("plan_running", 0), 1),
           "ttft_s": round(first_token, 1) if first_token else None}
    gold_ids = set()
    for level, key in (("federal", "fed"), ("cantonal", "can")):
        if item.get(key):
            act, art, ids = _hit(evidence, level, item[key])
            res[f"{key}_act"], res[f"{key}_art"] = act, art
            gold_ids |= ids
    if item.get("com"):  # communal gold = regulation title fragments
        subs = [checks.sources.fold(x) for x in item["com"]]
        ids = {e["id"] for e in evidence if e["level"] == "communal"
               and any(s in checks.sources.fold(e["title"]) for s in subs)}
        res["com_doc"] = bool(ids)
        res["com_any"] = any(e["level"] == "communal" for e in evidence)
        gold_ids |= ids

    if final:
        text, c = final["text"], final["check"]
        h = pipeline.HEADINGS[item["lang"]]
        res.update({
            "words": c["words"], "citations": c["citations"],
            "invalid": len(c["invalid_citations"]), "unsupported": len(c["unsupported_articles"]),
            "unsupported_list": c["unsupported_articles"], "prose_left": c["prose_citations"], "repaired": c["repaired"],
            "gold_cited": bool(gold_ids & set(c["cited_ids"])),
            "lang_ok": f"## {h[0]}" in text,
            "headings_ok": all(f"## {x}" in text for x in (h[0], h[1], h[4], h[5])),
            "disclaimer_ok": h[6].rstrip(".") in text,
            "answer": text,
            "verification": final.get("verification", []),
            "revisions": sum(r.get("revised", False) for r in final.get("verification", [])),
            "sources_added": sum(len(r.get("added", [])) for r in final.get("verification", [])),
            "claims_checked": sum(r.get("claims", 0) for r in final.get("verification", [])),
        })
    res["sources"] = [f"[{e['id']}] {e['level'][:3]} {e['law']} {e['number']}" for e in evidence]
    return res


def pct(rows, key):
    vals = [r[key] for r in rows if key in r]
    return f"{100 * sum(bool(v) for v in vals) / len(vals):.0f}% ({sum(bool(v) for v in vals)}/{len(vals)})" if vals else "–"


def avg(rows, key):
    vals = [r[key] for r in rows if r.get(key) is not None]
    return f"{sum(vals) / len(vals):.1f}" if vals else "–"


def summarize(rows, model):
    lines = [f"### {model}", "",
             "| metric | value |", "|---|---|",
             f"| planner JSON ok | {pct(rows, 'planner_ok')} |",
             f"| federal act retrieved | {pct(rows, 'fed_act')} |",
             f"| federal gold article retrieved | {pct(rows, 'fed_art')} |",
             f"| cantonal act retrieved | {pct(rows, 'can_act')} |",
             f"| cantonal gold article retrieved | {pct(rows, 'can_art')} |",
             f"| communal: any regulation found / gold regulation found | {pct(rows, 'com_any')} / {pct(rows, 'com_doc')} |",
             f"| answer cites a gold source | {pct(rows, 'gold_cited')} |",
             f"| answers with an invalid [n] | {pct([dict(x=r['invalid'] > 0) for r in rows if 'invalid' in r], 'x')} |",
             f"| answers with unsupported article no. | {pct([dict(x=r['unsupported'] > 0) for r in rows if 'unsupported' in r], 'x')} |",
             f"| prose citations repaired / left (total) | {sum(r.get('repaired', 0) for r in rows)} / {sum(r.get('prose_left', 0) for r in rows)} |",
             f"| answer in right language | {pct(rows, 'lang_ok')} |",
             f"| all headings present | {pct(rows, 'headings_ok')} |",
             f"| disclaimer present | {pct(rows, 'disclaimer_ok')} |",
             f"| avg words (target < 230) | {avg(rows, 'words')} |",
             f"| avg citations | {avg(rows, 'citations')} |",
             f"| avg plan time (s) | {avg(rows, 'plan_s')} |",
             f"| avg time to first token (s) | {avg(rows, 'ttft_s')} |",
             f"| avg total time (s) | {avg(rows, 'total_s')} |",
             f"| verification: claims checked / revisions / sources added (avg per answer) | {avg(rows, 'claims_checked')} / {avg(rows, 'revisions')} / {avg(rows, 'sources_added')} |",
             f"| errors | {sum(bool(r['error']) for r in rows)} |", ""]
    lines += ["| id | lang | fed act/art | can act/art | gold cited | invalid | unsupported | words | ttft | total |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    yn = lambda v: "–" if v is None else ("✓" if v else "✗")  # noqa: E731
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['lang']} | {yn(r.get('fed_act'))}/{yn(r.get('fed_art'))} | {yn(r.get('can_act'))}/{yn(r.get('can_art') if 'can_art' in r else r.get('com_doc'))} "
            f"| {yn(r.get('gold_cited'))} | {r.get('invalid', '–')} | {', '.join(r.get('unsupported_list', [])) or 0} "
            f"| {r.get('words', '–')} | {r.get('ttft_s', '–')} | {r['total_s']} |")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=config.APERTUS_MODEL)
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--tag", default="")
    ap.add_argument("--set", default="questions.json")
    args = ap.parse_args()
    config.APERTUS_MODEL = args.model

    items = json.loads((HERE / args.set).read_text(encoding="utf-8"))
    if args.only:
        keep = set(args.only.split(","))
        items = [i for i in items if i["id"] in keep]
    with ThreadPoolExecutor(args.workers) as ex:
        rows = list(ex.map(run_one, items))

    out = HERE / "results"
    out.mkdir(exist_ok=True)
    name = args.model.split("/")[-1] + (f"-{args.tag}" if args.tag else "")
    (out / f"{name}.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    summary = summarize(rows, name)
    (out / f"{name}.md").write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
