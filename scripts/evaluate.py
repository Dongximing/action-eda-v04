"""Score predictions against private labels; writes report.md and report.json.

  python scripts/evaluate.py --samples data/smoke/samples.jsonl \
      --labels data/smoke/labels.jsonl --run runs/smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aeda.evaluate import DEFAULT_PAIRS, join, paired_bootstrap, stratified_table, to_markdown  # noqa: E402
from aeda.schema import load_labels, load_samples, read_jsonl  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--run", required=True, help="directory containing predictions.jsonl")
    ap.add_argument("--n-boot", type=int, default=2000)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()

    run = Path(a.run)
    joined, missing = join(read_jsonl(run / "predictions.jsonl"), load_labels(a.labels),
                           load_samples(a.samples))
    table = stratified_table(joined)
    diffs = []
    for x, y in DEFAULT_PAIRS:
        for st in [("all", "all"), ("order_sensitive", "True"), ("order_sensitive", "False"),
                   ("composition", "True"), ("indirect", "True"), ("ref", "anaphoric"),
                   ("origin", "dynamic"), ("origin", "fixed")]:
            d = paired_bootstrap(joined, x, y, st, n_boot=a.n_boot, seed=a.seed)
            if d:
                diffs.append(d)
    (run / "report.json").write_text(json.dumps({"table": table, "diffs": diffs, "missing_labels": missing},
                                                ensure_ascii=False, indent=2), encoding="utf-8")
    md = to_markdown(table, diffs)
    (run / "report.md").write_text(md + "\n", encoding="utf-8")
    print(md)
    if missing:
        print(f"\n[warn] {missing} predictions had no label")


if __name__ == "__main__":
    main()
