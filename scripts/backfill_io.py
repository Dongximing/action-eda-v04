#!/usr/bin/env python3
"""Write <arm>_io.jsonl.gz (every model request and answer, see run_online._attach_io_log) for runs finished before
the log existed. Each game is played again in a temporary copy of its folder with the run's answer cache; the
network is closed, so nothing is sent to a provider and a missing answer fails that game (reported). The replay
must reproduce the finished run's actions and outcome, otherwise its log is not written.

  python scripts/backfill_io.py [--arms direct,explore,selfexplore,...] [--folders d1,more,more2,more3] [--workers 4]

"direct" is the baseline: for the d1 games its run lives in baseline/oneshot12 (natural.json); it is replayed from
the same cache, which the d1 folders received from there.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARMS = ["direct", "explore", "selfexplore", "onecall", "onecall_use", "jevexplore", "jevexplore_name", "jevexplore_hard",
        "think_jev", "statejev", "think_state", "think_copy"]


def one(folder: str, gid: str, arm: str) -> tuple[str, str]:
    os.environ["https_proxy"] = os.environ["HTTPS_PROXY"] = "http://127.0.0.1:9"
    os.environ.setdefault("OPENROUTER_API_KEY", "replay-only")
    sys.path.insert(0, str(ROOT / "scripts"))
    import run_online as R
    sys.path.insert(0, str(R.DEFAULT_RUNNER))
    src_folder = ROOT / "runs/online" / folder / gid
    if arm == "direct":
        done_path = src_folder / "direct.json"
        if not done_path.exists():
            done_path = R.DEFAULT_SRC / gid / "natural.json"
    else:
        done_path = src_folder / f"{arm}.json"
    if not done_path.exists():
        return f"{folder}/{gid}/{arm}", "no finished run"
    done = json.loads(done_path.read_text())
    tmp = Path(tempfile.mkdtemp(prefix="backfill_io_"))
    try:
        shutil.copytree(src_folder, tmp / gid, ignore=shutil.ignore_patterns("*_io.jsonl.gz", "*.json"))
        src = R.DEFAULT_SRC
        if arm == "direct":   # make play() run the baseline itself: a src without this game's natural.json
            src = tmp / "_src"
            src.mkdir()
            for f in ("one_shot_examples.json", "protocol.json", "routing.json"):
                shutil.copy2(R.DEFAULT_SRC / f, src / f)
        proto = R.DEFAULT_SRC / "protocol.json" if (R.DEFAULT_SRC / gid).exists() else ROOT / "runs/online" / folder / "protocol.json"
        g = next(x for x in json.loads(proto.read_text())["games"] if x["id"] == gid)
        cfg = done.get("config", {}) if arm != "direct" else {}
        play_arm = "explore" if arm == "direct" else arm
        job = {"id": gid, "game": g["game"], "family": g["family"], "action_example_sha256": g["action_example_sha256"],
               "src": str(src), "out": str(tmp), "runner": str(R.DEFAULT_RUNNER), "split": str(R.DEFAULT_SPLIT),
               "route": cfg.get("route", "parasail"), "adapter": cfg.get("adapter", "adapters.openrouter_chat:choose"),
               "fewshot": cfg.get("fewshot", str(ROOT / "data/fewshot/alfworld_record_fewshot.json")),
               "record_style": cfg.get("record_style", "state"), "max_revisions": cfg.get("max_revisions", 1),
               "max_steps": cfg.get("max_steps", 50), "arm": play_arm, "tag": play_arm, "mw_k": 3, "mw_writer": "risks",
               "jev_url": cfg.get("jev_url", "http://127.0.0.1:8000/v1/systemone"), "jev_model": cfg.get("jev_model", "OneJev1.6-4B")}
        job["replay_cache"] = True   # rebuild from the stored answers; nothing is sent
        r = R.play(job)
        if arm == "direct":
            got = json.loads((tmp / gid / "direct.json").read_text())
            same = [h["action"] for h in got["history"]] == [h["action"] for h in done["history"]] and got["won"] == done["won"]
        else:
            same = [h["action"] for h in r["history"]] == [h["action"] for h in done["history"]] and r["won"] == done["won"]
        log = tmp / gid / f"{arm}_io.jsonl.gz"
        if not same:
            return f"{folder}/{gid}/{arm}", "replay differs from the finished run: log not written"
        if not log.exists():
            return f"{folder}/{gid}/{arm}", "no log produced"
        shutil.copy2(log, src_folder / log.name)
        n = sum(1 for _ in __import__("gzip").open(log, "rt"))
        return f"{folder}/{gid}/{arm}", f"ok ({n} requests)"
    except Exception as e:  # noqa: BLE001
        return f"{folder}/{gid}/{arm}", f"failed: {type(e).__name__}: {str(e)[:120]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--folders", default="d1,more,more2,more3")
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    jobs = []
    for folder in a.folders.split(","):
        for gdir in sorted((ROOT / "runs/online" / folder).glob("*/")):
            if not (gdir / "calls.sqlite").exists():
                continue
            for arm in a.arms.split(","):
                has = (gdir / ("direct.json" if arm == "direct" else f"{arm}.json")).exists() or \
                      (arm == "direct" and (ROOT / "baseline/oneshot12" / gdir.name / "natural.json").exists())
                if has and not (gdir / f"{arm}_io.jsonl.gz").exists():
                    jobs.append((folder, gdir.name, arm))
    print(f"{len(jobs)} runs to log", flush=True)
    bad = 0
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for f in as_completed([ex.submit(one, *j) for j in jobs]):
            name, status = f.result()
            bad += not status.startswith("ok")
            print(f"{name}: {status}", flush=True)
    print(f"done: {len(jobs) - bad} logged, {bad} not")


if __name__ == "__main__":
    main()
