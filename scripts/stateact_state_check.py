#!/usr/bin/env python3
"""Official StateAct runs: is the state the agent writes right, and does it act on it? Offline, reads their traces.

  python3 scripts/stateact_state_check.py [--trial qwen35_9b_unseen_lost35] [--show u101]

Each StateAct turn writes "current location" and "current inventory" before its action. These are compared with the
state read from the feedback text so far (analyze_loops.State; location from "You arrive at", held object from
"You pick up" / "You move"). Also counted: actions that contradict the agent's own written state (acting on a place
other than its written location; heat/cool/clean/put while its written inventory is None).
Games are matched to our ids by the opening room text and task (runs/online/unseen/*/react_std_t1536.json).
Writes runs/online/analysis/stateact_state_<trial>.md.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_loops import ENT, State  # noqa: E402

LOGS = ROOT / "third_party/stateact/official/StateAct/alfworld_runs/game_logs"


def field(text: str, name: str) -> str | None:
    """The value of a state line; the model sometimes drops "current " ("inventory: ..."). None: the line is missing."""
    for n in (name, name.replace("current ", "")):
        m = re.search(rf"^>?{n}:\s*(.*)$", text, re.M)
        if m:
            return m.group(1).strip()
    return None


def command(text: str) -> str:
    a = (field(text, "action") or "").strip()
    m = re.match(r"put\s+(.*?)\s+(?:in/on|in|on)\s+(.*)$", a)
    return f"move {m.group(1)} to {m.group(2)}" if m else a


def ours() -> dict:
    """(room text, task) -> [(our id, arrival texts)]; several games can share a room and a task."""
    out = {}
    for f in sorted((ROOT / "runs/online/unseen").glob("*/react_std_t1536.json")):
        r = json.loads(f.read_text())
        room = r["history"][0]["observation"].split("\n\n", 1)[-1].strip()
        out.setdefault((room, r["task"].strip().lower()), []).append((f.parent.name, arrivals([h["observation"] for h in r["history"][1:]])))
    return out


def arrivals(observations: list[str]) -> dict:
    """First 'You arrive at X ...' / 'You open the X ...' text per receptacle: what it held before anyone moved things."""
    out = {}
    for o in observations:
        m = re.match(rf"you (?:arrive at|open the) ({ENT})", (o or "").strip().lower())
        if m and m.group(1) not in out:
            out[m.group(1)] = " ".join(o.lower().split())
    return out


def match(cands: list, trace_obs: list[str]) -> str:
    """The candidate whose receptacle contents agree with the trace's (ties and no overlap: first candidate)."""
    seen = arrivals(trace_obs)
    def score(c):
        same = sum(1 for k, v in c[1].items() if k in seen and seen[k] == v)
        diff = sum(1 for k, v in c[1].items() if k in seen and seen[k] != v)
        return same - 2 * diff
    return max(cands, key=score)[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", default="qwen35_9b_unseen_lost35")
    ap.add_argument("--show", default="")
    a = ap.parse_args()
    d = LOGS / f"alfworld_eval_{a.trial}"
    rows = list(csv.DictReader(open(d / "alfworld_results.csv")))
    idx = ours()
    proto = {g["id"]: g for g in json.loads((ROOT / "runs/online/unseen/protocol.json").read_text())["games"]}
    md = [f"# StateAct ({a.trial}): written state vs the state in the feedback", "",
          "| game | type | result | steps | early stop | location wrong | inventory wrong | acts away from its written location | "
          "transform/put with written inventory None |", "|---|---|---|---|---|---|---|---|---|"]
    tot = {"steps": 0, "loc": 0, "inv": 0, "away": 0, "empty": 0}
    for r in rows:
        tr = json.loads((d / os.path.basename(r["trace_file"])).read_text())
        first = tr[1]["content"]
        room, task = first.split("\nYour task is to: ")[0].strip(), first.split("Your task is to: ")[1].strip()
        gid = match(idx[(room, task.lower())], [m["content"] for m in tr[2:] if m["role"] == "user"])
        st = State()
        steps = loc_bad = inv_bad = away = empty = 0
        lines = []
        turns = [(tr[j]["content"], tr[j + 1]["content"] if j + 1 < len(tr) else "") for j in range(len(tr)) if tr[j]["role"] == "assistant"]
        for k, (out, obs) in enumerate(turns, 1):
            wl, wi, cmd = field(out, "current location"), field(out, "current inventory"), command(out)
            real_loc, real_held = st.loc or "starting location", st.held or "None"
            lbad = wl is not None and wl.lower() != real_loc
            ibad = wi is not None and (wi.lower() in ("none", "nothing", "empty", "")) != (real_held == "None") or \
                (wi and real_held != "None" and real_held not in wi.lower())
            ents = re.findall(ENT, cmd.lower())
            tgt = ents[-1] if ents else None
            acts_away = bool(tgt and wl and re.match(r"(take|move|open|close|heat|cool|clean)\b", cmd.lower()) and tgt != wl.lower())
            empty_hand = bool(re.match(r"(move|heat|cool|clean)\b", cmd.lower()) and wi and wi.lower() in ("none", "nothing", "empty"))
            steps += 1
            loc_bad += lbad
            inv_bad += bool(ibad)
            away += acts_away
            empty += empty_hand
            lines.append(f"| {k} | {wl if wl is not None else '(missing)'} {'✗(real: ' + real_loc + ')' if lbad else ''} | {wi if wi is not None else '(missing)'} {'✗(real: ' + real_held + ')' if ibad else ''} | "
                         f"{cmd}{' ←away' if acts_away else ''}{' ←empty hand' if empty_hand else ''} | {obs.strip()[:70]} |")
            st.update(k, cmd, obs)
        for key, v in (("steps", steps), ("loc", loc_bad), ("inv", inv_bad), ("away", away), ("empty", empty)):
            tot[key] += v
        won = r["success"] == "True"
        md.append(f"| {gid} | {proto[gid]['family'].replace('_then_place_in_recep', '').replace('pick_', '')} | {'won' if won else 'lost'} | "
                  f"{r['num_of_steps']} | {r['early_stop'] or '-'} | {loc_bad} | {inv_bad} | {away} | {empty} |")
        if gid in a.show.split(","):
            print(f"\n## {gid}: {task}  ({'won' if won else 'lost'})\n\n| # | written location | written inventory | command | feedback |\n|---|---|---|---|---|")
            print("\n".join(lines))
    md += ["", f"All finished games: {tot['steps']} turns; written location wrong {tot['loc']}, written inventory wrong {tot['inv']}, "
           f"acts away from its own written location {tot['away']}, transform/put with its own written inventory None {tot['empty']}."]
    (ROOT / f"runs/online/analysis/stateact_state_{a.trial}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
