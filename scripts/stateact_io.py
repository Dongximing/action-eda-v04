#!/usr/bin/env python3
"""Every model input and output of the official StateAct (or ReAct) run on the d1 games, in the same layout as
scripts/replay_io.py writes for our arms. Nothing is run: the run's own trace files are read.

  python3 scripts/stateact_io.py [--trial qwen35_9b_d1_50steps] [--games game02,game05]

Their client (llamp OpenAIChatText) sends, for each step, ONE user message whose text is the concatenation of
every message so far: their prompt (two annotated examples), the opening observation, then for each earlier step
">" + the cleaned output and the next observation. The trace keeps that message list and each raw model output
(`old_content`), so each request is rebuilt exactly. OpenRouter's reported tokens for each request are matched in
order from third_party/stateact/official/usage_<trial>.jsonl (time window of that game; a game that was
interrupted and rerun uses its last, finished attempt).
Writes runs/online/d1/readable/<game>_<agent>_official_io.{md,jsonl}.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "third_party/stateact/official"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--trial", default="qwen35_9b_d1_50steps")
    ap.add_argument("--games", default="", help="comma list of our game ids (default: all 12)")
    a = ap.parse_args()
    logs = OFFICIAL / "StateAct/alfworld_runs/game_logs" / f"alfworld_eval_{a.trial}"
    rows = list(csv.DictReader(open(logs / "alfworld_results.csv")))
    usage = [json.loads(l) for l in open(OFFICIAL / f"usage_{a.trial}.jsonl")]
    start = lambda r: dt.datetime.strptime(r["trace_file"][-24:-5], "%d_%m_%Y_%H_%M_%S").timestamp()  # noqa: E731
    starts = [start(r) for r in rows] + [9e12]
    last = {r["env_idx"]: i for i, r in enumerate(rows)}
    ours = {}
    for g in json.loads((ROOT / "baseline/oneshot12/protocol.json").read_text())["games"]:
        r = json.loads((ROOT / f"runs/online/d1/{g['id']}/selfexplore.json").read_text())
        ours[(r["history"][0]["observation"].split("\n\n", 1)[1].strip(), r["task"].strip().lower())] = g["id"]
    want = {g for g in a.games.split(",") if g}
    agent = rows[0]["agent_type"]
    name = "stateact" if agent == "ours-text" else agent
    out_dir = ROOT / "runs/online/d1/readable"
    out_dir.mkdir(parents=True, exist_ok=True)
    for env, i in sorted(last.items(), key=lambda x: int(x[0])):
        r = rows[i]
        tr = json.loads((logs / os.path.basename(r["trace_file"])).read_text())
        first = tr[1]["content"]
        room, task = first.split("\nYour task is to: ")[0].strip(), first.split("Your task is to: ")[1].strip()
        gid = ours[(room, task.lower())]
        if want and gid not in want:
            continue
        calls = [u for u in usage if starts[i] <= u["time"] < starts[i + 1]]
        log, k = [], 0
        for j, m in enumerate(tr):
            if m["role"] != "assistant":
                continue
            text = "".join(x["content"] for x in tr[:j])     # everything before this answer, as llamp sends it
            u = calls[k] if k < len(calls) else {}
            log.append({"n": k + 1, "who": "agent model (qwen3.5-9b)", "operation": f"{name} step",
                        "request": {"kind": "chat", "messages": [{"role": "user", "content": text}],
                                    "settings": {"temperature": 0, "stop": ["\n\n"], "reasoning": "off", "provider": "parasail"}},
                        "answer_raw": m.get("old_content", m["content"]),
                        "next_observation": tr[j + 1]["content"] if j + 1 < len(tr) else None,
                        "tokens": {"input": u.get("input_tokens"), "output": u.get("output_tokens"), "usd": u.get("cost_usd")}})
            k += 1
        base = out_dir / f"{gid}_{name}_official_io"
        with open(f"{base}.jsonl", "w", encoding="utf-8") as fh:
            for x in log:
                fh.write(json.dumps(x, ensure_ascii=False) + "\n")
        prompt = tr[0]["content"]
        md = [f"# {gid} / {name} (official code): every model input and output", "",
              f"Task: {task}  |  result: {'won' if r['success'] == 'True' else 'lost'} in {r['num_of_steps']} steps"
              f"{'  |  early stop: ' + r['early_stop'] if r['early_stop'] else ''}  |  requests: {len(log)}", "",
              "Each request is ONE user message: their prompt (below, printed once), then the opening observation and, for "
              "every earlier step, \">\" + the cleaned output and the next observation. Settings: temperature 0, stop at a "
              "blank line, reasoning off, provider Parasail.", "", "## Their prompt (the start of every request)", "", "```", prompt, "```", ""]
        for x in log:
            text = x["request"]["messages"][0]["content"]
            md += [f"## Request {x['n']}", "", f"Tokens (OpenRouter): input {x['tokens']['input']}, output {x['tokens']['output']}", "",
                   "**User message** (after their prompt)", "", "```", text[len(prompt):], "```", "",
                   "**Model output (raw)**", "", "```", x["answer_raw"], "```", "",
                   f"**Game reply**: {(x['next_observation'] or '(end)').strip()}", ""]
        Path(f"{base}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
        print(f"{base}.md  ({len(log)} requests, tokens matched {sum(x['tokens']['input'] is not None for x in log)})")


if __name__ == "__main__":
    main()
