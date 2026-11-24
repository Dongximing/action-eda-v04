#!/usr/bin/env bash
# Run all methods with Jev as the decision model over several context_k values,
# optionally add named comparison decision models (local HF), then evaluate and summarise.
#
#   DATA=data/diag JEV_ADAPTER=adapters.jev_adapter:choose GEN_MODEL=Qwen/Qwen3-4B \
#   CTX="0 1" bash scripts/run_sweep.sh
#
#   # also run the original EDA readout model as a comparison decision model:
#   COMPARE_MODELS="Qwen/Qwen3-4B" ... bash scripts/run_sweep.sh
#
# Env vars (defaults in brackets):
#   DATA            dataset dir with samples.jsonl + labels.jsonl                 [data/diag]
#   JEV_ADAPTER     module:function for Jev (required unless SKIP_JEV=1)          []
#   GEN_MODEL       HF model used only to generate text for E1 extraction         [Qwen/Qwen3-4B]
#   CTX             context_k values                                               [0 1]
#   METHODS         methods to run                                                 [H1,H2,U1,D1,D1f,D2,E1,P0,Q0]
#   COMPARE_MODELS  HF models run as named comparison decision models             []
#   SKIP_JEV        1 to run only the comparison models                           [0]
#   OUT             output root                                                    [runs/sweep]
#   EXTRA           extra args for run_offline.py, e.g. "--dtype float16"         []
set -euo pipefail
cd "$(dirname "$0")/.."

DATA=${DATA:-data/diag}
JEV_ADAPTER=${JEV_ADAPTER:-}
GEN_MODEL=${GEN_MODEL:-Qwen/Qwen3-4B}
CTX=${CTX:-"0 1"}
METHODS=${METHODS:-H1,H2,U1,D1,D1f,D2,E1,P0,Q0}
COMPARE_MODELS=${COMPARE_MODELS:-}
SKIP_JEV=${SKIP_JEV:-0}
OUT=${OUT:-runs/sweep}
EXTRA=${EXTRA:-}
PY=${PY:-python}
NAME=$(basename "$DATA")

if [ ! -f "$DATA/samples.jsonl" ] || [ ! -f "$DATA/labels.jsonl" ]; then
  echo "missing $DATA/samples.jsonl or labels.jsonl (diagnostic set: $PY scripts/make_diagnostic.py --out data/diag)" >&2
  exit 1
fi
if [ "$SKIP_JEV" != "1" ] && [ -z "$JEV_ADAPTER" ]; then
  echo "set JEV_ADAPTER=module:function (see adapters/jev_adapter.py), or SKIP_JEV=1" >&2
  exit 1
fi

run_one () {  # $1 = run dir, rest = backend args
  local run=$1; shift
  mkdir -p "$run"
  echo "== $run"
  $PY scripts/run_offline.py --samples "$DATA/samples.jsonl" --methods "$METHODS" --out "$run" \
      --gen-model "$GEN_MODEL" "$@" $EXTRA 2> >(tee "$run/stderr.log" >&2)
  $PY scripts/evaluate.py --samples "$DATA/samples.jsonl" --labels "$DATA/labels.jsonl" --run "$run" > /dev/null
}

for k in $CTX; do
  if [ "$SKIP_JEV" != "1" ]; then
    run_one "$OUT/$NAME/jev/ctx$k" --backend jev --jev-adapter "$JEV_ADAPTER" --context-k "$k"
  fi
  for model in $COMPARE_MODELS; do
    run_one "$OUT/$NAME/hf_$(echo "$model" | tr '/' '_')/ctx$k" --backend hf --model "$model" --context-k "$k"
  done
done
$PY scripts/summarize.py --root "$OUT/$NAME" | tee "$OUT/$NAME/summary.md"
