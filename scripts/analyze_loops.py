#!/usr/bin/env python3
"""Claim 1 of docs/early_error_study_design.md: are action loops caused by an earlier error? Offline, no API calls.

  python3 scripts/analyze_loops.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3 --arm react_std

For every game of --arm:
  loop        two definitions, both reported:
              stuck  the first window of >= w consecutive steps that bring no new information: every feedback is
                     "Nothing happens" or was already seen earlier in the episode (w = 5; 3 and 8 for sensitivity).
                     This also catches cycles of different commands (go to microwave, open, heat, close, ...), the
                     usual loop of an agent that writes thoughts. t_L = the window's first step. (primary)
              repeat the first run of >= 3 identical consecutive commands (the loop of an action-only agent).
  state       rebuilt from the feedback text only: location, carried object, open/closed receptacles, what was seen
              where, and which objects were heated / cooled / cleaned.
  why         why the looped command fails at t_L, from the ALFWorld preconditions in the agent's own action guide:
              go to the place you are at; take while holding something / not at the place / object not there;
              put/heat/cool/clean without holding that object or not at the place; open/close in the wrong state or
              place; a command that names nothing in the game (malformed); or it succeeds (a loop of a working command).
  origin      the step that created the failing condition, traced back in the history:
                not holding the object  -> the step that put it down, or that took something else (wrong object)
                holding something else  -> the step that took it (wrong object if it is not the task's object)
                object not at the place -> the step that moved it away, or none if it was never there (hallucinated)
                receptacle closed       -> the step that closed it, or none if never opened
              An origin before t_L is an earlier error; "none" means nothing earlier explains the loop (the
              agent's own misconception starts at the loop).
Also lists, before t_L, the first wrong-object take and the first time the task object was put down somewhere that
is not the goal before the task was done. Writes <out>/loops_<arm>.md and .jsonl (default out runs/online/analysis).
"""
from __future__ import annotations

import argparse
import collections
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = [re.compile(r"put an? (clean|hot|cool) (\w+) in (\w+)"), re.compile(r"(clean|heat|cool) some (\w+) and put it in (\w+)")]
VERB = {"clean": "clean", "hot": "heat", "heat": "heat", "cool": "cool"}
# the other ALFWorld task types (valid_unseen): (verb, object, goal receptacle); verb None = nothing to do to the object
TASK_OTHER = [(re.compile(r"(?:put two|find two) (\w+) (?:and put them )?(?:in|on) (\w+)"), lambda m: (None, m.group(1), m.group(2))),
              (re.compile(r"(?:examine the|look at) (\w+) (?:with|under) the (\w+)"), lambda m: (None, m.group(1), None)),
              (re.compile(r"put (?:an?|some) (\w+) (?:in|on) (\w+)"), lambda m: (None, m.group(1), m.group(2)))]
ENT = r"[a-z]+ \d+"


def parse_task(task: str):
    t = task.lower()
    for p in TASK:
        m = p.search(t)
        if m:
            return VERB[m.group(1)], m.group(2), m.group(3)
    for p, f in TASK_OTHER:
        m = p.search(t)
        if m:
            return f(m)
    return None, None, None


def seen_items(text: str) -> set[str]:
    m = re.search(r"you see (.*)", text)
    return set(re.findall(rf"\b({ENT})\b", m.group(1))) if m else set()


