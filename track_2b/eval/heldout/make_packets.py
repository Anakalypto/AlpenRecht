"""Build blind, paired grading packets: one markdown file per question with Answer A / Answer B.

usage: python -I make_packets.py <set.json> <run_x.jsonl> <run_y.jsonl> <out_dir> [<reference.json>]
Which run is A or B is decided per question by a hash of the id (so graders can't learn a pattern);
the key is written to <out_dir>/_key.json, which graders never see.
"""
import hashlib
import json
import pathlib
import sys

set_path, xa, ya, out_dir = sys.argv[1:5]
ref_path = sys.argv[5] if len(sys.argv) > 5 else None
items = {i["id"]: i for i in json.loads(pathlib.Path(set_path).read_text(encoding="utf-8"))}
refs = {r["id"]: r for r in json.loads(pathlib.Path(ref_path).read_text(encoding="utf-8"))} if ref_path else {}


def load(p):
    rows = {}
    for line in pathlib.Path(p).read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            rows[r["id"]] = r
    return rows


X, Y = load(xa), load(ya)
out = pathlib.Path(out_dir)
out.mkdir(parents=True, exist_ok=True)
key = {}


def render(label, r):
    if r is None:
        return f"## Answer {label}\n\n(NO RUN RECORDED)\n"
    if r.get("answer"):
        body = r["answer"]
    else:
        body = f"(NO ANSWER PRODUCED. error: {r.get('error_event') or r.get('exception') or 'none'})"
    src = "\n".join(f"- [{s['id']}] {s['level']} · {s['law']} · {s['number']} · {s.get('title', '')[:90]} · {s.get('url', '')}\n"
                    f"  excerpt: {' '.join((s.get('excerpt') or '').split())[:500]}" for s in r.get("sources") or [])
    return f"## Answer {label}\n\n{body}\n\n### Sources shown with Answer {label}\n{src or '(none)'}\n"


for qid, it in items.items():
    flip = int(hashlib.sha1(qid.encode()).hexdigest(), 16) % 2 == 1
    a, b = (Y.get(qid), X.get(qid)) if flip else (X.get(qid), Y.get(qid))
    key[qid] = {"A": "y" if flip else "x", "B": "x" if flip else "y"}
    ref = refs.get(qid)
    ref_txt = ""
    if ref:
        gold = "\n".join(f"- {g['act']} (SR {g.get('sr', '')}) art. {g['article']}: \"{g.get('quote', '')}\" <{g.get('url', '')}>"
                         for g in ref.get("gold_sources", []))
        ref_txt = (f"\n## Reference (verified against the official text)\n{ref['reference_answer']}\n\nKey facts:\n"
                   + "\n".join(f"- {k}" for k in ref.get("key_facts", []))
                   + "\n\nCommon errors to watch for:\n" + "\n".join(f"- {k}" for k in ref.get("common_errors", []))
                   + f"\n\nGoverning sources:\n{gold}\n")
    text = (f"# {qid}\n\nQuestion ({it['lang']}): {it['q']}\nPlace: {it['loc']}\n{ref_txt}\n"
            + render("A", a) + "\n" + render("B", b))
    (out / f"{qid}.md").write_text(text, encoding="utf-8")
(out / "_key.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
print(f"{len(items)} packets -> {out}")
