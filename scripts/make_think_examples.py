#!/usr/bin/env python3
"""Thought versions of the agent's one-shot demonstrations, from ReAct's published ALFWorld prompts.

The baseline's demonstrations (baseline/oneshot12/one_shot_examples.json) are ReAct's act_<family>_0 examples
(ReAct, MIT license: data/fewshot/LICENSE-ReAct). This script takes ReAct's react_<family>_0 examples, the same
games with the published "think:" lines, from the same file (checked by its SHA-256), and writes them in the
baseline's demonstration layout with each step as {"thought": ..., "action": ...}:
  * a think line is joined to the command that follows it (several in a row are joined with a space);
  * a command with no think line before it gets an empty thought;
  * the placement command and its feedback get the same adaptation as the baseline's examples
    ("put X in/on Y" -> "move X to Y", "You put the X in/on the Y." -> "You move the X to the Y.").

  python3 scripts/make_think_examples.py --react-prompts <alfworld_3prompts.json>
writes data/fewshot/react_think_examples.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = {"pick_clean_then_place_in_recep": "clean", "pick_heat_then_place_in_recep": "heat",
            "pick_cool_then_place_in_recep": "cool"}
SOURCE = "https://github.com/ysymyth/ReAct/blob/6bdb3a1fd38b8188fc7ba4102969fe483df8fdc9/prompts/alfworld_3prompts.json"
SHA = "a10976b4ae99f4802aa9e621933bb71065ae103f2bd273a24466ab1005fbc45a"


def adapt(command: str, feedback: str) -> tuple[str, str]:
    m = re.match(r"put (.+) in/on (.+)$", command)
    if m:
        command = f"move {m.group(1)} to {m.group(2)}"
        feedback = re.sub(r"^You put the (.+) in/on the (.+)\.$", r"You move the \1 to the \2.", feedback)
    return command, feedback


def convert(text: str) -> dict:
    lines = [ln for ln in text.strip().split("\n")]
    room, task = lines[0], lines[1]
    assert task.startswith("Your task is to: ")
    out = [f"{task}", f"Initial observation: {room}"]
    steps, pending, corrections = [], [], []
    i = 2
    while i < len(lines):
        cmd = lines[i]
        assert cmd.startswith(">"), cmd   # the published file writes "> cmd" and, a few times, ">cmd"
        cmd = cmd[1:].strip()
        fb = lines[i + 1].strip() if i + 1 < len(lines) else ""
        i += 2
        while fb.startswith(">") and fb[1:].strip().startswith("think:") and not cmd.startswith("think:"):
            # the published react_cool_0 has "> take pan 1 ...", then "> think: ...", "OK.", then the take's
            # feedback: the thought belongs before the command (recorded in "corrections")
            pending.append(fb[1:].strip()[len("think:"):].strip())
            corrections.append(f"moved the thought before '{cmd}'")
            assert lines[i] == "OK.", lines[i]
            fb, i = lines[i + 1].strip(), i + 2
        if cmd.startswith("think:"):
            assert fb == "OK.", fb
            pending.append(cmd[len("think:"):].strip())
            continue
        cmd, fb = adapt(cmd, fb)
        step = {"thought": " ".join(pending), "action": cmd}
        pending = []
        steps.append({**step, "observation": fb})
        out.append("Action: " + json.dumps(step, ensure_ascii=False, separators=(",", ":")))
        out.append(f"Observation: {fb}")
    return {"text": "\n".join(out), "steps": len(steps), "corrections": corrections}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--react-prompts", required=True, help="ReAct's prompts/alfworld_3prompts.json (any copy with the same SHA-256)")
    ap.add_argument("--out", default=str(ROOT / "data/fewshot/react_think_examples.json"))
    a = ap.parse_args()
    raw = Path(a.react_prompts).read_bytes()
    if hashlib.sha256(raw).hexdigest() != SHA:
        raise SystemExit(f"{a.react_prompts} is not the pinned ReAct file (sha256 {SHA})")
    prompts = json.loads(raw)
    examples = {fam: {"id": f"react_{short}_0", **convert(prompts[f"react_{short}_0"])} for fam, short in FAMILIES.items()}
    doc = {"source": SOURCE, "source_file_sha256": SHA, "license": "MIT (data/fewshot/LICENSE-ReAct)",
           "rule": "ReAct's react_<family>_0 examples (the same games as the baseline's act_<family>_0). Each think line "
                   "is joined to the command after it; placement command and feedback adapted to the installed grammar.",
           "examples": examples}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(a.out)
    for fam, e in examples.items():
        print(fam, e["id"], e["steps"], "steps")


if __name__ == "__main__":
    main()
