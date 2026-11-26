"""Convert the ALFWorld paired-runner outputs (gameXX/natural.json, e.g.
outputs/alfworld-9b-oneshot-alternate) into verification samples and labels.

Each natural.json holds one complete rollout of the main agent (qwen3.5-9b, one-shot):
history[0] is the reset observation, history[1:] are (action, observation) steps.
Every state-changing proposed action becomes one sample whose records are the steps
before it; claims and tracker labels come from scripts/convert_alfworld.convert, and
labels.extra.action_succeeded records whether the environment then executed it.

  python scripts/convert_paired_outputs.py \
      --src baseline/oneshot12 \
      --out data/alfworld9b
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from aeda.schema import write_jsonl  # noqa: E402
from convert_alfworld import convert  # noqa: E402


def episode(game_dir: Path) -> dict:
    nat = json.loads((game_dir / "natural.json").read_text(encoding="utf-8"))
    hist = nat["history"]
    if not hist or hist[0]["action"] != "reset":
        raise ValueError(f"{game_dir}: history must start with the reset record")
    return {"episode_id": game_dir.name, "task": nat["task"], "init_obs": hist[0]["observation"],
            "steps": [{"action": h["action"], "observation": h["observation"]} for h in hist[1:]],
            "meta": {"game": nat["game"], "family": nat["family"], "won": nat["won"], "end": nat.get("end")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="folder with gameXX/natural.json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    games = sorted(p for p in Path(a.src).expanduser().glob("game*") if (p / "natural.json").is_file())
    if not games:
        raise SystemExit(f"no game*/natural.json under {a.src}")
    samples, labels, eps = [], [], []
    for g in games:
        ep = episode(g)
        s, l = convert(ep)
        for lab in l:
            lab["extra"].update({"family": ep["meta"]["family"], "game_won": ep["meta"]["won"]})
        samples += s
        labels += l
        eps.append(ep)
    out = Path(a.out)
    write_jsonl(out / "samples.jsonl", samples)
    write_jsonl(out / "labels.jsonl", labels)
    write_jsonl(out / "trajectories.jsonl", eps)
    n_fail = len({l["sid"] for l in labels if not l["extra"]["action_succeeded"]})
    n_c = sum(l["gold"] == "CONTRADICTED" for l in labels)
    calls = sum(len(s["records"]) * len(s["claims"]) for s in samples)
    print(f"{len(games)} games, {len(samples)} actions ({n_fail} failed in the environment), "
          f"{len(labels)} claims ({n_c} contradicted by tracker) -> {out}")
    print(f"upper bound of per-record judgments for one full scan (U1 at context_k=0): {calls}")


if __name__ == "__main__":
    main()