class State:
    def __init__(self):
        self.loc, self.held, self.closed = None, None, {}
        self.where: dict[str, str] = {}          # object -> receptacle it was last seen in/on
        self.done: dict[str, set] = collections.defaultdict(set)
        self.held_since = None                    # step that set .held (to an object or to None)

    def update(self, step: int, act: str, obs: str):
        o, a = obs.strip().lower(), act.strip().lower()
        m = re.match(rf"you arrive at ({ENT})\.", o)
        if m:
            self.loc = m.group(1)
            if re.search(rf"the {re.escape(self.loc)} is closed", o):
                self.closed[self.loc] = True
            if "is open" in o:
                self.closed[self.loc] = False
            for it in seen_items(o):
                self.where[it] = self.loc
        m = re.match(rf"you open the ({ENT})", o)
        if m:
            self.closed[m.group(1)] = False
            for it in seen_items(o):
                self.where[it] = m.group(1)
        m = re.match(rf"you close the ({ENT})", o)
        if m:
            self.closed[m.group(1)] = True
        m = re.match(rf"on the ({ENT}), you see", o)
        if m:
            for it in seen_items(o):
                self.where[it] = m.group(1)
        m = re.match(rf"you pick up the ({ENT}) from the ({ENT})", o)
        if m:
            self.held, self.held_since = m.group(1), step
            self.where.pop(m.group(1), None)
        m = re.match(rf"you (?:move|put) the ({ENT}) (?:to|in|on|in/on) the ({ENT})", o)
        if m:
            self.held, self.held_since = None, step
            self.where[m.group(1)] = m.group(2)
        m = re.match(rf"you (heat|cool|clean) the ({ENT}) using", o)
        if m:
            self.done[m.group(2)].add(m.group(1))


def why_fails(cmd: str, st: State, obs_after: str) -> str:
    """The precondition the command violates in state st (before running it)."""
    c = " ".join(cmd.lower().split())
    if not obs_after.strip().lower().startswith("nothing happens"):
        return "succeeds"
    m = re.match(rf"go to ({ENT})$", c)
    if m:
        return "already there" if st.loc == m.group(1) else "go to failed (place unknown)"
    m = re.match(rf"take ({ENT}) from ({ENT})$", c)
    if m:
        if st.held:
            return "hands full"
        if st.loc != m.group(2):
            return "not at the place"
        if st.closed.get(m.group(2)):
            return "receptacle closed"
        return "object not there"
    m = re.match(rf"(?:move|put) ({ENT}) (?:to|in|on|in/on) ({ENT})$", c)
    if m:
        if st.held != m.group(1):
            return "not holding that object"
        if st.loc != m.group(2):
            return "not at the place"
        if st.closed.get(m.group(2)):
            return "receptacle closed"
        return "placement failed (other)"
    m = re.match(rf"(heat|cool|clean) ({ENT}) with ({ENT})$", c)
    if m:
        if st.held != m.group(2):
            return "not holding that object"
        if st.loc != m.group(3):
            return "not at the place"
        return "transform failed (other)"
    m = re.match(rf"(open|close) ({ENT})$", c)
    if m:
        if st.loc != m.group(2):
            return "not at the place"
        return "already open/closed"
    return "malformed or unknown command"


def trace_origin(cause: str, cmd: str, hist: list[dict], t: int, st: State, obj: str) -> tuple[int | None, str]:
    """The step (1-based) before t that created the failing condition, and what it was."""
    c = " ".join(cmd.lower().split())
    if cause == "not holding that object":
        if st.held_since is not None and st.held_since < t:
            a = hist[st.held_since]["action"].lower()
            if st.held is None:
                return st.held_since, f"put the object down: {a}"
            return st.held_since, f"took another object: {a}"
        return None, "never held it"
    if cause == "hands full":
        if st.held_since is not None and st.held_since < t:
            kind = "wrong object" if obj and st.held and st.held.split()[0] != obj else "took an object"
            return st.held_since, f"{kind}: {hist[st.held_since]['action'].lower()}"
        return None, "holding since unknown"
    if cause == "object not there":
        it = re.match(rf"take ({ENT})", c).group(1)
        for k in range(t - 1, 0, -1):
            o = hist[k]["observation"].lower()
            if re.match(rf"you pick up the {re.escape(it)}", o) or re.match(rf"you (?:move|put) the {re.escape(it)}", o):
                return k, f"object moved: {hist[k]['action'].lower()}"
        ever = any(re.search(rf"\b{re.escape(it)}\b", hist[k]["observation"].lower()) for k in range(0, t))
        return None, "object was seen elsewhere" if ever else "object never seen (hallucinated)"
    if cause == "receptacle closed":
        r = re.findall(ENT, c)[-1]
        for k in range(t - 1, 0, -1):
            if re.match(rf"you close the {re.escape(r)}", hist[k]["observation"].lower()):
                return k, f"closed it: {hist[k]['action'].lower()}"
        return None, "never opened"
    return None, "none"


