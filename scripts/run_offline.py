"""Run verifiers on (claim, history-prefix) samples and save per-claim predictions.

Example (no model needed):
  python scripts/run_offline.py --samples data/smoke/samples.jsonl \
      --backend table --table data/smoke/mock_table.json --out runs/smoke

Example (local Qwen3-4B, thinking off):
  python scripts/run_offline.py --samples data/smoke/samples.jsonl \
      --backend hf --model Qwen/Qwen3-4B --out runs/qwen3-4b
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aeda import prompts  # noqa: E402
from aeda.backends import make_backend  # noqa: E402
from aeda.schema import load_samples, write_jsonl  # noqa: E402
from aeda.verifiers import METHODS, Config, run  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--samples", required=True)
    ap.add_argument("--methods", default="H1,H2,U1,D1,D1f,D2,E1,P0,Q0")
    ap.add_argument("--backend", choices=["hf", "jev", "table"], default="table")
    ap.add_argument("--table", help="JSON table for --backend table")
    ap.add_argument("--model", default="Qwen/Qwen3-4B")
    ap.add_argument("--device", default=None)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--thinking", action="store_true", help="enable Qwen3 thinking (default off)")
    ap.add_argument("--out", required=True)
    for f in dataclasses.fields(Config):
        ap.add_argument(f"--{f.name.replace('_', '-')}", type=type(f.default) if f.type != "bool" else int,
                        default=f.default)
    a = ap.parse_args()

    methods = [m.strip() for m in a.methods.split(",") if m.strip()]
    unknown = [m for m in methods if m not in METHODS]
    if unknown:
        ap.error(f"unknown methods {unknown}; choose from {sorted(METHODS)}")
    cfg = Config(**{f.name: (bool(getattr(a, f.name)) if f.type == "bool" else getattr(a, f.name))
                    for f in dataclasses.fields(Config)})

    if a.backend == "table":
        backend = make_backend("table", table=a.table)
    elif a.backend == "hf":
        backend = make_backend("hf", model_name=a.model, device=a.device, dtype=a.dtype,
                               enable_thinking=a.thinking)
    else:
        backend = make_backend("jev")

    samples = load_samples(a.samples)
    t0 = time.time()
    rows = run(samples, methods, backend, cfg)
    wall = time.time() - t0

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "predictions.jsonl", rows)
    meta = {
        "samples": a.samples, "n_samples": len(samples),
        "n_claims": sum(len(s.claims) for s in samples),
        "methods": methods, "backend": backend.name, "thinking": a.thinking,
        "prompt_version": prompts.PROMPT_VERSION, "config": dataclasses.asdict(cfg),
        "wall_seconds": wall, "backend_usage": backend.usage.as_dict(),
        "errors": sum("error" in r for r in rows),
        "python": platform.python_version(), "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("n_claims", "methods", "backend", "wall_seconds", "errors")},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
