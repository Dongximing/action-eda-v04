"""Action-level view of a run on ALFWorld samples: a method blocks the proposed action
when any of its claims is CONTRADICTED. Compared against two references:

  tracker  : any claim contradicted by the tracker labels (what the fixed claims can catch)
  env      : the action actually failed in the environment ("Nothing happens"),
             which also includes failures outside the fixed preconditions

  python scripts/action_level.py --labels data/alfworld9b/labels.jsonl --run runs/alfworld9b/jev/ctx0
Writes <run>/action_level.md and prints it.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def read(p):
    return [json.loads(x) for x in Path(p).read_text(encoding="utf-8").splitlines() if x.strip()]


def score(pred: dict, ref: dict) -> dict:
    keys = sorted(ref)
    tp = sum(pred[k] and ref[k] for k in keys)
    fp = sum(pred[k] and not ref[k] for k in keys)
    fn = sum(not pred[k] and ref[k] for k in keys)
    neg = sum(not ref[k] for k in keys)
    return {"n": len(keys), "blocked": tp + fp, "tp": tp, "fp": fp, "fn": fn,
            "precision": tp / (tp + fp) if tp + fp else None,
            "recall": tp / (tp + fn) if tp + fn else None,
            "false_block_rate": fp / neg if neg else None}


def fmt(x):
    return "-" if x is None else f"{x:.3f}" if isinstance(x, float) else str(x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labels", required=True)
    ap.add_argument("--run", required=True, help="run dir with predictions.jsonl")
    a = ap.parse_args()
    labels = read(a.labels)
    ref_tracker, ref_env = defaultdict(bool), {}
    for l in labels:
        ref_tracker[l["sid"]] |= l["gold"] == "CONTRADICTED"
        ref_env[l["sid"]] = not l["extra"]["action_succeeded"]
    by_method = defaultdict(lambda: defaultdict(bool))
    unknown = defaultdict(lambda: defaultdict(bool))
    for r in read(Path(a.run) / "predictions.jsonl"):
        by_method[r["method"]][r["sid"]] |= r["verdict"] == "CONTRADICTED"
        unknown[r["method"]][r["sid"]] |= r["verdict"] == "UNKNOWN"
    lines = [f"# Action-level blocking: {a.run}", "",
             f"{len(ref_env)} proposed actions; tracker-contradicted {sum(ref_tracker.values())}, "
             f"failed in env {sum(ref_env.values())}.", "",
             "| method | ref | blocked | tp | fp | fn | precision | recall | false-block | actions with UNKNOWN |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for m in sorted(by_method):
        pred = {k: by_method[m].get(k, False) for k in ref_env}
        n_unk = sum(unknown[m].get(k, False) for k in ref_env)
        for name, ref in (("tracker", {k: ref_tracker[k] for k in ref_env}), ("env", ref_env)):
            s = score(pred, ref)
            lines.append(f"| {m} | {name} | {s['blocked']} | {s['tp']} | {s['fp']} | {s['fn']} | "
                         f"{fmt(s['precision'])} | {fmt(s['recall'])} | {fmt(s['false_block_rate'])} | {n_unk} |")
    text = "\n".join(lines)
    (Path(a.run) / "action_level.md").write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
