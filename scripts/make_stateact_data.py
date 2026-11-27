#!/usr/bin/env python3
"""A data folder for the official StateAct code holding only the given valid_unseen games (copies from
data/alfworld/json_2.1.1/valid_unseen, checked against runs/online/unseen/protocol.json).

  python3 scripts/make_stateact_data.py --games u013,u047,u072,u083,u095,u097,u101,u102,u115 \
      --out third_party/stateact/alfworld_data_9

Then: ALFWORLD_DATA=<out> TRIAL=<name> NUM=<number of games> bash scripts/run_stateact_official.sh
Their code runs every game in the folder's valid_unseen split. The game list is written to <out>/games.json.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--games", required=True, help="comma list of our ids (u001-u134)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    src = ROOT / "data/alfworld/json_2.1.1/valid_unseen"
    out = Path(a.out) if Path(a.out).is_absolute() else ROOT / a.out
    games = {g["id"]: g for g in json.loads((ROOT / "runs/online/unseen/protocol.json").read_text())["games"]}
    if out.exists():
        shutil.rmtree(out)
    (out / "logic").mkdir(parents=True)
    for f in ("alfred.pddl", "alfred.twl2"):
        shutil.copy2(ROOT / "data/alfworld/logic" / f, out / "logic" / f)
    for s in ("train", "valid_seen", "valid_unseen"):
        (out / "json_2.1.1" / s).mkdir(parents=True, exist_ok=True)
    rows = []
    for gid in [g for g in a.games.split(",") if g]:
        g = games[gid]
        trial = Path(g["game"]).parent
        shutil.copytree(src / trial, out / "json_2.1.1/valid_unseen" / trial)
        ok = hashlib.sha256((out / "json_2.1.1/valid_unseen" / trial / "game.tw-pddl").read_bytes()).hexdigest() == g["sha256"]
        if not ok:
            raise SystemExit(f"{gid}: game file differs from the protocol")
        rows.append({"id": gid, "game": g["game"], "family": g["family"]})
    (out / "games.json").write_text(json.dumps({"games": rows}, indent=1))
    print(f"{len(rows)} games -> {out}")


if __name__ == "__main__":
    main()
