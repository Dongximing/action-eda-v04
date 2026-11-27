#!/usr/bin/env python3
"""What happens after an error, and can the history at that moment tell the outcomes apart? Offline, no model calls.

  python3 scripts/recovery_analysis.py [--run runs/online/unseen] [--arm react_std_t1536]

Error episode
  Progress is the furthest subgoal reached, read from the feedback text: 1 the task object seen, 2 a task object
  held, 3 its required step done (heat/cool/clean; light tasks: none), 4 + k  k task objects placed in the goal.
  An episode starts at the first error after the last progress gain. An error is a failed command ("Nothing
  happens") or a history-only rule alarm on a command that ran (scripts/c2_detectors.py Ep: wrong object, task
  object put down too early, carried while fetching the second, wrong appliance). Its cause is the rule reading
  of the state before the command (analyze_loops.why_fails / c2_detectors.e2_rules).
Outcome (uses the rest of the episode, for labelling only)
  quick    progress gained again within 5 steps
  slow     gained later than 5 steps
  never    no further gain before the game ended (budget spent or won without a gain is impossible)
  relapse  (flag) after the gain, a later episode has the same cause
Signals at the episode start, from history only (the agent's next output included: it is written before the next
command runs)
  acted    the agent's next command addresses the rule cause (e.g. "not at the place" -> go to that place)
  stated   the agent's next thought names the rule cause (keyword reading, checked on a sample by hand)
  belief   the next thought asserts a state the history contradicts (holding X while not, at R while not, the
           task done while the game goes on)
  prior    errors before this one; same_before: an earlier episode had the same cause; left: steps left
Writes runs/online/analysis/recovery_<arm>.{md,jsonl}.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_loops import ENT, State, parse_task, why_fails  # noqa: E402
from c2_detectors import e2_rules, failed, norm  # noqa: E402

QUICK = 5
STATED = {  # keywords in the next thought that name each cause
    "not at the place": r"\b(not at|am not at|go to|need to go|go there|navigate|first go|move to the location|at the (?:\w+ )?\d+ yet)\b",
    "not holding that object": r"\b(not holding|don't have|do not have|need to (?:pick|take)|pick (?:it )?up first|haven't (?:picked|taken)|not in my (?:hand|inventory))\b",
    "hands full": r"\b(already holding|hands are full|holding (?:the |a )?\w+ \d+ already|put (?:it|the \w+ \d+) down first|can only (?:hold|carry) one)\b",
    "wrong appliance": r"\bmicrowave\b|\bfridge\b|\bsinkbasin\b",
    "malformed or unknown command": r"\b(format|exact name|specific (?:name|object)|placeholder|valid action|syntax)\b",
    "already there": r"\b(already at|already here|i am at)\b",
    "already open/closed": r"\b(already open|already closed)\b",
    "receptacle closed": r"\b(closed|open it first|need to open)\b",
    "object not there": r"\b(not there|no longer|not on|isn't there|not here|elsewhere)\b",
}


def progress(st: State, task: str, placed: int) -> int:
    verb, obj, goal = parse_task(task)
    p = 0
    if obj and any(k.split()[0] == obj for k in st.where) or (st.held and obj and st.held.split()[0] == obj):
        p = 1
    if st.held and obj and st.held.split()[0] == obj:
        p = 2
        if verb and verb in st.done[st.held]:
            p = 3
    return max(p, 3 + placed) if placed else p


def cause_of(task: str, hist: list[dict], t: int, st: State) -> str | None:
    """The rule cause of an error at step t (None: no error)."""
    if failed(hist[t]):
        c = why_fails(hist[t]["action"] or "", st, hist[t]["observation"] or "")
        rules = e2_rules(task, hist[:t + 1])
        if "tool" in rules:
            return "wrong appliance"
        return c
    rules = e2_rules(task, hist[:t + 1])
    obj = parse_task(task)[1]
    m = re.match(rf"you pick up the ({ENT}) from", (hist[t]["observation"] or "").lower())
    if m and obj and m.group(1).split()[0] != obj:
        return "wrong object"
    for k, name in (("early", "put down too early"), ("carry", "carried while fetching the second")):
        if k in rules:
            return name
    return None


def acted(cause: str, cmd: str, nxt: str, st: State) -> bool:
    c, n = norm(cmd), norm(nxt)
    ents = re.findall(ENT, c)
    if cause == "not at the place":
        return bool(ents) and n == f"go to {ents[-1]}"
    if cause == "not holding that object":
        return n.startswith("take ") or (bool(ents) and n.startswith("go to ") and False)
    if cause == "hands full":
        return bool(st.held) and (n.startswith(f"move {st.held} ") or n.startswith(f"put {st.held} "))
    if cause == "wrong appliance":
        return bool(re.search(r"(microwave|fridge|sinkbasin)", n))
    if cause == "malformed or unknown command":
        return bool(re.fullmatch(rf"(go to|open|close|use|examine) {ENT}|take {ENT} from {ENT}|move {ENT} to {ENT}|"
                                 rf"(heat|cool|clean) {ENT} with {ENT}|look|inventory", n))
    if cause in ("already there", "already open/closed"):
        return n != c
    if cause == "receptacle closed":
        return bool(ents) and n == f"open {ents[-1]}"
    if cause == "object not there":
        return n.startswith("go to ") or n == "look"
    if cause == "wrong object":
        return bool(ents) and (n.startswith(f"move {ents[0]} ") or n.startswith(f"put {ents[0]} "))
    if cause == "put down too early":
        return bool(ents) and n.startswith(f"take {ents[0]} ")
    if cause == "carried while fetching the second":
        return False
    return False


def belief_errors(thought: str, st: State, won_later: bool) -> list[str]:
    """Claims in the agent's thought that the history contradicts (state after the error step)."""
    t = (thought or "").lower()
    out = []
    for m in re.finditer(rf"\bi (?:have|am holding|am carrying|hold|now have|still have) (?:the )?({ENT})", t):
        if st.held != m.group(1):
            out.append(f"claims to hold {m.group(1)}")
            break
    for m in re.finditer(rf"\bi am (?:currently |now |already )?at (?:the )?({ENT})", t):
        if st.loc != m.group(1):
            out.append(f"claims to be at {m.group(1)}")
            break
    if re.search(r"\btask (?:is|has been) (?:now )?(?:successfully )?(?:complete|completed|done|accomplished)\b", t):
        out.append("claims the task is done")
    return out


