#!/usr/bin/env python3
"""E3 of docs/early_error_study_design.md §5: a judge model reads the history so far and says whether the agent
has made an uncorrected mistake. No hand-written rules. Offline, local OneJev (System One API, scripts/onejev_mac_server.py).

  python3 scripts/c2_judge_offline.py [--run runs/online/unseen] [--arm react_std_t1536] [--games u001,u002] [--limit N]

For each game and step t the judge gets the task, the opening observation and records 1..t (command, feedback),
nothing later and nothing from the environment's internals. Two yes/no ("noul") questions share that prefix:
  mistake   "The agent has made a mistake that it has not corrected."
  on_track  "The agent is on track to complete the task."
Lost games are asked up to their stuck-window start + 1 (nothing later is scored); won games at every step.
Answers are cached in runs/online/analysis/c2_judge_<arm>.jsonl (one line per game and step), so a rerun resumes.
Score with: python3 scripts/c2_judge_offline.py --score
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from analyze_loops import stuck_start  # noqa: E402

QUESTIONS = {
    "mistake": {"type": "noul", "instructions": "The agent has made a mistake that it has not corrected."},
    "on_track": {"type": "noul", "instructions": "The agent is on track to complete the task."},
}


def ask(url: str, state: dict) -> dict:
    data = json.dumps({"state": state, "questions": QUESTIONS}, ensure_ascii=False).encode("utf-8")
    for i in range(5):
        try:
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=600) as r:
                out = json.load(r)
            return {k: float(out["answers"][k]["noul"]) for k in QUESTIONS} | {"prefix_tokens": out["meta"].get("prefix_tokens")}
        except Exception:  # noqa: BLE001
            if i == 4:
                raise
            time.sleep(2 ** i)


def state_at(r: dict, t: int) -> dict:
    """What the judge may read at step t: the task, the opening observation and records 1..t."""
    h = r["history"]
    return {"task": r["task"], "opening_observation": h[0]["observation"],
            "records": [{"step": i, "command": h[i]["action"], "feedback": h[i]["observation"]} for i in range(1, t + 1)]}


def collect(a):
    out = ROOT / f"runs/online/analysis/c2_judge_{a.arm}.jsonl"
    done = set()
    if out.exists():
        done = {(x["id"], x["t"]) for x in map(json.loads, open(out))}
    games = {f.parent.name: json.loads(f.read_text()) for f in sorted(Path(a.run).glob(f"*/{a.arm}.json"))}
    want = [g for g in a.games.split(",") if g] or sorted(games)
    jobs = []
    for g in want:
        r = games[g]
        n = len(r["history"]) - 1
        last = n if r["won"] else min(n, (stuck_start(r["history"], 5) or n) + 1)
        jobs += [(g, t) for t in range(1, last + 1) if (g, t) not in done]
    if a.limit:
        jobs = jobs[:a.limit]
    print(f"{len(jobs)} requests to ask ({len(done)} cached)", flush=True)
    t0 = time.time()
    with open(out, "a") as fh:
        for k, (g, t) in enumerate(jobs, 1):
            ans = ask(a.url, state_at(games[g], t))
            fh.write(json.dumps({"id": g, "t": t, **ans}) + "\n")
            fh.flush()
            if k % 50 == 0 or k == len(jobs):
                el = time.time() - t0
                print(f"{k}/{len(jobs)}  {el / k:.2f}s each, about {el / k * (len(jobs) - k) / 60:.0f} min left", flush=True)


def score(a):
    rows = [json.loads(l) for l in open(ROOT / f"runs/online/analysis/c2_judge_{a.arm}.jsonl")]
    by = {}
    for x in rows:
        by.setdefault(x["id"], {})[x["t"]] = x
    labels = {x["id"]: x for x in map(json.loads, open(ROOT / f"runs/online/analysis/c1_audit_{a.arm}.jsonl"))}
    games = {f.parent.name: json.loads(f.read_text()) for f in sorted(Path(a.run).glob(f"*/{a.arm}.json"))}
    lost = [g for g in labels if labels[g]["t_L"] and g in by]
    early = [g for g in lost if labels[g]["kind"] in "AB"]
    won = [g for g, r in games.items() if r["won"] and g in by]
    md = [f"# C2 / E3: judge model (OneJev1.6-4B, local) on {a.arm}", "",
          f"Scored games: {len(lost)} lost with a stuck window ({len(early)} with e before the loop), {len(won)} won. "
          "Alarm at step t when the score >= threshold. Score: P(yes) of `mistake`, or 1 - P(yes) of `on_track`.", "",
          "| score | threshold | caught in [e, t_L) (early games) | first alarm before e (lost) | won games with an alarm | "
          "alarms per step, won | lead t_L-d (median) |", "|---|---|---|---|---|---|---|"]
    for name, f in (("mistake", lambda x: x["mistake"]), ("not on_track", lambda x: 1 - x["on_track"])):
        for th in (0.3, 0.5, 0.7, 0.8, 0.9, 0.95):
            al = {g: [t for t, x in sorted(by[g].items()) if f(x) >= th] for g in lost + won}
            hit = [next((d for d in al[g] if labels[g]["e"] <= d < labels[g]["t_L"]), None) for g in early]
            before = sum(1 for g in lost if al[g] and al[g][0] < labels[g]["e"])
            won_any = sum(1 for g in won if al[g])
            steps = sum(len(by[g]) for g in won)
            leads = [labels[g]["t_L"] - d for g, d in zip(early, hit) if d is not None]
            k = sum(d is not None for d in hit)
            md.append(f"| {name} | {th} | {k}/{len(early)} ({100 * k / max(1, len(early)):.0f}%) | {before}/{len(lost)} | "
                      f"{won_any}/{len(won)} ({100 * won_any / max(1, len(won)):.0f}%) | "
                      f"{sum(len(al[g]) for g in won) / max(1, steps):.3f} | {statistics.median(leads) if leads else '-'} |")
    # how well the score separates the step at e from steps of won games
    for name, f in (("mistake", lambda x: x["mistake"]), ("not on_track", lambda x: 1 - x["on_track"])):
        pos = [f(by[g][labels[g]["e"]]) for g in early if labels[g]["e"] in by[g]]
        neg = [f(x) for g in won for x in by[g].values()]
        auc = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg) / max(1, len(pos) * len(neg))
        md.append("")
        md.append(f"`{name}`: mean score at the error step e {statistics.mean(pos):.3f} (n {len(pos)}), at steps of won games "
                  f"{statistics.mean(neg):.3f} (n {len(neg)}); AUC (error step vs won-game step) {auc:.3f}")
    out = ROOT / f"runs/online/analysis/c2_judge_{a.arm}.md"
    out.write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", default=str(ROOT / "runs/online/unseen"))
    ap.add_argument("--arm", default="react_std_t1536")
    ap.add_argument("--url", default="http://127.0.0.1:8000/v1/systemone")
    ap.add_argument("--games", default="")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--score", action="store_true")
    a = ap.parse_args()
    score(a) if a.score else collect(a)


if __name__ == "__main__":
    main()
