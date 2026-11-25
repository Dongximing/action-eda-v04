"""Convert ALFWorld trajectories into pre-action verification samples (negative control).

For every state-changing proposed action (take/put/open/close/clean/heat/cool) one
sample is written. Its records are the steps BEFORE that action; its claims are
the fixed preconditions from the public action semantics (aeda.alfworld.preconditions).

Labels: gold comes from the deterministic tracker over the same visible prefix
(label_source="tracker"). This is circular for T0 by construction: the control
asks whether model-based verifiers reach the tracker, not whether the tracker is
right. Whether the real action then succeeded ("Nothing happens" or not) is stored
in labels.extra.action_succeeded for analysis; it is never shown to verifiers.

  python scripts/convert_alfworld.py --traj my_alfworld_logs.jsonl --out data/alfworld
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aeda import alfworld as A  # noqa: E402
from aeda.schema import read_jsonl, write_jsonl  # noqa: E402


def convert(ep: dict, max_samples: int | None = None):
    samples, labels = [], []
    steps = [(s["action"], s["observation"]) for s in ep["steps"]]
    for t, (action, obs) in enumerate(steps):
        name, _ = A.parse_action(action)
        if name not in A.STATE_CHANGING:
            continue
        sample = A.build_sample(ep["episode_id"], ep["task"], ep.get("init_obs", ""), steps, t, action)
        if sample is None:
            continue
        st = A.replay(steps[:t])
        for c in sample["claims"]:
            labels.append({"sid": sample["sid"], "cid": c["cid"], "gold": A.evaluate_spec(c["spec"], st),
                           "order_sensitive": None, "composition": False, "indirect": False,
                           "implicit_order": False, "synthetic": False,
                           "extra": {"label_source": "tracker", "action": action, "step": t,
                                     "action_succeeded": A.succeeded(obs), "spec_type": c["spec"]["type"],
                                     "n_records": len(sample["records"])}})
        samples.append(sample)
        if max_samples and len(samples) >= max_samples:
            break
    return samples, labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--traj", required=True, help="JSONL, one episode per line (see aeda/alfworld.py)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-per-episode", type=int, default=None)
    a = ap.parse_args()
    samples, labels = [], []
    for ep in read_jsonl(a.traj):
        s, l = convert(ep, a.max_per_episode)
        samples += s
        labels += l
    out = Path(a.out)
    write_jsonl(out / "samples.jsonl", samples)
    write_jsonl(out / "labels.jsonl", labels)
    n_c = sum(l["gold"] == "CONTRADICTED" for l in labels)
    print(f"{len(samples)} samples, {len(labels)} claims ({n_c} contradicted by tracker) -> {out}")
    print(json.dumps({"note": "labels come from the tracker; see script docstring"}))


if __name__ == "__main__":
    main()
