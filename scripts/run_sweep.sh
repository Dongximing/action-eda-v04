#!/usr/bin/env bash
# Sweep models x context_k on one dataset, then evaluate and summarise.
#
#   DATA=data/diag MODELS="Qwen/Qwen3-4B Qwen/Qwen3.5-4B" CTX="0 1" bash scripts/run_sweep.sh
#
# Env vars (defaults in brackets):
#   DATA     dataset dir with samples.jsonl + labels.jsonl          [data/diag]
#   MODELS   space-separated HF model ids                           [Qwen/Qwen3-4B]
#   CTX      space-separated context_k values                       [0 1]
#   METHODS  comma-separated methods                                [H1,H2,U1,D1,D1f,D2,E1,P0,Q0]
#   OUT      output root                                            [runs/sweep]
#   EXTRA    extra args for run_offline.py, e.g. "--dtype float16"  []
set -euo pipefail
cd "$(dirname "$0")/.."

DATA=${DATA:-data/diag}
MODELS=${MODELS:-Qwen/Qwen3-4B}
CTX=${CTX:-"0 1"}
METHODS=${METHODS:-H1,H2,U1,D1,D1f,D2,E1,P0,Q0}
OUT=${OUT:-runs/sweep}
EXTRA=${EXTRA:-}
PY=${PY:-python}

if [ ! -f "$DATA/samples.jsonl" ]; then
  echo "missing $DATA/samples.jsonl (for the diagnostic set run: $PY scripts/make_diagnostic.py --out data/diag)" >&2
  exit 1
fi

for model in $MODELS; do
  tag=$(echo "$model" | tr '/' '_')
  for k in $CTX; do
    run="$OUT/$(basename "$DATA")/${tag}/ctx${k}"
    mkdir -p "$run"
    echo "== $model ctx=$k -> $run"
    $PY scripts/run_offline.py --samples "$DATA/samples.jsonl" --backend hf --model "$model" \
        --context-k "$k" --methods "$METHODS" --out "$run" $EXTRA 2> >(tee "$run/stderr.log" >&2)
    $PY scripts/evaluate.py --samples "$DATA/samples.jsonl" --labels "$DATA/labels.jsonl" --run "$run" > /dev/null
  done
done
$PY scripts/summarize.py --root "$OUT/$(basename "$DATA")" | tee "$OUT/$(basename "$DATA")/summary.md"