def stuck_start(hist: list[dict], w: int) -> int | None:
    seen, flags = set(), []
    for h in hist:
        o = " ".join(h["observation"].split())
        flags.append(o.lower().startswith("nothing happens") or o in seen)
        seen.add(o)
    n = len(hist) - 1
    return next((i for i in range(1, n - w + 2) if all(flags[i:i + w])), None)


def _thought(r: dict, step: int) -> str | None:
    """The agent's own text written before the command of `step` (react_std / stateact logs keep it)."""
    for e in r.get("place_lists", []):
        if e.get("step") == step - 1 and isinstance(e.get("output"), str):
            return " ".join(e["output"].split())[:400]
    return (r.get("thoughts") or {}).get(str(step))


def analyze_stuck(r: dict, w: int) -> dict:
    """Primary: the first no-new-information window; the failing commands in it, why each fails, and the earliest
    step that created one of those failing conditions."""
    hist = r["history"]
    verb, obj, recep = parse_task(r["task"])
    n = len(hist) - 1
    t = stuck_start(hist, w)
    st = State()
    first_wrong_take = first_bad_put = None
    states = {}
    for i in range(1, n + 1):
        states[i] = (st.loc, st.held, st.held_since, dict(st.closed))
        o = hist[i]["observation"].lower()
        m = re.match(rf"you pick up the ({ENT}) from", o)
        if m and obj and m.group(1).split()[0] != obj and first_wrong_take is None:
            first_wrong_take = i
        m = re.match(rf"you (?:move|put) the ({ENT}) (?:to|in|on|in/on) the ({ENT})", o)
        if m and obj and m.group(1).split()[0] == obj and m.group(2).split()[0] != recep and verb not in st.done[m.group(1)] \
                and first_bad_put is None:
            first_bad_put = i
        st.update(i, hist[i]["action"], hist[i]["observation"])
    seen_target = next((i for i in range(0, n + 1) if obj and re.search(rf"\b{obj} \d+", hist[i]["observation"].lower())), None)
    out = {"id": r["id"], "task": r["task"], "won": r["won"], "steps": n, "stuck_start": t,
           "first_wrong_take": first_wrong_take, "first_target_put_down_early": first_bad_put, "target_first_seen": seen_target}
    if t is None:
        return out
    end = next((j for j in range(t, n + 1) if not (hist[j]["observation"].lower().startswith("nothing happens")
                                                    or any(" ".join(hist[j]["observation"].split()) == " ".join(hist[q]["observation"].split())
                                                           for q in range(0, j)))), n + 1)
    failing = []
    for j in range(t, end):
        if not hist[j]["observation"].lower().startswith("nothing happens"):
            continue
        loc, held, held_since, closed = states[j]
        tmp = State()
        tmp.loc, tmp.held, tmp.held_since, tmp.closed = loc, held, held_since, closed
        cause = why_fails(hist[j]["action"], tmp, hist[j]["observation"])
        origin, what = trace_origin(cause, hist[j]["action"], hist, j, tmp, obj)
        failing.append({"step": j, "command": hist[j]["action"], "why": cause, "origin": origin, "origin_what": what})
    earlier = [f for f in failing if f["origin"] is not None and f["origin"] < t]
    first = min(earlier, key=lambda f: f["origin"]) if earlier else None
    first_fail = next((i for i in range(1, t) if hist[i]["observation"].lower().startswith("nothing happens")), None)
    # origin, in order of evidence: a committed wrong object; the task object put down before it was done; the step that
    # created a failing condition inside the window; else the first failed command before the window (the agent's
    # explanation of that failure, in its next thought, is what the human audit checks)
    if first_wrong_take is not None and first_wrong_take < t:
        origin, what, kind = first_wrong_take, f"wrong object taken: {hist[first_wrong_take]['action'].lower()}", "wrong object taken"
    elif first_bad_put is not None and first_bad_put < t:
        origin, what, kind = first_bad_put, f"task object put down early: {hist[first_bad_put]['action'].lower()}", "task object put down early"
    elif first:
        origin, what, kind = first["origin"], first["origin_what"], re.sub(r":.*", "", first["origin_what"])
    elif first_fail is not None:
        origin, what, kind = first_fail, f"first failed command: {hist[first_fail]['action'].lower()}", "earlier failed command"
    elif not failing:
        origin, what = None, None
        kind = "no failing command (no new information)" + ("; target not seen yet" if seen_target is None or seen_target >= t else "")
    else:
        origin, what, kind = None, None, "failures with no earlier origin"
    first = {"origin": origin, "origin_what": what} if origin is not None else None
    out.update(stuck_length=end - t, commands_in_window=collections.Counter(" ".join(hist[j]["action"].lower().split()) for j in range(t, end)).most_common(4),
               failing=failing, origin=first["origin"] if first else None, origin_what=first["origin_what"] if first else None,
               origin_kind=kind, why_counts=dict(collections.Counter(f["why"] for f in failing)),
               thought_after_origin=_thought(r, first["origin"] + 1) if first else None)
    return out


