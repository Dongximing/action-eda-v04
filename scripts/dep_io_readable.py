#!/usr/bin/env python3
"""Readable full record of a react_dep / react_ptr_* game: every model input and output, the game reply, and the
controller's decision, step by step. Offline; reads <tag>_io.jsonl.gz (every request as sent) and <tag>.json.

  python3 scripts/dep_io_readable.py [--run runs/online/unseen] [--tag react_dep_t1536] [--games u047]

Each request repeats the whole conversation, so the first request is printed in full and every later one only with
the messages added since the request before it (the model's previous output and the new "Observation: ..." turn,
which carries the controller's "Check:" line or a "Not run" reply). Writes <run>/<game>/<tag>_io.md.
"""
from __future__ import annotations

import argparse
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=str(ROOT / "runs/online/unseen"))
    ap.add_argument("--tag", default="react_dep_t1536")
    ap.add_argument("--games", default="")
    a = ap.parse_args()
    want = {g for g in a.games.split(",") if g}
    for f in sorted(Path(a.run).glob(f"*/{a.tag}.json")):
        if want and f.parent.name not in want:
            continue
        r = json.loads(f.read_text())
        rows = [json.loads(l) for l in gzip.open(f.parent / f"{a.tag}_io.jsonl.gz", "rt")]
        H, dg = r["history"], r.get("dep_graph", {})
        settings = {k: v for k, v in rows[0]["request"]["payload"].items() if k != "messages"}
        md = [f"# {r['id']} / {a.tag}: every model input and output", "",
              f"Task: {r['task']}  |  result: {'won' if r['won'] else 'lost'} in {r['steps']} steps  |  requests: {len(rows)}, "
              f"{sum(x['from_cache'] for x in rows)} answered from the cache (identical to the ReAct run)", "",
              "Settings of every request: `" + json.dumps(settings, ensure_ascii=False) + "`", ""]
        prev = 0
        for x in rows:
            msgs = x["request"]["payload"]["messages"]
            step = x["env_step"] + 1                       # the env step this request chooses the command for
            md += [f"## Request {x['n']} (chooses the command for step {step}){'  [from cache]' if x['from_cache'] else ''}", ""]
            if prev == 0:
                md += ["**Model input: message 1 (user), the same in every request**", "", "```", msgs[0]["content"], "```", ""]
                new = msgs[1:]
            else:
                new = msgs[prev:]
                md += [f"**Model input ({len(msgs)} messages): the {prev} messages of the request before, plus**", ""]
            for m in new:
                md += [f"_{m['role']}_", "", "```", m["content"], "```", ""]
            prev = len(msgs)
            out = x["raw_output"] if x["raw_output"] is not None else x["answer"]
            md += ["**Model output**", "", "```", out, "```", ""]
            if step < len(H):
                b = dg.get("blocked", {}).get(str(step))
                if b:
                    md.append(f"**Controller before running:** not run. {b['told']} Ran instead: `{b['ran_instead']}`")
                md.append(f"**Environment ran:** `{H[step]['action']}` -> {H[step]['observation'].strip()}")
                n = dg.get("notes", {}).get(str(step))
                if n:
                    md.append(f"**Controller after the reply (shown to the model in the next request):** {n}")
                md.append("")
        out_path = f.parent / f"{a.tag}_io.md"
        out_path.write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"{out_path.relative_to(ROOT)}: {len(rows)} requests")


if __name__ == "__main__":
    main()
