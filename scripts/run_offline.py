"""Run verifiers on (claim, history-prefix) samples and save per-claim predictions.

Decision model (Jev) for all methods; a separate generator only for E1 extraction:
  python scripts/run_offline.py --samples data/diag/samples.jsonl --out runs/jev/diag \
      --backend jev --jev-adapter adapters.jev_adapter:choose --gen-model Qwen/Qwen3-4B

A local HF model as an explicitly named comparison decision model (e.g. the original
EDA's Qwen3-4B readout); its results must be reported under that model's name:
  python scripts/run_offline.py ... --backend hf --model Qwen/Qwen3-4B

Exit code is non-zero if any claim hit a model/interface error, unless --allow-errors.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import platform
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from aeda import prompts  # noqa: E402
from aeda.backends import HFOptionBackend, AdapterBackend, JevBackend, TableBackend  # noqa: E402
from aeda.schema import load_samples, write_jsonl  # noqa: E402
from aeda.verifiers import METHODS, NEEDS_GENERATOR, Config, run  # noqa: E402

DEFAULT_METHODS = "H1,H2,U1,D1,D1f,D2,E1,P0,Q0"


def build_config(a) -> Config:
    vals = {}
    for f in dataclasses.fields(Config):
        v = getattr(a, f.name)
        vals[f.name] = bool(v) if f.type == "bool" else v
    return Config(**vals)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--samples", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--methods", default=DEFAULT_METHODS)
    ap.add_argument("--backend", choices=["jev", "api", "hf", "table"], required=True,
                    help="decision model: jev (study model), api (named model behind an adapter, e.g. OpenRouter), "
                         "hf (named local comparison model), table (tests)")
    ap.add_argument("--jev-adapter", default=None, help="module:function, see adapters/jev_adapter.py")
    ap.add_argument("--adapter", default=None, help="module:function for --backend api, e.g. adapters.openrouter_chat:choose")
    ap.add_argument("--workers", type=int, default=1, help="concurrent (method, sample) jobs; use >1 only for API backends")
    ap.add_argument("--model", default=None, help="HF model id for --backend hf")
    ap.add_argument("--table", default=None, help="JSON table for --backend table")
    ap.add_argument("--gen-model", default=None,
                    help="HF model id used only to generate text (E1 extraction). "
                         "With --backend hf it defaults to --model.")
    ap.add_argument("--device", default=None)
    ap.add_argument("--dtype", default="bfloat16")
    ap.add_argument("--thinking", action="store_true", help="enable Qwen3 thinking for HF models (default off)")
    ap.add_argument("--allow-errors", action="store_true")
    for f in dataclasses.fields(Config):
        ap.add_argument(f"--{f.name.replace('_', '-')}", type=int if f.type in ("bool", "int") else float,
                        default=f.default)
    a = ap.parse_args()

    methods = [m.strip() for m in a.methods.split(",") if m.strip()]
    unknown = [m for m in methods if m not in METHODS]
    if unknown:
        ap.error(f"unknown methods {unknown}; choose from {sorted(METHODS)}")
    cfg = build_config(a)

    hf_cache: dict[str, HFOptionBackend] = {}

    def hf(model_id: str) -> HFOptionBackend:
        if model_id not in hf_cache:
            hf_cache[model_id] = HFOptionBackend(model_id, device=a.device, dtype=a.dtype,
                                                 enable_thinking=a.thinking)
        return hf_cache[model_id]

    if a.backend == "jev":
        backend = JevBackend(a.jev_adapter)
    elif a.backend == "api":
        backend = AdapterBackend(a.adapter)
    elif a.backend == "hf":
        if not a.model:
            ap.error("--backend hf needs --model (it is reported as that model, not as Jev)")
        backend = hf(a.model)
    else:
        if not a.table:
            ap.error("--backend table needs --table")
        backend = TableBackend.from_file(a.table)

    generator = None
    if NEEDS_GENERATOR & set(methods):
        if a.gen_model:
            generator = hf(a.gen_model)
        elif a.backend == "hf":
            generator = backend
        elif a.backend == "table":
            generator = backend
        else:
            ap.error(f"{sorted(NEEDS_GENERATOR & set(methods))} need --gen-model (Jev does not generate text)")

    samples = load_samples(a.samples)
    t0 = time.time()
    rows = run(samples, methods, backend, cfg, generator, workers=a.workers)
    wall = time.time() - t0

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "predictions.jsonl", rows)
    n_err = sum("error" in r for r in rows)
    meta = {
        "samples": a.samples, "n_samples": len(samples), "n_claims": sum(len(s.claims) for s in samples),
        "methods": methods, "decision_backend": backend.name,
        "generator": None if generator is None else generator.name,
        "thinking": a.thinking, "prompt_version": prompts.PROMPT_VERSION, "config": dataclasses.asdict(cfg),
        "wall_seconds": wall, "decision_usage": backend.usage.as_dict(),
        "generator_usage": None if generator is None or generator is backend else generator.usage.as_dict(),
        "errors": n_err, "python": platform.python_version(), "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    (out / "run_meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: meta[k] for k in ("n_claims", "methods", "decision_backend", "generator",
                                           "wall_seconds", "errors")}, ensure_ascii=False))
    if n_err:
        first = next(r for r in rows if "error" in r)
        print(f"[error] {n_err} claims failed; first: {first['method']} {first['cid']}: {first['error']}",
              file=sys.stderr)
        if not a.allow_errors:
            sys.exit(2)


if __name__ == "__main__":
    main()
