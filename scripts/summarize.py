"""Collect report.json files under a root into one markdown summary.

  python scripts/summarize.py --root runs/sweep/diag
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

COLS = [("all", "all"), ("order_sensitive", "True"), ("composition", "True"), ("indirect", "True"),
        ("ref", "anaphoric")]
KEY_DIFFS = [("D1", "U1", "order_sensitive=True"), ("D1", "H1", "order_sensitive=True"),
             ("D2", "D1", "composition=True"), ("D1", "E1", "all=all"), ("D1", "P0", "all=all"),
             ("D1", "Q0", "all=all")]


def fmt(x):
    return "-" if x is None else (f"{x:.3f}" if isinstance(x, float) else str(x))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    a = ap.parse_args()
    reports = sorted(Path(a.root).rglob("report.json"))
    if not reports:
        print(f"no report.json under {a.root}")
        return
    lines = ["# Summary", "", "Decidable accuracy by stratum (n in parentheses); fb = false-block rate on SUPPORTED gold.", ""]
    head = ["run", "method"] + [f"{d}={v}" for d, v in COLS] + ["fb(all)", "unknown(all)", "calls/claim"]
    lines += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    diff_lines = ["", "## Key paired differences (decidable accuracy, episode bootstrap 95% CI)", "",
                  "| run | a | b | stratum | n | diff | CI |", "|---|---|---|---|---|---|---|"]
    for rp in reports:
        run = str(rp.parent.relative_to(a.root))
        rep = json.loads(rp.read_text(encoding="utf-8"))
        idx = {(r["method"], r["stratum"], r["value"]): r for r in rep["table"]}
        for meth in sorted({r["method"] for r in rep["table"]}):
            cells = []
            for d, v in COLS:
                r = idx.get((meth, d, v))
                cells.append(f"{fmt(r.get('acc_decidable'))} ({r['n_decidable']})" if r else "-")
            allr = idx.get((meth, "all", "all"), {})
            lines.append("| " + " | ".join([run, meth] + cells + [fmt(allr.get("false_block_rate")),
                                                                   fmt(allr.get("unknown_rate")),
                                                                   fmt(allr.get("mean_calls"))]) + " |")
        for x, y, st in KEY_DIFFS:
            for d in rep["diffs"]:
                if d["a"] == x and d["b"] == y and d["stratum"] == st:
                    diff_lines.append(f"| {run} | {x} | {y} | {st} | {d['n_claims']} | {d['diff']:+.3f} | "
                                      f"[{d['ci95'][0]:+.3f}, {d['ci95'][1]:+.3f}] |")
        meta_p = rp.parent / "run_meta.json"
        if meta_p.exists():
            m = json.loads(meta_p.read_text(encoding="utf-8"))
            lines.append(f"| {run} | _meta_ | backend={m['backend']} ctx={m['config'].get('context_k')} "
                         f"prompt={m['prompt_version']} wall={m['wall_seconds']:.0f}s errors={m['errors']} |" + " |" * (len(head) - 3))
    print("\n".join(lines + diff_lines))


if __name__ == "__main__":
    main()
