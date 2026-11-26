#!/usr/bin/env python3
"""Where do lost games get stuck? Offline analysis of finished trajectories (no API calls).

  python scripts/analyze_losses.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3 --arm llm

For every lost game of --arm (and of the baseline on the same games) it reports:

  stage reached   how far the agent got toward the task:
                    not_found     the target object type never appeared in any observation
                    found         seen, but never picked up
                    wrong_object  picked up only objects of another type (e.g. soapbottle for soapbar)
                    taken         picked up the target, but clean / heat / cool never succeeded
                    transformed   the clean / heat / cool succeeded, but it was never placed in the target
  wasted steps    "Nothing happens" steps; repeated look / inventory / examine (same observation as the
                  previous step); steps after the last new observation (the stuck tail)
  longest repeat  longest run of the same action in a row
  closed unopened receptacles the agent reached while closed and never opened

Writes <out>/losses.md and <out>/losses.jsonl (default out: runs/online).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from aeda import alfworld as A  # noqa: E402

SRC = Path.home() / "Documents/Codex/2026-11-21/yo/outputs/alfworld-9b-oneshot-alternate"
TASK = [re.compile(r"put an? (clean|hot|cool) (\w+) in (\w+)"),
        re.compile(r"(clean|heat|cool) some (\w+) and put it in (\w+)")]
VERB = {"clean": "clean", "hot": "heat", "heat": "heat", "cool": "cool"}
IDLE = {"look", "inventory"}
STAGES = ["not_found", "found", "wrong_object", "taken", "transformed"]


def parse_task(task: str) -> tuple[str, str, str]:
    for p in TASK:
        m = p.search(task.lower())
        if m:
            return VERB[m.group(1)], m.group(2), m.group(3)
    raise ValueError(f"unknown task {task!r}")


def baseline_history(game_dir: Path, gid: str) -> list[dict] | None:
    if (game_dir / "direct.json").exists():
        return json.loads((game_dir / "direct.json").read_text())["history"]
    if (SRC / gid / "natural.json").exists():
        return json.loads((SRC / gid / "natural.json").read_text())["history"]
    return None


def analyze(task: str, history: list[dict]) -> dict:
    verb, obj, recep = parse_task(task)
    is_obj = re.compile(rf"\b{re.escape(obj)} \d+\b")
    steps = history[1:]
    stage, picked, wrong = "not_found", None, []
    seen_obs, last_new, run, best, prev_act = set(), 0, 0, (0, ""), None
    nothing = idle = 0
    closed, opened = set(), set()
    for i, h in enumerate(steps, 1):
        act, obs = h["action"].strip().lower(), h["observation"]
        ok = A.succeeded(obs)
        name, args = A.parse_action(act)
        nothing += not ok
        if act.split()[0] in IDLE or act.startswith("examine"):
            idle += i > 1 and obs == steps[i - 2]["observation"]
        if obs not in seen_obs:
            seen_obs.add(obs)
            last_new = i
        run = run + 1 if act == prev_act else 1
        prev_act = act
        if run > best[0]:
            best = (run, act)
        m = re.match(r"you arrive at (\w+ \d+)\. the \w+ \d+ is closed", obs.lower())
        if m:
            closed.add(m.group(1))
        if name == "open" and ok:
            opened.add(args[0])
        # stage
        if stage == "not_found" and is_obj.search(obs.lower()):
            stage = "found"
        if name == "take" and ok:
            if is_obj.fullmatch(args[0]):
                stage, picked = "taken", args[0]
            elif stage in ("not_found", "found", "wrong_object"):
                wrong.append(args[0])
                stage = "wrong_object"
        if name == verb and ok and picked and args[0] == picked and stage == "taken":
            stage = "transformed"
    return {"verb": verb, "object": obj, "receptacle": recep, "stage": stage, "wrong_objects": wrong,
            "steps": len(steps), "nothing_happens": nothing, "idle_repeats": idle,
            "stuck_tail": len(steps) - last_new, "longest_repeat": best[0], "longest_repeat_action": best[1],
            "closed_unopened": sorted(closed - opened)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--arm", default="llm")
    ap.add_argument("--out", default="runs/online")
    a = ap.parse_args()
    rows = []
    for d in a.dirs:
        for f in sorted(Path(d).glob(f"*/{a.arm}.json")):
            r = json.loads(f.read_text())
            if r["won"]:
                continue
            row = {"id": r["id"], "family": r["family"], "task": r["task"], "arm": a.arm, **analyze(r["task"], r["history"])}
            bh = baseline_history(f.parent, r["id"])
            row["baseline"] = None if bh is None or r["baseline_won"] else analyze(r["task"], bh)
            rows.append(row)
    out = Path(a.out)
    with (out / "losses.jsonl").open("w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    def block(label, items):
        n = len(items)
        if not n:
            return [f"## {label}: no lost games", ""]
        st = Counter(x["stage"] for x in items)
        tot = sum(x["steps"] for x in items)
        lines = [f"## {label}: {n} lost games, {tot} steps", "",
                 "| stage reached | games |", "|---|---|"]
        lines += [f"| {s} | {st[s]} |" for s in STAGES]
        lines += ["", "| wasted steps | steps | share of all steps |", "|---|---|---|"]
        for k, name in [("nothing_happens", "\"Nothing happens\""), ("idle_repeats", "repeated look / inventory"),
                        ("stuck_tail", "after the last new observation")]:
            v = sum(x[k] for x in items)
            lines.append(f"| {name} | {v} | {100 * v / tot:.0f}% |")
        lr = [x["longest_repeat"] for x in items]
        lines += ["", f"Games with the same action {10}+ times in a row: {sum(v >= 10 for v in lr)}/{n}; "
                      f"with a stuck tail of 20+ steps: {sum(x['stuck_tail'] >= 20 for x in items)}/{n}; "
                      f"with a closed receptacle reached but never opened: {sum(bool(x['closed_unopened']) for x in items)}/{n}.", ""]
        return lines

    lines = [f"# Where lost games get stuck ({a.arm} and baseline)", ""]
    lines += block(a.arm, rows)
    lines += block("baseline (same games, lost there too)", [r["baseline"] for r in rows if r["baseline"]])
    lines += ["## Per game", "",
              f"| game | task | stage | wrong object | Nothing happens | stuck tail | longest repeat | baseline stage |",
              "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        b = r["baseline"]
        lines.append(f"| {r['id']} | {r['task']} | {r['stage']} | {', '.join(r['wrong_objects']) or '-'} | "
                     f"{r['nothing_happens']} | {r['stuck_tail']} | {r['longest_repeat']}x `{r['longest_repeat_action']}` | "
                     f"{b['stage'] if b else 'n/a'} |")
    text = "\n".join(lines) + "\n"
    (out / "losses.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