def episodes(r: dict) -> list[dict]:
    hist, task = r["history"], r["task"]
    thoughts = {e["step"]: e.get("output") or "" for e in r.get("place_lists", [])}
    n = len(hist) - 1
    st, placed, best, last_gain = State(), 0, 0, 0
    goal = parse_task(task)[2]
    obj = parse_task(task)[1]
    prog_after = []
    errs = []                   # (step, cause, state before)
    for t in range(1, n + 1):
        before = State()
        before.__dict__.update({k: (v.copy() if hasattr(v, "copy") else v) for k, v in st.__dict__.items()})
        before.done = collections.defaultdict(set, {k: set(v) for k, v in st.done.items()})
        c = cause_of(task, hist, t, before)
        if c:
            errs.append((t, c, before))
        st.update(t, hist[t]["action"] or "", hist[t]["observation"] or "")
        m = re.match(rf"you (?:move|put) the ({ENT}) (?:to|in|on|in/on) the ({ENT})", (hist[t]["observation"] or "").lower())
        if m and obj and goal and m.group(1).split()[0] == obj and m.group(2).split()[0] == goal:
            placed += 1
        prog_after.append(progress(st, task, placed))
    gains = [t for t in range(1, n + 1) if prog_after[t - 1] > max([0] + prog_after[:t - 1])]
    eps, used = [], set()
    for t, c, before in errs:
        prev_gain = max([g for g in gains if g <= t] + [0])
        if prev_gain in used:
            continue
        used.add(prev_gain)
        nxt_gain = next((g for g in gains if g > t), None)
        k = nxt_gain - t if nxt_gain else None
        outcome = "never" if k is None else ("quick" if k <= QUICK else "slow")
        th = thoughts.get(t, "")
        after = State()
        sim = State()
        for i in range(1, t + 1):
            sim.update(i, hist[i]["action"] or "", hist[i]["observation"] or "")
        after = sim
        nxt_cmd = hist[t + 1]["action"] if t + 1 <= n else ""
        eps.append({"id": r["id"], "won": r["won"], "t": t, "cause": c, "command": hist[t]["action"], "outcome": outcome,
                    "steps_to_gain": k, "next_command": nxt_cmd, "acted": acted(c, hist[t]["action"] or "", nxt_cmd or "", before),
                    "stated": bool(re.search(STATED.get(c, r"$^"), th.lower())) if c in STATED else None,
                    "belief": belief_errors(th, after, r["won"]), "prior_errors": sum(1 for x in errs if x[0] < t),
                    "left": 50 - t, "thought": " ".join(th.split())[:500]})
    seen_causes = collections.Counter()
    for e in eps:
        e["same_before"] = seen_causes[e["cause"]] > 0
        seen_causes[e["cause"]] += 1
    for i, e in enumerate(eps):
        e["relapse"] = e["outcome"] != "never" and any(f["cause"] == e["cause"] for f in eps[i + 1:])
    return eps


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=str(ROOT / "runs/online/unseen"))
    ap.add_argument("--arm", default="react_std_t1536")
    a = ap.parse_args()
    games = [json.loads(f.read_text()) for f in sorted(Path(a.run).glob(f"*/{a.arm}.json"))]
    eps = [e for r in games for e in episodes(r)]
    out = ROOT / f"runs/online/analysis/recovery_{a.arm}"
    with open(f"{out}.jsonl", "w") as fh:
        for e in eps:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    oc = collections.Counter(e["outcome"] for e in eps)
    md = [f"# Error recovery: {a.arm}, {len(games)} games, {len(eps)} error episodes", "",
          f"Outcomes: quick (progress again within {QUICK} steps) {oc['quick']}, slow {oc['slow']}, never {oc['never']}; "
          f"relapse after a gain: {sum(e['relapse'] for e in eps)}.", "",
          "## By cause", "", "| cause | episodes | quick | slow | never | relapse | acted on the cause | thought names it | false belief |",
          "|---|---|---|---|---|---|---|---|---|"]
    by = collections.defaultdict(list)
    for e in eps:
        by[e["cause"]].append(e)
    for c, es in sorted(by.items(), key=lambda x: -len(x[1])):
        o = collections.Counter(x["outcome"] for x in es)
        st = [x["stated"] for x in es if x["stated"] is not None]
        md.append(f"| {c} | {len(es)} | {o['quick']} | {o['slow']} | {o['never']} | {sum(x['relapse'] for x in es)} | "
                  f"{sum(x['acted'] for x in es)} | {sum(st) if st else '-'} | {sum(bool(x['belief']) for x in es)} |")

    def rate(sel, key="never"):
        return f"{sum(1 for e in sel if e['outcome'] == key)}/{len(sel)} ({100 * sum(1 for e in sel if e['outcome'] == key) / max(1, len(sel)):.0f}%)"
    md += ["", "## Signals at the episode start vs outcome", "",
           "| signal (history only) | episodes | never recovered | quick |", "|---|---|---|---|"]
    sigs = [("all", lambda e: True),
            ("next command acts on the cause", lambda e: e["acted"]), ("next command does not", lambda e: not e["acted"]),
            ("thought names the cause", lambda e: e["stated"] is True), ("thought does not", lambda e: e["stated"] is False),
            ("thought has a false belief", lambda e: bool(e["belief"])), ("no false belief", lambda e: not e["belief"]),
            ("same cause seen before", lambda e: e["same_before"]), ("first time for this cause", lambda e: not e["same_before"]),
            ("3+ earlier errors", lambda e: e["prior_errors"] >= 3), ("0-2 earlier errors", lambda e: e["prior_errors"] < 3),
            ("acted, no false belief", lambda e: e["acted"] and not e["belief"]),
            ("not acted and false belief", lambda e: (not e["acted"]) and bool(e["belief"]))]
    for name, f in sigs:
        sel = [e for e in eps if f(e)]
        md.append(f"| {name} | {len(sel)} | {rate(sel)} | {rate(sel, 'quick')} |")
    bel = collections.Counter(b.split(" ", 2)[0] + " " + b.split(" ", 2)[1] + (" " + b.split(" ", 2)[2].split()[0] if len(b.split()) > 2 else "")
                              for e in eps for b in e["belief"])
    md += ["", "False-belief kinds: " + ", ".join(f"{k} {v}" for k, v in bel.most_common()), ""]
    md += ["## Games", "", f"- won games with at least one episode: {len({e['id'] for e in eps if e['won']})}; "
           f"lost games: {len({e['id'] for e in eps if not e['won']})}"]
    Path(f"{out}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
