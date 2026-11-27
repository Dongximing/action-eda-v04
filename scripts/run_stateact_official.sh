#!/usr/bin/env bash
# Run the OFFICIAL StateAct code (github.com/ai-nikolai/StateAct, pinned commit) with qwen/qwen3.5-9b through
# OpenRouter on our 12 d1 games. Run it yourself, in a terminal where OPENROUTER_API_KEY is set:
#
#   bash scripts/run_stateact_official.sh
#
# What it does:
#   1. clones their repository into third_party/stateact/official/StateAct and checks out commit 8fb47be;
#   2. makes a Python 3.11 environment for it (third_party/stateact/official/.venv) with what their
#      alfworld_runs/requirements.txt asks for, except vllm (local GPU models only; llamp is installed without it);
#   3. runs their alfworld_run.py as their README's reproduction command, with the model changed and the step
#      limit set to 50 environment steps per game (their LIMIT 100 -> 51, see below):
#      --agent ours-text, keys goal/locations_visited/current_location/current_inventory/thought/action,
#      --prompt_ids 1 0, --apply_correction, temperature 0, --llm_type OpenAIChatText (their OpenAI client,
#      pointed at OpenRouter through OPENAI_BASE_URL), --num_envs 12.
# Games: ALFWORLD_DATA=third_party/stateact/alfworld_data, whose valid_unseen folder holds only our 12 d1 games
# (copies from data/alfworld, valid_seen), so their default split eval_out_of_distribution runs exactly those.
# Request settings: scripts/stateact_official_shim/sitecustomize.py adds reasoning off and the provider route of
# baseline/oneshot12/routing.json to every request (as in our own arms) and logs OpenRouter's usage; without it
# qwen3.5-9b returns no answer text. Their code, prompts and parsing are unchanged.
# Their ReAct baseline instead of StateAct: AGENT=react bash scripts/run_stateact_official.sh (two ReAct examples per
# task type with "think:" steps; a think step is a model call that counts toward the same limit, as in their code).
# Other games: ALFWORLD_DATA=<folder laid out like alfworld_data> TRIAL=<name> NUM=<number of games> bash scripts/run_stateact_official.sh
#   e.g. the 35 valid_unseen games standard ReAct lost (third_party/stateact/alfworld_data_lost35, list in its games.json):
#   ALFWORLD_DATA=third_party/stateact/alfworld_data_lost35 TRIAL=qwen35_9b_unseen_lost35 NUM=35 bash scripts/run_stateact_official.sh
# Resume after an interruption: START=<first env index not finished> NUM=<how many> bash scripts/run_stateact_official.sh
# (their alfworld_results.csv in the same trial folder gets the new rows appended).
# Logs: third_party/stateact/official/StateAct/alfworld_runs/game_logs/alfworld_eval_<trial>/ and
#       third_party/stateact/official/usage_<trial>.jsonl
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WORK="$ROOT/third_party/stateact/official"
COMMIT=8fb47be6f5f3978a38726608ae347987341f1d82
: "${OPENROUTER_API_KEY:?set OPENROUTER_API_KEY in this terminal first}"

mkdir -p "$WORK"
if [ ! -d "$WORK/StateAct/.git" ]; then
  git clone https://github.com/ai-nikolai/StateAct "$WORK/StateAct"
fi
git -C "$WORK/StateAct" checkout -q -- . && git -C "$WORK/StateAct" checkout -q "$COMMIT"
# the one change to their code: 50 environment steps per game, as in all our arms (their LIMIT = 100). Their loop
# calls the model, counts the call, and stops when the count reaches LIMIT before stepping, so LIMIT = 51 lets
# 50 actions run (the 51st reply is not executed and is left out of the token counts).
sed -i '' 's/^        LIMIT = 100$/        LIMIT = 51/' "$WORK/StateAct/alfworld_runs/alfworld_run.py"
grep -q '^        LIMIT = 51$' "$WORK/StateAct/alfworld_runs/alfworld_run.py" || { echo "step limit patch failed"; exit 1; }

PY="$WORK/.venv/bin/python"
if [ ! -x "$PY" ]; then
  uv venv -p 3.11 "$WORK/.venv"
  uv pip install --python "$PY" "llamp==0.0.19" --no-deps
  uv pip install --python "$PY" openai tiktoken pyyaml "transformers>=4.48.2"
  # their pins first; on failure the versions our own ALFWorld environment runs on this Mac
  uv pip install --python "$PY" "alfworld==0.4.2" "textworld==1.6.2" "fast-downward-textworld==20.6.3" \
    || uv pip install --python "$PY" "alfworld==0.4.2" "textworld==1.7.0" "fast-downward-textworld==20.6.4"
fi

export OPENAI_API_KEY="$OPENROUTER_API_KEY"
export OPENAI_BASE_URL="https://openrouter.ai/api/v1"
export ALFWORLD_DATA="${ALFWORLD_DATA:-$ROOT/third_party/stateact/alfworld_data}"   # its valid_unseen folder = the games run
case "$ALFWORLD_DATA" in /*) ;; *) ALFWORLD_DATA="$ROOT/$ALFWORLD_DATA" ;; esac    # the run below starts in their folder
[ -d "$ALFWORLD_DATA/json_2.1.1/valid_unseen" ] || { echo "no json_2.1.1/valid_unseen in $ALFWORLD_DATA"; exit 1; }
# request settings only (reasoning off, provider route as our arms) and OpenRouter usage logging; see the shim
AGENT="${AGENT:-ours-text}"     # ours-text = StateAct; react = their ReAct baseline (README step 8)
if [ "$AGENT" = "react" ]; then DEFAULT_TRIAL=qwen35_9b_d1_50steps_react; else DEFAULT_TRIAL=qwen35_9b_d1_50steps; fi
TRIAL="${TRIAL:-$DEFAULT_TRIAL}"
KEYS=()
if [ "$AGENT" = "ours-text" ]; then
  KEYS=(--keys_to_use '["goal","locations_visited","current_location","current_inventory","thought","action"]')
fi
export PYTHONPATH="$ROOT/scripts/stateact_official_shim${PYTHONPATH:+:$PYTHONPATH}"
export STATEACT_ROUTE="$("$PY" -c 'import json,sys;print(json.load(open(sys.argv[1]))["selected"])' "$ROOT/baseline/oneshot12/routing.json")"
export STATEACT_USAGE_LOG="$WORK/usage_$TRIAL.jsonl"

cd "$WORK/StateAct/alfworld_runs"
mkdir -p game_logs
"$PY" alfworld_run.py \
  --agent "$AGENT" \
  --llm_type "OpenAIChatText" \
  --model "qwen/qwen3.5-9b" \
  --force_model \
  ${KEYS[@]+"${KEYS[@]}"} \
  --trial_name "$TRIAL" \
  --start_index "${START:-0}" \
  --num_envs "${NUM:-12}" \
  --prompt_ids 1 0 \
  --apply_correction \
  --force_run \
  --eval_split eval_out_of_distribution
