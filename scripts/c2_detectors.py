#!/usr/bin/env python3
"""C2 of docs/early_error_study_design.md: can the originating error be caught early from the current history only?
Offline, no model calls.

  python3 scripts/c2_detectors.py [--run runs/online/unseen] [--arm react_std_t1536]

Every detector is a function of (task text, history[0..t]) that says whether to raise an alarm at step t. The
evaluator gives it the prefix only (a copy, so later records cannot be read), never the environment's internal state
or its list of admissible commands. Step t holds the command run at t and its feedback.

Reactive baselines
  R1  the same command 3 times in a row (a loop alarm)
  R2  two failures in a row on the same target (VBL's Diagnose trigger, K = 2)
  R3  any failure ("Nothing happens")
History-only error checks (game rules of the action guide + state read from the feedback text)
  E1  name check: picked up an object whose name is not the task's object
  E2  precondition check on the command just run, from the state before it:
        nav    acts on a receptacle it is not at (take/put/open/close/heat/cool/clean)
        full   take while already holding something
        early  the task object is put down before its required step is done (light task: put down at all;
               heat/cool/clean: put down anywhere, the goal and the appliance included, before the transform;
               put/two: put down somewhere that is not the goal)
        carry  two-object task: holding a task object and going to a place that is not the goal
        tool   heat without a microwave, cool without a fridge, clean without a sink
        form   a command outside the action grammar (placeholders such as "obj"/"recep", extra text)
  E   E1 or E2
  Ep  the precise part of E: E1 or E2 without nav and form (the two rules that also fire often in won games)
E3 (a judge model reading the history) is not run here.

Scored against the C1 audit labels (runs/online/analysis/c1_audit_<arm>.jsonl): e = the first never-repaired error,
t_L = start of the stuck window. Writes runs/online/analysis/c2_detectors_<arm>.{md,jsonl}.
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import re
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_loops import ENT, State, parse_task  # noqa: E402

GRAMMAR = [rf"go to {ENT}", rf"take {ENT} from {ENT}", rf"(?:move|put) {ENT} (?:to|in|on|in/on) {ENT}", rf"open {ENT}",
           rf"close {ENT}", rf"use {ENT}", rf"(?:clean|heat|cool) {ENT} with {ENT}", "look", "inventory", rf"examine {ENT}"]
TOOL = {"heat": ("microwave",), "cool": ("fridge",), "clean": ("sinkbasin", "bathtubbasin")}


def failed(h: dict) -> bool:
    return (h.get("observation") or "").strip().lower().startswith("nothing happens")


def norm(a: str) -> str:
    return " ".join((a or "").lower().split())


def state_before(hist: list[dict], t: int) -> State:
    st = State()
    for i in range(1, t):
        st.update(i, hist[i]["action"] or "", hist[i]["observation"] or "")
    return st


def e2_rules(task: str, hist: list[dict]) -> list[str]:
    """The E2 rules violated by the command at the last step of `hist` (the prefix the detector is given)."""
    t = len(hist) - 1
    a, verb_obj = norm(hist[t]["action"]), parse_task(task)
    verb, obj, goal = verb_obj
    st = state_before(hist, t)
    two = bool(re.search(r"\btwo\b", task.lower()))
    light = bool(re.search(r"lamp", task.lower()))
    out = []
    if not any(re.fullmatch(g, a) for g in GRAMMAR):
        return ["form"]
    m = re.fullmatch(rf"take ({ENT}) from ({ENT})", a)
    if m:
        if st.held:
            out.append("full")
        if st.loc != m.group(2):
            out.append("nav")
    m = re.fullmatch(rf"(?:move|put) ({ENT}) (?:to|in|on|in/on) ({ENT})", a)
    if m:
        if st.loc != m.group(2):
            out.append("nav")
        it, rec = m.group(1), m.group(2)
        if obj and it.split()[0] == obj and st.held == it:
            if light or (verb and verb not in st.done[it]) or (not verb and goal and rec.split()[0] != goal):
                out.append("early")
    m = re.fullmatch(rf"(open|close) ({ENT})", a)
    if m and st.loc != m.group(2):
        out.append("nav")
    m = re.fullmatch(rf"(heat|cool|clean) ({ENT}) with ({ENT})", a)
    if m:
        if st.loc != m.group(3):
            out.append("nav")
        if m.group(3).split()[0] not in TOOL[m.group(1)]:
            out.append("tool")
    m = re.fullmatch(rf"go to ({ENT})", a)
    if m and two and st.held and obj and st.held.split()[0] == obj and goal and m.group(1).split()[0] != goal:
        out.append("carry")
    return out


def detect(name: str, task: str, hist: list[dict]) -> bool:
    """Alarm at the last step of `hist`, from `hist` only."""
    t = len(hist) - 1
    if t < 1:
        return False
    h = hist[t]
    if name == "R1":
        return t >= 3 and norm(hist[t]["action"]) == norm(hist[t - 1]["action"]) == norm(hist[t - 2]["action"])
    if name == "R2":
        if t < 2 or not (failed(h) and failed(hist[t - 1])):
            return False
        tg = lambda a: (re.findall(ENT, norm(a)) or [norm(a)])[-1]  # noqa: E731
        return tg(h["action"]) == tg(hist[t - 1]["action"])
    if name == "R3":
        return failed(h)
    if name == "E1":
        obj = parse_task(task)[1]
        m = re.match(rf"you pick up the ({ENT}) from", (h["observation"] or "").lower())
        return bool(m and obj and m.group(1).split()[0] != obj)
    if name.startswith("E2"):
        rules = e2_rules(task, hist)
        return bool(rules) if name == "E2" else name[3:] in rules
    if name == "E":
        return detect("E1", task, hist) or detect("E2", task, hist)
    if name == "Ep":
        return detect("E1", task, hist) or any(x not in ("nav", "form") for x in e2_rules(task, hist))
    raise ValueError(name)


DETECTORS = ["R1", "R2", "R3", "E1", "E2", "E", "Ep", "E2:nav", "E2:full", "E2:early", "E2:carry", "E2:tool", "E2:form"]


def alarms(name: str, r: dict) -> list[int]:
    hist = r["history"]
    out = []
    for t in range(1, len(hist)):
        prefix = copy.deepcopy(hist[:t + 1])   # the detector never sees records after t
        if detect(name, r["task"], prefix):
            out.append(t)
    return out


def boot(vals: list[float], n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    if not vals:
        return (float("nan"), float("nan"))
    ms = sorted(sum(rng.choice(vals) for _ in vals) / len(vals) for _ in range(n))
    return ms[int(0.025 * n)], ms[int(0.975 * n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=str(ROOT / "runs/online/unseen"))
    ap.add_argument("--arm", default="react_std_t1536")
    ap.add_argument("--heldout", action="store_true",
                    help="no C1 labels for this run: score alarms before the stuck window (w = 5) of lost games and "
                         "alarms in won games")
    a = ap.parse_args()
    if a.heldout:
        return heldout(a)
    games = {f.parent.name: json.loads(f.read_text()) for f in sorted(Path(a.run).glob(f"*/{a.arm}.json"))}
    labels = {x["id"]: x for x in map(json.loads, open(ROOT / f"runs/online/analysis/c1_audit_{a.arm}.jsonl"))}
    lost = [g for g in labels if labels[g]["t_L"]]           # lost games with a stuck window
    early_games = [g for g in lost if labels[g]["kind"] in "AB"]
    won = [g for g, r in games.items() if r["won"]]
    rows, table = [], []
    for name in DETECTORS:
        al = {g: alarms(name, games[g]) for g in games}
        per = []
        for g in lost:
            e, t = labels[g]["e"], labels[g]["t_L"]
            first = al[g][0] if al[g] else None
            hit = next((d for d in al[g] if e <= d <= t), None)
            per.append({"id": g, "kind": labels[g]["kind"], "e": e, "t_L": t, "alarms": al[g], "first": first,
                        "before_e": first is not None and first < e, "hit_by_loop": hit,
                        "hit_before_loop": next((d for d in al[g] if e <= d < t), None)})
        early = [p for p in per if p["kind"] in "AB"]
        r_before = [1.0 if p["hit_before_loop"] is not None else 0.0 for p in early]
        r_by = [1.0 if p["hit_by_loop"] is not None else 0.0 for p in per]
        first_ok = [1.0 if (p["first"] is not None and p["e"] <= p["first"] <= p["t_L"]) else 0.0 for p in per]
        won_any = [1.0 if al[g] else 0.0 for g in won]
        won_steps = sum(len(games[g]["history"]) - 1 for g in won)
        won_rate = sum(len(al[g]) for g in won) / won_steps
        leads = [p["t_L"] - p["hit_before_loop"] for p in early if p["hit_before_loop"] is not None]
        lags = [p["hit_by_loop"] - p["e"] for p in per if p["hit_by_loop"] is not None]
        table.append({"detector": name,
                      "caught_before_loop": (sum(r_before), len(early), boot(r_before)),
                      "caught_by_loop_start": (sum(r_by), len(per), boot(r_by)),
                      "first_alarm_in_window": (sum(first_ok), len(per)),
                      "first_alarm_before_e": sum(p["before_e"] for p in per),
                      "won_games_with_alarm": (sum(won_any), len(won), boot(won_any)),
                      "won_alarms_per_step": won_rate,
                      "lead_median": statistics.median(leads) if leads else None,
                      "lag_median": statistics.median(lags) if lags else None})
        rows.append({"detector": name, "lost": per, "won_alarms": {g: al[g] for g in won}})
    out = ROOT / f"runs/online/analysis/c2_detectors_{a.arm}"
    with open(f"{out}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    pct = lambda k, n: f"{k:.0f}/{n} ({100 * k / n:.0f}%)"  # noqa: E731
    ci = lambda c: f"[{100 * c[0]:.0f}, {100 * c[1]:.0f}]"  # noqa: E731
    md = [f"# C2: history-only detectors, {a.arm}, {len(games)} games", "",
          f"Scored on the {len(lost)} lost games with a stuck window (C1 audit labels: e = first never-repaired error, "
          f"t_L = start of the stuck window; {len(early_games)} of them have e before t_L) and on the {len(won)} won games "
          "(alarms there are false alarms or alarms on errors the agent repaired). 95% intervals: bootstrap over games.", "",
          "| detector | caught in [e, t_L) (early games) | caught in [e, t_L] (all lost) | first alarm lands in [e, t_L] | "
          "first alarm before e | won games with an alarm | alarms per step, won games | lead t_L-d (median) | lag d-e (median) |",
          "|---|---|---|---|---|---|---|---|---|"]
    for x in table:
        k, n, c = x["caught_before_loop"]
        k2, n2, c2 = x["caught_by_loop_start"]
        k3, n3 = x["first_alarm_in_window"]
        k4, n4, c4 = x["won_games_with_alarm"]
        md.append(f"| {x['detector']} | {pct(k, n)} {ci(c)} | {pct(k2, n2)} {ci(c2)} | {pct(k3, n3)} | {x['first_alarm_before_e']} | "
                  f"{pct(k4, n4)} {ci(c4)} | {x['won_alarms_per_step']:.3f} | {x['lead_median']} | {x['lag_median']} |")
    md += ["", "Notes: the E rules were written after reading these lost games (C1 audit), so their recall here is in-sample; "
           "see c2_heldout_* for games the rules were not written from. Alarms in won games are mostly real errors the agent "
           "later repaired (e.g. a butterknife taken for a knife, then put back), not misreadings; whether alarming on them "
           "helps is the C3 question.", "", "## Per game (E, R2, R1)", "", "| game | kind | e | t_L | E alarms | R2 alarms | R1 alarms |", "|---|---|---|---|---|---|---|"]
    by = {r["detector"]: {p["id"]: p for p in r["lost"]} for r in rows}
    for g in lost:
        f = lambda d: ",".join(map(str, by[d][g]["alarms"][:8])) or "-"  # noqa: E731
        md.append(f"| {g} | {labels[g]['kind']} | {labels[g]['e']} | {labels[g]['t_L']} | {f('E')} | {f('R2')} | {f('R1')} |")
    Path(f"{out}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:5 + len(table)]))


def heldout(a):
    from analyze_loops import stuck_start
    games = [json.loads(f.read_text()) for d in a.run.split(",") for f in sorted(Path(d).glob(f"*/{a.arm}.json"))]
    lost = [r for r in games if not r["won"] and stuck_start(r["history"], 5)]
    won = [r for r in games if r["won"]]
    md = [f"# C2 held-out check: {a.arm} in {a.run}, {len(games)} games (rules not written from these)", "",
          f"{len(lost)} lost games with a stuck window (w = 5), {len(won)} won games. No origin labels: 'before the "
          "loop' = an alarm in [1, t_L).", "",
          "| detector | lost games alarmed before the loop | lead t_L - first alarm (median) | won games with an alarm | alarms per step, won |",
          "|---|---|---|---|---|"]
    for name in DETECTORS:
        before, leads = [], []
        for r in lost:
            t = stuck_start(r["history"], 5)
            d = [x for x in alarms(name, r) if x < t]
            before.append(1.0 if d else 0.0)
            if d:
                leads.append(t - d[0])
        al = [alarms(name, r) for r in won]
        steps = sum(len(r["history"]) - 1 for r in won)
        md.append(f"| {name} | {sum(before):.0f}/{len(lost)} ({100 * sum(before) / len(lost):.0f}%) | "
                  f"{statistics.median(leads) if leads else '-'} | {sum(1 for x in al if x)}/{len(won)} "
                  f"({100 * sum(1 for x in al if x) / len(won):.0f}%) | {sum(map(len, al)) / steps:.3f} |")
    out = ROOT / f"runs/online/analysis/c2_heldout_{a.arm}_{Path(a.run.split(',')[0]).name}"
    Path(f"{out}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
