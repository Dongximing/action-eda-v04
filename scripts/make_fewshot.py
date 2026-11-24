"""Build few-shot worked examples for the per-record judgment from demonstration
trajectories that are NOT test episodes (default: the three ReAct Act-only demos
the main agent saw, data/fewshot/react_act_examples.json; MIT, see LICENSE-ReAct).

Labels come from the tracker comparing the state right before and right after one
record, so nothing is hand-labelled:
  A  the record makes the condition true      (go to X -> "at X"; take O -> "holding O";
                                               move O -> "holding nothing")
  B  the record makes the condition false     (go to Y while at X -> "at X";
                                               take O -> "holding nothing"; move O -> "holding O")
  C  the record says nothing about it         ("holding O" while only walking around)
Only these unambiguous patterns are used. One example per pattern, round-robin over
the demos, in a fixed order (no randomness).

  python scripts/make_fewshot.py --out data/fewshot/alfworld_record_fewshot.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aeda import alfworld as A  # noqa: E402

# (answer, pattern) in the order they are shown; balanced 3 A / 3 B / 2 C
PATTERNS = [("A", "arrive"), ("B", "leave"), ("C", "walk_holding"), ("A", "take"),
            ("B", "take_empty"), ("A", "move_empty"), ("B", "move_holding"), ("C", "walk_holding")]


def parse_demo(text: str) -> list[tuple[str, str]]:
    steps, action = [], None
    for line in text.splitlines():
        if line.startswith("Action: "):
            raw = line[len("Action: "):].strip()
            action = json.loads(raw)["action"] if raw.startswith("{") else raw
        elif line.startswith("Observation: ") and action is not None:
            steps.append((action, line[len("Observation: "):].strip()))
            action = None
    return steps


def candidates(steps: list[tuple[str, str]]) -> list[dict]:
    out = []
    for i, (act, obs) in enumerate(steps):
        if not A.succeeded(obs):
            continue
        before, after = A.replay(steps[:i]), A.replay(steps[:i + 1])
        name, args = A.parse_action(act)
        rec = A.record_text(act, obs)

        def add(pattern, answer, cond):
            out.append({"pattern": pattern, "answer": answer, "condition": cond, "record": rec, "step": i})
        if name == "goto" and before.loc != after.loc:
            add("arrive", "A", f"The agent is currently at {after.loc}")
            if before.loc:
                add("leave", "B", f"The agent is currently at {before.loc}")
            if before.holding and before.holding not in rec.lower():
                add("walk_holding", "C", f"The agent is currently holding {before.holding}")
        elif name == "take" and before.holding is None:
            add("take", "A", f"The agent is currently holding {args[0]}")
            add("take_empty", "B", "The agent is currently holding nothing")
        elif name == "put" and before.holding:
            add("move_empty", "A", "The agent is currently holding nothing")
            add("move_holding", "B", f"The agent is currently holding {before.holding}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demos", default=str(ROOT / "data/fewshot/react_act_examples.json"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=len(PATTERNS), help="use the first n patterns")
    a = ap.parse_args()
    src = json.loads(Path(a.demos).read_text(encoding="utf-8"))
    demos = [(v["id"], parse_demo(v["text"])) for v in src["examples"].values()]
    pools = [(did, candidates(steps)) for did, steps in demos]
    chosen, used = [], set()
    for j, (ans, pat) in enumerate(PATTERNS[:a.n]):
        for k in range(len(pools)):  # round-robin start so demos are mixed
            did, cands = pools[(j + k) % len(pools)]
            hit = next((c for c in cands if c["pattern"] == pat and (did, c["step"], pat) not in used), None)
            if hit:
                used.add((did, hit["step"], pat))
                chosen.append({**hit, "source": did})
                break
        else:
            raise SystemExit(f"no demo step for pattern {pat}")
    out = {"source": a.demos, "source_sha256": hashlib.sha256(Path(a.demos).read_bytes()).hexdigest(),
           "rule": __doc__.split("\n\n")[1].strip(), "examples": chosen}
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    for e in chosen:
        print(f"{e['answer']}  [{e['source']} step {e['step']}] {e['condition']}  <=  {e['record'][:70]!r}")


if __name__ == "__main__":
    main()
