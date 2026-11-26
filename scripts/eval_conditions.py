#!/usr/bin/env python3
"""Offline benchmark of condition writers (aeda/conditions.py) on baseline checkpoints.

Checkpoints: proposals of checked commands (the baseline's CHECK_VERBS) in the baseline
trajectories of the 68 online games (src natural.json for gameXX, direct.json for newXX),
deduplicated by (game, command, tracker state) so loops count once, then a fixed-seed sample
of up to --n, half of them commands that failed in the environment.

For every writer the agent model writes conditions once per checkpoint (cached in
<out>/calls.sqlite, so a rerun is free). Scores, using the tracker only as a reference:

  required covered      the location / hand preconditions of the command (aeda.alfworld.preconditions)
                        that the writer wrote (parsed with aeda.alfworld.parse_claim)
  failure explained     commands that failed because a location / hand precondition was false:
                        the writer wrote a location / hand condition the tracker calls false
  false-alarm condition commands that succeeded, but a written location / hand condition is false
                        (the condition is not really needed; D1 judging it correctly would block)
  effect written        clean / heat / cool commands with a condition saying the object is already
                        clean / hot / cool (the command's effect, not a precondition)
  free text             conditions that are not location / hand conditions (cannot be scored here)

  export OPENROUTER_API_KEY=...
  ~/state-audit-pilot/.venv/bin/python scripts/eval_conditions.py --writers risks,v2,v2demo
Writes <out>/report.md and <out>/conditions.jsonl.
"""
from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from aeda import alfworld as A  # noqa: E402
from aeda import conditions as W  # noqa: E402

YO = Path.home() / "Documents/Codex/2026-11-21/yo/outputs"
DEFAULT_SRC = YO / "alfworld-9b-oneshot-alternate"
DEFAULT_RUNNER = YO / "alfworld-action-eda-oneshot-altprovider"
EFFECT = {"clean": r"\b(clean|cleaned|washed)\b", "heat": r"\b(hot|heated|warm|warmed)\b",
          "cool": r"\b(cool|cooled|cold|chilled)\b"}


def baseline_trajectories(src: Path, dirs: list[Path]) -> list[dict]:
    out = []
    for d in dirs:
        for g in sorted(d.iterdir()):
            if not g.is_dir():
                continue
            if (g / "direct.json").exists():
                t = json.loads((g / "direct.json").read_text())
            elif (src / g.name / "natural.json").exists():
                t = json.loads((src / g.name / "natural.json").read_text())
            else:
                continue
            out.append({"id": g.name, "family": t["family"], "task": t["task"], "history": t["history"]})
    return out


def checkpoints(trajs: list[dict], check_verbs, n: int, seed: int) -> list[dict]:
    seen, fail, ok = set(), [], []
    for t in trajs:
        h = t["history"]
        for i in range(1, len(h)):
            act = h[i]["action"]
            if (act.lower().split() or [""])[0] not in check_verbs:
                continue
            steps = [(x["action"], x["observation"]) for x in h[1:i]]
            st = A.replay(steps)
            key = (t["id"], act, st.loc, st.holding)
            if key in seen:
                continue
            seen.add(key)
            cp = {"id": t["id"], "family": t["family"], "step": i - 1, "task": t["task"], "action": act, "history": h[:i],
                  "succeeded": A.succeeded(h[i]["observation"])}
            (ok if cp["succeeded"] else fail).append(cp)
    rng = random.Random(seed)
    half = n // 2
    pick = rng.sample(fail, min(half, len(fail)))
    pick += rng.sample(ok, min(n - len(pick), len(ok)))
    return sorted(pick, key=lambda c: (c["id"], c["step"]))


