#!/usr/bin/env python3
"""After a failure, does the agent blame the recent action or the earlier premise that actually caused it? Offline.

  python3 scripts/blame_analysis.py [--arm react_std_t1536]

Games: the lost games whose C1 audit origin e comes before the loop (kind A/B, runs/online/analysis/c1_audit_<arm>.jsonl).
Failures: every "Nothing happens" after e. For each, the agent's next thought (written right after the failure) is
read for a mention that questions the premise set at e, with patterns per origin kind:
  wrong object        the held object may not be the task's object
  put down too early  it is no longer held / must be taken back out
  kept carrying       hands are full / put the first one down
  skipped pickup      it was never picked up
Anything else counts as blaming the recent action or the environment. The pattern reading is checked by hand
(sample printed with --show). Writes runs/online/analysis/blame_<arm>.{md,jsonl}.
"""
import argparse, collections, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOUBT = r"\b(not|isn't|wrong|different|instead|maybe|might|perhaps|whether|considered|correct|right)\b"
PREMISE = {   # sentence-level: every listed pattern must occur in the same sentence of the thought
    "wrong object": [r"\b{held}\b", r"\b{obj}\b|\b(correct|right|wrong|same) (object|item)\b", DOUBT],
    "put down early": [r"\b(hold|holding|held|in (my )?hand|in my inventory|take (it|the \w+ \d+) (back )?out|pick (it|the \w+ \d+) (back )?up|still (in|inside))\b",
                       r"\b(need|must|have to|should|not|no longer|isn't|first|before)\b"],
    "kept carrying": [r"\b(holding|hold|carry|carrying|in (my )?hand|hands)\b", r"\b(put|place|drop|first|one at a time|already|full|only)\b",
                      r"\b(first|before|can only|one at a time|full|already holding|need to put|drop)\b"],
    "skipped pickup": [r"\b(pick|take|holding|have|inventory)\b", r"\b(not|haven't|never|first|need)\b"],
}
KIND = {"wrong object": "wrong object", "put down early": "put down early", "kept carrying": "kept carrying",
        "skipped pickup": "skipped pickup"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", default="react_std_t1536")
    ap.add_argument("--show", type=int, default=0)
    a = ap.parse_args()
    lab = [json.loads(l) for l in open(ROOT / f"runs/online/analysis/c1_audit_{a.arm}.jsonl")]
    rows = []
    for L in lab:
        if L["kind"] not in "AB" or L["error"] not in PREMISE:
            continue
        r = json.loads((ROOT / f"runs/online/unseen/{L['id']}/{a.arm}.json").read_text())
        H = r["history"]
        th = {e["step"]: " ".join((e.get("output") or "").split()) for e in r["place_lists"]}
        obj = re.search(r"(?:some|a|an|two|the) (\w+)", r["task"].lower().replace("look at", "the").replace("examine the", "the")).group(1)
        held = None
        for t in range(1, L["e"] + 1):
            m = re.match(r"you pick up the (\w+) \d+", (H[t]["observation"] or "").lower())
            if m:
                held = m.group(1)
        pats = [x.replace("{obj}", re.escape(obj)).replace("{held}", re.escape(held or obj)) for x in PREMISE[L["error"]]]
        for t in range(L["e"] + 1, len(H)):
            if not (H[t]["observation"] or "").strip().lower().startswith("nothing happens"):
                continue
            text = th.get(t, "").split("Action:")[0].lower()
            sents = re.split(r"(?<=[.!?])\s+", text)
            hit = next((x for x in sents if all(re.search(p, x) for p in pats)), None)
            rows.append({"id": L["id"], "error": L["error"], "e": L["e"], "t": t, "command": H[t]["action"],
                         "questions_premise": bool(hit), "match": hit[:220] if hit else None,
                         "next_command": H[t + 1]["action"] if t + 1 < len(H) else None, "thought": text[:700]})
    out = ROOT / f"runs/online/analysis/blame_{a.arm}"
    with open(f"{out}.jsonl", "w") as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    games = sorted({x["id"] for x in rows})
    md = [f"# Blame after failure: {a.arm}", "",
          f"{len(games)} lost games whose origin e comes before the loop; {len(rows)} failures after e.", "",
          "| origin kind | games | failures after e | next thought questions the premise | games where it ever does |",
          "|---|---|---|---|---|"]
    for k in PREMISE:
        xs = [x for x in rows if x["error"] == k]
        gs = sorted({x["id"] for x in xs})
        ever = sorted({x["id"] for x in xs if x["questions_premise"]})
        if xs:
            md.append(f"| {k} | {len(gs)} | {len(xs)} | {sum(x['questions_premise'] for x in xs)} "
                      f"({100 * sum(x['questions_premise'] for x in xs) / len(xs):.0f}%) | {len(ever)}/{len(gs)} |")
    q = sum(x["questions_premise"] for x in rows)
    md.append(f"| all | {len(games)} | {len(rows)} | {q} ({100 * q / max(1, len(rows)):.0f}%) | "
              f"{len({x['id'] for x in rows if x['questions_premise']})}/{len(games)} |")
    first = {}
    for x in rows:
        first.setdefault(x["id"], x)
    fq = sum(v["questions_premise"] for v in first.values())
    md += ["", f"First failure after e only: the next thought questions the premise in {fq}/{len(first)} games.", ""]
    md += ["## Every failure whose next thought questions the premise", "", "| game | step | failed command | matched text | next command |", "|---|---|---|---|---|"]
    for x in rows:
        if x["questions_premise"]:
            md.append(f"| {x['id']} | {x['t']} | {x['command']} | {x['match']} | {x['next_command']} |")
    Path(f"{out}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    if a.show:
        import random
        random.seed(0)
        for x in random.sample([x for x in rows if not x["questions_premise"]], a.show):
            print(f"\n--- NOT {x['id']} t{x['t']} [{x['error']}] cmd={x['command']}\n{x['thought'][:420]}")


if __name__ == "__main__":
    main()
