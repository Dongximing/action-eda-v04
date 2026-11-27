#!/usr/bin/env python3
"""C1 audit (docs/early_error_study_design.md §3): one annotator's reading of every lost game of the 1536-token
standard ReAct run on valid_unseen (runs/online/unseen/*/react_std_t1536.json), next to the rule labels of
scripts/analyze_loops.py (stuck window w = 5). Offline. Writes runs/online/analysis/c1_audit_react_std_t1536.{md,jsonl}.

e    = the first wrong step that was never repaired (the step where a different command would have kept the game
       winnable), read from the trajectory.
t_L  = start of the first stuck window (w = 5), from analyze_loops.
kind = A  an earlier error of a different kind; the loop is its consequence
       B  the loop is the same error repeated, first shown before the window
       C  the error starts at the loop (e = t_L)
       -  no stuck window
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# gid: (e, kind, what e is, first visible symptom step or None if e itself is visible)
LABELS = {
    "u007": (7, "A", "put down early", "put the bowl down next to the lamp instead of holding it while using the lamp", None),
    "u008": (8, "A", "put down early", "put the bowl on the shelf with the lamp instead of holding it", None),
    "u013": (16, "A", "put down early", "put the mug on the desk with the lamp instead of holding it", None),
    "u025": (19, "A", "skipped pickup", "saw peppershaker 1 on countertop 3 (step 18) and walked to the drawer without taking it", 20),
    "u030": (13, "C", "skipped navigation", "move saltshaker 1 to cabinet 1 while at drawer 1", None),
    "u033": (24, "B", "skipped navigation", "move saltshaker 1 to drawer 1 while at countertop 3 (repeated in the window)", None),
    "u042": (37, "A", "wrong object", "took box 2 while searching for the watch; hands full when the watch is found", 42),
    "u043": (18, "C", "skipped navigation", "move bowl 1 to cabinet 1 while at the sink", None),
    "u046": (4, "A", "wrong object", "took towel 1; the task is cloth", None),
    "u047": (3, "A", "wrong object", "took handtowel 1; the task is cloth", None),
    "u049": (2, "A", "wrong object", "took handtowel 1; the task is cloth", None),
    "u055": (20, "A", "wrong object", "took butterknife 1; the task is knife", None),
    "u056": (15, "A", "put down early", "put the mug in the coffeemachine (goal) before cleaning it", None),
    "u072": (22, "C", "skipped navigation", "move spatula 1 to drawer 1 while at the sink", None),
    "u074": (17, "C", "skipped navigation", "cool bread 1 with fridge 1 while at countertop 3", None),
    "u079": (8, "C", "skipped navigation", "cool lettuce 1 with fridge 1 while at countertop 2", None),
    "u081": (9, "C", "skipped navigation", "move mug 1 to cabinet 3 while at the fridge", None),
    "u083": (10, "A", "wrong object", "took cup 1; the task is mug", None),
    "u095": (1, "A", "failure misexplained", "open fridge 1 from the middle of the room; the next thought blames the action list, then the outputs break format", None),
    "u097": (1, "C", "skipped navigation", "open fridge 1 from the middle of the room, then the outputs break format", None),
    "u101": (15, "A", "wrong object", "took mug 1; the task is cup", None),
    "u102": (8, "A", "wrong object", "took mug 3; the task is cup", None),
    "u103": (11, "A", "wrong object", "took mug 1; the task is cup", None),
    "u107": (3, "-", "skipped pickup", "no stuck window: many different errors (skipped pickup, put in microwave before heating, coffeemachine)", 4),
    "u108": (14, "A", "put down early", "put the mug in the microwave, then heat fails (not held); stoveburner tried at step 11", None),
    "u109": (11, "A", "put down early", "put the mug in the microwave, then heat fails (not held); stoveburner tried at step 7", None),
    "u110": (4, "A", "put down early", "put the mug in the coffeemachine (goal) before heating it", None),
    "u111": (7, "A", "put down early", "put the mug in the coffeemachine (goal) before heating it; tried to heat with the coffeemachine at step 6", None),
    "u115": (12, "A", "put down early", "put the tomato in the microwave, then heat fails (not held); stoveburner tried at step 8", None),
    "u117": (12, "A", "put down early", "put the tomato in the microwave, then heat fails (not held); stoveburner tried at step 8", None),
    "u119": (12, "A", "kept carrying", "two-object task: kept cd 3 in hand while trying to take the second cd (hands full)", 23),
    "u122": (10, "A", "kept carrying", "two-object task: kept keychain 3 in hand while searching for the second", 35),
    "u124": (4, "A", "kept carrying", "two-object task: kept peppershaker 1 in hand, then take peppershaker 2 fails (hands full)", 5),
    "u129": (5, "A", "kept carrying", "two-object task: kept soapbar 1 in hand (did not put it in the open cabinet 1)", 17),
    "u132": (19, "B", "skipped navigation", "take soapbar 1 from countertop 1 while at the garbagecan (repeated in the window)", None),
}


def main():
    rule = {}
    for l in open(ROOT / "runs/online/analysis/loops_react_std_t1536.jsonl"):
        x = json.loads(l)["stuck_w5"]
        rule[x["id"]] = x
    lost = sorted(g for g, x in rule.items() if not x["won"])
    assert lost == sorted(LABELS), (set(lost) ^ set(LABELS))
    rows = []
    for g in lost:
        e, kind, what, note, symptom = LABELS[g]
        x = rule[g]
        t = x["stuck_start"]
        rows.append({"id": g, "task": x["task"], "t_L": t, "e": e, "kind": kind, "error": what, "note": note,
                     "first_symptom": symptom or e, "gap_e_to_loop": (t - e) if t else None,
                     "rule_origin": x.get("origin"), "rule_kind": x.get("origin_kind"),
                     "rule_says_earlier": x.get("origin") is not None and t is not None and x["origin"] < t})
    out = ROOT / "runs/online/analysis/c1_audit_react_std_t1536"
    with open(f"{out}.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    stuck = [r for r in rows if r["t_L"]]
    import collections, statistics
    k = collections.Counter(r["kind"] for r in stuck)
    a = [r for r in stuck if r["kind"] == "A"]
    gaps = sorted(r["gap_e_to_loop"] for r in stuck if r["kind"] in "AB")
    agree = sum((r["kind"] in "AB") == r["rule_says_earlier"] for r in stuck)
    md = ["# C1 audit: lost games of standard ReAct (1536 tokens), valid_unseen 134", "",
          "One annotator (Claude), reading each trajectory; the design's second annotator and Cohen's kappa are still to do.", "",
          f"- lost: {len(rows)}; with a stuck window (w = 5): {len(stuck)}",
          f"- A, an earlier error of a different kind causes the loop: {k['A']} / {len(stuck)}",
          f"- B, the same error, first shown before the window: {k['B']} / {len(stuck)}",
          f"- C, the error starts at the loop: {k['C']} / {len(stuck)}",
          f"- steps from e to the loop (A and B): median {statistics.median(gaps)}, range {gaps[0]}-{gaps[-1]}",
          f"- the rule (analyze_loops) agrees on earlier-origin yes/no in {agree} / {len(stuck)} games", "",
          "| kind of e | A | B | C |", "|---|---|---|---|"]
    for w in sorted({r["error"] for r in stuck}):
        md.append(f"| {w} | " + " | ".join(str(sum(r['error'] == w and r['kind'] == c for r in stuck)) for c in "ABC") + " |")
    md += ["", "| game | task | e | t_L | kind | error | note | first symptom | rule origin |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['task']} | {r['e']} | {r['t_L'] or '-'} | {r['kind']} | {r['error']} | {r['note']} | "
                  f"{r['first_symptom']} | {r['rule_origin'] or '-'} ({r['rule_kind'] or '-'}) |")
    Path(f"{out}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md[:20]))


if __name__ == "__main__":
    main()