def score(cp: dict, conds: list[dict]) -> dict:
    steps = [(x["action"], x["observation"]) for x in cp["history"][1:]]
    st = A.replay(steps)
    need = [p["spec"] for p in A.preconditions(cp["action"])]
    parsed = [(c["claim"], A.parse_claim(c["claim"])) for c in conds]
    specs = [s for _, s in parsed if s]
    false_specs = [s for s in specs if A.evaluate_spec(s, st) == "CONTRADICTED"]
    need_false = [s for s in need if A.evaluate_spec(s, st) == "CONTRADICTED"]
    verb = A.parse_action(cp["action"])[0]
    obj = (A.parse_action(cp["action"])[1] or [""])[0]
    effect = verb in EFFECT and any(obj and obj in c["claim"].lower() and re.search(EFFECT[verb], c["claim"].lower())
                                    and not re.search(r"\bnot\b|\bdirty\b", c["claim"].lower()) for c in conds)
    return {"n": len(conds), "free": sum(s is None for _, s in parsed),
            "need": len(need), "covered": sum(s in specs for s in need),
            "catchable_failure": (not cp["succeeded"]) and bool(need_false),
            "explained": (not cp["succeeded"]) and bool(need_false) and bool(false_specs),
            "false_alarm": cp["succeeded"] and bool(false_specs),
            "not_required": sum(s not in need for s in specs), "effect": effect}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", default=str(DEFAULT_SRC))
    ap.add_argument("--runs", default="runs/online/d1,runs/online/more,runs/online/more2,runs/online/more3")
    ap.add_argument("--runner", default=str(DEFAULT_RUNNER))
    ap.add_argument("--writers", default="risks,v2,v2demo")
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--n", type=int, default=160)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", default="runs/conditions")
    a = ap.parse_args()
    writers = [w for w in a.writers.split(",") if w]
    for w in writers:
        if w not in W.WRITERS:
            ap.error(f"unknown writer {w} (choose from {', '.join(W.WRITERS)})")
    if not os.getenv("OPENROUTER_API_KEY"):
        ap.error("set OPENROUTER_API_KEY in this terminal")
    sys.path.insert(0, a.runner)
    from audit import CHECK_VERBS
    from models import GPUChat, public_checkpoint as model_cp
    from paired_store import CallBook, digest
    from pilot import public_checkpoint
    from providers import ProviderError

    src, out = Path(a.src).expanduser(), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    cps = checkpoints(baseline_trajectories(src, [Path(d) for d in a.runs.split(",")]), CHECK_VERBS, a.n, a.seed)
    route = json.loads((src / "routing.json").read_text())["selected"]
    actor = GPUChat("https://openrouter.ai/api/v1", "qwen/qwen3.5-9b", os.environ["OPENROUTER_API_KEY"], openrouter=True)
    actor.openrouter_route = route
    examples = json.loads((src / "one_shot_examples.json").read_text())["examples"]
    book = CallBook(out / "calls.sqlite")
    rows, agg = [], {w: Counter() for w in writers}
    try:
        for i, c in enumerate(cps, 1):
            view = {"task": c["task"], "observation": c["history"][-1]["observation"], "history": c["history"]}
            cp = public_checkpoint(view, c["action"])
            actor.action_example = examples[c["family"]]  # the same one-shot demo the agent had in this game
            for w in writers:
                op = "risks" if w == "risks" else f"conditions-{w}"
                inputs = [cp, a.k] + ([digest(actor.action_example)] if w == "v2demo" else [])
                try:
                    conds = book.ask("eval", "qwen", op, inputs, actor,
                                     lambda: W.write(actor, cp, w, a.k, model_cp))
                    err = None
                except (ProviderError, ValueError) as e:
                    conds, err = [], f"{type(e).__name__}: {e}"
                s = score(c, conds)
                g = agg[w]
                g["checkpoints"] += 1
                g["errors"] += err is not None
                for key in ("n", "free", "need", "covered", "not_required"):
                    g[key] += s[key]
                for key in ("catchable_failure", "explained", "false_alarm", "effect"):
                    g[key] += bool(s[key])
                g["succeeded"] += c["succeeded"]
                g["effect_eligible"] += A.parse_action(c["action"])[0] in EFFECT
                rows.append({"id": c["id"], "step": c["step"], "action": c["action"], "succeeded": c["succeeded"],
                             "writer": w, "conditions": [x["claim"] for x in conds], "error": err, **s})
            if i % 20 == 0:
                print(f"{i}/{len(cps)} checkpoints", flush=True)
    finally:
        book.close()
    with (out / "conditions.jsonl").open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def pct(x, y):
        return "-" if not y else f"{x}/{y} ({100 * x / y:.0f}%)"
    lines = [f"# Condition writers on {len(cps)} baseline checkpoints", "",
             f"{sum(not c['succeeded'] for c in cps)} failed in the env, {sum(c['succeeded'] for c in cps)} succeeded; "
             f"k = {a.k}; writer = qwen/qwen3.5-9b ({route}).", "",
             "| writer | conditions / checkpoint | free text | required covered | failure explained | "
             "false-alarm condition | not-required loc/hand | effect written | errors |",
             "|---|---|---|---|---|---|---|---|---|"]
    for w in writers:
        g = agg[w]
        lines.append(f"| {w} | {g['n'] / max(1, g['checkpoints']):.2f} | {pct(g['free'], g['n'])} | "
                     f"{pct(g['covered'], g['need'])} | {pct(g['explained'], g['catchable_failure'])} | "
                     f"{pct(g['false_alarm'], g['succeeded'])} | {g['not_required']} | "
                     f"{pct(g['effect'], g['effect_eligible'])} | {g['errors']} |")
    text = "\n".join(lines) + "\n"
    (out / "report.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