def analyze(r: dict, k: int) -> dict:
    hist = r["history"]
    verb, obj, recep = parse_task(r["task"])
    acts = [" ".join(h["action"].lower().split()) for h in hist]
    n = len(hist) - 1
    t_loop = next((i for i in range(1, n - k + 2) if all(acts[i + j] == acts[i] for j in range(k))), None)
    st = State()
    first_wrong_take = first_bad_put = None
    for i in range(1, n + 1):
        if t_loop is not None and i == t_loop:
            break
        o = hist[i]["observation"].lower()
        m = re.match(rf"you pick up the ({ENT}) from", o)
        if m and obj and m.group(1).split()[0] != obj and first_wrong_take is None:
            first_wrong_take = i
        m = re.match(rf"you (?:move|put) the ({ENT}) (?:to|in|on|in/on) the ({ENT})", o)
        if m and obj and m.group(1).split()[0] == obj and m.group(2).split()[0] != recep and verb not in st.done[m.group(1)] \
                and first_bad_put is None:
            first_bad_put = i
        st.update(i, hist[i]["action"], hist[i]["observation"])
    out = {"id": r["id"], "task": r["task"], "won": r["won"], "steps": n, "loop_start": t_loop,
           "first_wrong_take": first_wrong_take, "first_target_put_down_early": first_bad_put}
    if t_loop is None:
        return out
    cmd = hist[t_loop]["action"]
    cause = why_fails(cmd, st, hist[t_loop]["observation"])
    origin, what = trace_origin(cause, cmd, hist, t_loop, st, obj)
    out.update(loop_command=cmd, loop_length=next((j for j in range(t_loop, n + 1) if acts[j] != acts[t_loop]), n + 1) - t_loop,
               why_it_fails=cause, origin=origin, origin_what=what, state_at_loop={"at": st.loc, "holding": st.held})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("dirs", nargs="+")
    ap.add_argument("--arm", default="react_std")
    ap.add_argument("--out", default=str(ROOT / "runs/online/analysis"))
    a = ap.parse_args()
    games = [json.loads(f.read_text()) for d in a.dirs for f in sorted(Path(d).glob(f"*/{a.arm}.json"))]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    lines = [f"# Loops and their origins: {a.arm}, {len(games)} games", "",
             "Stuck = first window of w steps with no new information (every feedback is \"Nothing happens\" or seen before). "
             "Origin = the earliest step that created a condition making a failing command in the window fail (traced from "
             "the feedback text). Repeat = k identical commands in a row (secondary).", ""]
    stuck_rows = {}
    for w in (3, 5, 8):
        rows = [analyze_stuck(r, w) for r in games]
        stuck_rows[w] = rows
        lost = [x for x in rows if not x["won"]]
        ls = [x for x in lost if x["stuck_start"] is not None]
        lines += [f"## Stuck, w = {w}", "",
                  f"- lost games: {len(lost)}; stuck: {len(ls)}; won games that got stuck at some point: "
                  f"{sum(1 for x in rows if x['won'] and x['stuck_start'] is not None)}",
                  f"- lost and stuck, with an origin step before the window: {sum(1 for x in ls if x['origin'] is not None)} / {len(ls)}", ""]
        if w == 5:
            lines += ["| what explains the stuck window | lost games |", "|---|---|"]
            for kd, v in collections.Counter(x["origin_kind"] for x in ls).most_common():
                lines.append(f"| {kd} | {v} |")
            gaps = sorted(x["stuck_start"] - x["origin"] for x in ls if x["origin"] is not None)
            if gaps:
                lines += ["", f"Steps from origin to the start of the stuck window: median {gaps[len(gaps)//2]}, range {gaps[0]}-{gaps[-1]}."]
            whys = collections.Counter()
            for x in ls:
                whys.update(x["why_counts"])
            lines += ["", "Why the failing commands inside the windows fail (all windows): " +
                      ", ".join(f"{k} {v}" for k, v in whys.most_common()), ""]
            lines += ["| game | task | stuck from | length | origin step | origin | the agent's next thought (for the audit) | commands in the window |",
                      "|---|---|---|---|---|---|---|---|"]
            for x in ls:
                th = (x.get("thought_after_origin") or "-").replace("|", "/")[:220]
                cmds = "; ".join(f"{c[:40]} x{v}" for c, v in x["commands_in_window"]).replace("|", "/")
                lines.append(f"| {x['id']} | {x['task']} | {x['stuck_start']} | {x['stuck_length']} | {x['origin'] or '-'} | "
                             f"{x['origin_what'] or x['origin_kind']} | {th} | {cmds} |")
            lines.append("")
    rows3 = []
    for k in (2, 3, 4):
        rows = [analyze(r, k) for r in games]
        if k == 3:
            rows3 = rows
        lost = [x for x in rows if not x["won"]]
        lost_loop = [x for x in lost if x["loop_start"] is not None]
        with_origin = [x for x in lost_loop if x.get("origin") is not None]
        won_loop = [x for x in rows if x["won"] and x["loop_start"] is not None]
        lines += [f"## Repeat, k = {k}", "",
                  f"- lost games: {len(lost)}; with a loop: {len(lost_loop)}; won games with a loop: {len(won_loop)}",
                  f"- lost games whose loop has an earlier origin step: {len(with_origin)} / {len(lost_loop)}", ""]
        if k == 3:
            lines += ["| why the looped command fails | lost games | of them with an earlier origin |", "|---|---|---|"]
            for why, v in collections.Counter(x["why_it_fails"] for x in lost_loop).most_common():
                lines.append(f"| {why} | {v} | {sum(1 for x in with_origin if x['why_it_fails'] == why)} |")
            lines += ["", "| origin found | lost games |", "|---|---|"]
            for what, v in collections.Counter(re.sub(r":.*", "", x["origin_what"]) for x in lost_loop).most_common():
                lines.append(f"| {what} | {v} |")
            gaps = sorted(x["loop_start"] - x["origin"] for x in with_origin)
            if gaps:
                lines += ["", f"Steps from origin to loop start: median {gaps[len(gaps)//2]}, range {gaps[0]}-{gaps[-1]}."]
            lines.append("")
    lines += ["## Per game (k = 3)", "", "| game | task | won | loop starts | looped command | why it fails | origin step | origin | first wrong take | target put down early |",
              "|---|---|---|---|---|---|---|---|---|---|"]
    for x in rows3:
        lines.append(f"| {x['id']} | {x['task']} | {'yes' if x['won'] else 'no'} | {x['loop_start'] or '-'} | {x.get('loop_command', '-')} | "
                     f"{x.get('why_it_fails', '-')} | {x.get('origin') or '-'} | {x.get('origin_what', '-')} | "
                     f"{x['first_wrong_take'] or '-'} | {x['first_target_put_down_early'] or '-'} |")
    (out / f"loops_{a.arm}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with open(out / f"loops_{a.arm}.jsonl", "w", encoding="utf-8") as fh:
        for x, y in zip(stuck_rows[5], rows3):
            fh.write(json.dumps({"stuck_w5": x, "repeat_k3": y}, ensure_ascii=False) + "\n")
    print("\n".join(lines[:75]))


if __name__ == "__main__":
    main()
