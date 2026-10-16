"""Un-blind graded packets and summarise both runs.

usage (from track_2b/eval/heldout): python score.py grades_blind.json blind_key.json original evaluated ../questions_heldout100.json
blind_key.json says, per question, whether answer A or B was run x (original) or y (evaluated).
Final grade per id/answer: adjudicated grade if any, else the mean of the votes (scores) / majority (flags).
"""
import json
import math
import pathlib
import sys

res = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
kp = pathlib.Path(sys.argv[2])
key = json.loads((kp / "_key.json" if kp.is_dir() else kp).read_text(encoding="utf-8"))
nx, ny = sys.argv[3], sys.argv[4]
names = {"x": nx, "y": ny}

by = {}
for g in res["grades"]:
    by.setdefault(g["id"], []).append(g)
adj = {g["id"]: g for g in res.get("adjudicated", [])}

rows = {nx: {}, ny: {}}
wins = {nx: 0, ny: 0, "tie": 0}
for qid, gs in by.items():
    final = [adj[qid]] if qid in adj else gs
    for slot in ("A", "B"):
        run = names[key[qid][slot]]
        sc = sum(g[slot]["score"] for g in final) / len(final)
        fe = sum(g[slot]["factual_error"] for g in final) / len(final) >= 0.5
        gov = sum(g[slot]["governing_source_cited"] for g in final) / len(final) >= 0.5
        pad = sum(g[slot]["padding"] for g in final) / len(final) >= 0.5
        rows[run][qid] = {"score": sc, "fe": fe, "gov": gov, "pad": pad,
                          "errors": [e for g in final for e in g[slot]["errors"]]}
    votes = [g["better"] for g in final]
    for v in votes:
        wins[names[key[qid][v]] if v in ("A", "B") else "tie"] += 1 / len(votes)


def ci(p, n):
    if n == 0:
        return (0, 0)
    z = 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0, c - h), min(1, c + h))


for run in (nx, ny):
    r = rows[run]
    n = len(r)
    if not n:
        continue
    mean = sum(v["score"] for v in r.values()) / n
    full = sum(v["score"] >= 2.75 for v in r.values())
    good = sum(v["score"] >= 2 for v in r.values())
    fe = sum(v["fe"] for v in r.values())
    lo, hi = ci(good / n, n)
    print(f"{run}: n={n} mean={mean:.2f}/3 ({100 * mean / 3:.0f}%) | fully correct(3)={full} ({100 * full / n:.0f}%) | "
          f"usable(>=2)={good} ({100 * good / n:.0f}%, 95% CI {100 * lo:.0f}-{100 * hi:.0f}) | factual errors={fe} ({100 * fe / n:.0f}%) | "
          f"governing source cited={sum(v['gov'] for v in r.values())} | padding={sum(v['pad'] for v in r.values())}")
print("head-to-head (better):", {k: round(v, 1) for k, v in wins.items()})
if len(sys.argv) > 5:
    items = {i["id"]: i for i in json.loads(pathlib.Path(sys.argv[5]).read_text(encoding="utf-8"))}
    groups = {}
    for qid, it in items.items():
        lv = it.get("group") or ("communal" if "communal" in (it.get("levels") or []) else
                                 "cantonal" if "cantonal" in (it.get("levels") or []) else "federal")
        groups.setdefault(lv, []).append(qid)
    for lv, ids in groups.items():
        print(f"  {lv:9s} " + " | ".join(
            f"{run}: mean {sum(rows[run][i]['score'] for i in ids if i in rows[run]) / max(1, sum(i in rows[run] for i in ids)):.2f}"
            f" err {sum(rows[run][i]['fe'] for i in ids if i in rows[run])}/{sum(i in rows[run] for i in ids)}" for run in (nx, ny)))
if "--write" in sys.argv:
    pathlib.Path(sys.argv[1]).with_suffix(".scored.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
