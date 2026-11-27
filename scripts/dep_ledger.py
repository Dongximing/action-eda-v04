#!/usr/bin/env python3
"""The controller's ledger at every step of a finished react_dep (or react_ptr_*) game. Offline, no model calls.

  python3 scripts/dep_ledger.py [--run runs/online/unseen] [--tag react_dep_t1536] [--games u047,u083]

The controller (scripts/dep_graph.py) is fixed code, so feeding it the saved game record again rebuilds its ledger
exactly. For each step: the agent's command, what the environment ran, the feedback, the beliefs that command
depends on with their evidence level, the controller's decision, and the ledger after the step. Every replayed
note and block is checked against the ones saved during the run; a mismatch is reported.
Writes <run>/<game>/<tag>_ledger.md and, when the run did not save one, <tag>_graph.jsonl.gz (the whole graph,
nodes and typed edges, after every step; one JSON line per step).
"""
from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from dep_graph import DepGraph  # noqa: E402

MARK = {"supported": "有证据", "unsupported": "没证据", "refuted": "被否定", "ruled_out": "已排除"}


def ledger(r: dict, tag: str) -> tuple[list[str], list[str], list[dict]]:
    H, dg = r["history"], r["dep_graph"]
    agent_cmd = {e["step"] + 1: e.get("action") for e in r.get("place_lists", [])}
    blocked = {int(k): v for k, v in dg["blocked"].items()}
    saved_notes = {int(k): v for k, v in dg["notes"].items()}
    G = DepGraph(r["task"], H[0]["observation"], hops=dg.get("hops", 1))
    graphs = []
    lines = [f"# {r['id']} / {tag}: the controller's ledger at every step", "",
             f"Task: {r['task']}  |  result: {'won' if r['won'] else 'lost'} in {r['steps']} steps", "",
             "Evidence levels: 有证据 = a game reply says so; 没证据 = only assumed; 被否定 = a game reply contradicts it; "
             "已排除 = chosen as a culprit and ruled out.", ""]
    problems = []
    for i in range(1, len(H)):
        cmd = agent_cmd.get(i)
        ran, obs = H[i]["action"], H[i]["observation"] or ""
        error = cmd is None
        lines += [f"## Step {i}", "", f"- agent's command: `{cmd if cmd is not None else '(no Action in its output)'}`"]
        if ran != cmd:
            lines.append(f"- environment ran: `{ran}`")
        lines.append(f"- game reply: {obs.strip()}")
        if not error:
            look = copy.deepcopy(G)                      # the displayed levels must not change the real ledger
            deps = look.deps(cmd)
            if deps:
                lines.append("- this command depends on: " + "; ".join(
                    f"\"{look.text(k)}\" {MARK[look.level(k, i)[0]]}" for k in deps))
            decided = G.before(i, cmd)
            if bool(decided) != (i in blocked) or (decided and decided[0] != blocked[i]["ran_instead"]):
                problems.append(f"step {i}: block differs (replay {decided}, run {blocked.get(i)})")
            if decided:
                lines.append(f"- **decision before running: not run.** {decided[1]} Ran instead: `{decided[0]}`")
        G.update(i, ran, obs)
        note = G.after(i, ran, obs, ran_as_agent=not error and i not in blocked)
        if tag.startswith("react_dep") and note != saved_notes.get(i):
            problems.append(f"step {i}: note differs")
        if note:
            told = saved_notes.get(i, note)
            lines.append(f"- **decision after the reply:** {told}")
        graphs.append({**G.graph_at(i), "note": saved_notes.get(i), "blocked": blocked.get(i)})
        snap = G.snapshot(i)
        taken = "; ".join(f"{b['belief']} [{MARK[b['level']]}, step {b['step']}]" for b in snap["taken_for_task"]) or "-"
        ruled = "; ".join(f"{b['belief']} (step {b['at_step']})" for b in snap["ruled_out"]) or "-"
        lines += [f"- ledger after step {i}: at **{snap['location']}** (step {snap['location_step']}), holding "
                  f"**{snap['holding']}**" + (f" (step {snap['holding_step']})" if snap['holding'] != 'nothing' else "") +
                  f"; taken for the task: {taken}; done: {', '.join(snap['transforms_done']) or '-'}; "
                  f"tools that worked: {', '.join(snap['tools_known']) or '-'}; ruled out: {ruled}", ""]
    return lines, problems, graphs


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
        lines, problems, graphs = ledger(r, a.tag)
        out = f.parent / f"{a.tag}_ledger.md"
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        gpath = f.parent / f"{a.tag}_graph.jsonl.gz"
        if not gpath.exists():
            import gzip
            with gzip.open(gpath, "wt", encoding="utf-8") as fh:
                for x in graphs:
                    fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        print(f"{out.relative_to(ROOT)}: {r['steps']} steps, " + ("replay matches the run" if not problems else "MISMATCH: " + "; ".join(problems)))


if __name__ == "__main__":
    main()
