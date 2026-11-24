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
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from aeda import alfworld as A  # noqa: E402
from aeda.schema import read_jsonl, write_jsonl  # noqa: E402


def convert(ep: dict, max_samples: int | None = None):
    samples, labels = [], []
    steps = [(s["action"], s["observation"]) for s in ep["steps"]]
    base = [{"rid": 0, "source": "env", "text": ep.get("init_obs", ""), "entities": []}]
    for t, (action, obs) in enumerate(steps):
        name, _ = A.parse_action(action)
        if name not in A.STATE_CHANGING:
            continue
        prefix = steps[:t]
        records = base + [{"rid": i + 1, "source": "env", "text": A.record_text(a, o), "entities": []}
                          for i, (a, o) in enumerate(prefix)]
        # entity tags for filtered variants: receptacle/object names mentioned in the record
        st = A.replay(prefix)
        sid = f"{ep['episode_id']}-t{t}"
        claims, labs = [], []
        for j, pre in enumerate(A.preconditions(action)):
            cid = f"{sid}/c{j}"
            for r in records:
                # whole-name match, so "countertop 1" does not match "countertop 10"
                if any(e and re.search(rf"(?<![A-Za-z0-9_]){re.escape(e)}(?![A-Za-z0-9_])", r["text"].lower())
                       for e in pre["entities"]):
                    r["entities"] = sorted(set(r["entities"]) | set(pre["entities"]))
            claims.append({"cid": cid, "text": pre["text"], "kind": "state", "origin": "fixed",
                           "entities": pre["entities"], "spec": pre["spec"]})
            labs.append({"sid": sid, "cid": cid, "gold": A.evaluate_spec(pre["spec"], st),
                         "order_sensitive": None, "composition": False, "indirect": False,
                         "implicit_order": False, "synthetic": False,
                         "extra": {"label_source": "tracker", "action": action, "step": t,
                                   "action_succeeded": A.succeeded(obs), "spec_type": pre["spec"]["type"],
                                   "n_records": len(records)}})
        if not claims:
            continue
        samples.append({"sid": sid, "episode_id": ep["episode_id"], "task": ep["task"],
                        "proposed_action": action, "action_reversible": True, "window_complete": True,
                        "records": records, "claims": claims})
        labels += labs
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
