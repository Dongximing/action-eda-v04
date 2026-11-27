#!/usr/bin/env bash
# Fetch the StateAct ALFWorld few-shot data (Rozanov & Rei, arXiv 2410.02810) used by run_online.py --arm stateact.
# The repository has no license file, so the files are not committed here. They are read as data only (ast.literal_eval),
# never imported or executed.
set -euo pipefail
dest="$(cd "$(dirname "$0")/.." && pwd)/third_party/stateact/prompts"
mkdir -p "$dest"
for t in clean heat cool; do
  f="alfworld_prompts_utils_v4_${t}_base.py"
  curl -fsSL "https://raw.githubusercontent.com/ai-nikolai/StateAct/8fb47be6f5f3978a38726608ae347987341f1d82/alfworld_runs/prompts/$f" -o "$dest/$f"
  echo "$dest/$f"
done
