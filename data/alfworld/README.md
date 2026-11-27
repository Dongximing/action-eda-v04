# ALFWorld data (copy)

Unmodified copy of two folders from the ALFWorld release:

- `json_2.1.1/valid_seen/` — the 242 valid_seen games (`game.tw-pddl`, `initial_state.pddl`, `traj_data.json`).
  All 68 games of the online runs (`runs/online/{d1,more,more2,more3}`) come from here; each result file
  stores its game path relative to this folder.
- `json_2.1.1/valid_unseen/` — the 134 valid_unseen games (ALFWorld's eval_out_of_distribution, the standard test set
  of ReAct, StateAct and VBL), all 6 task types. `runs/online/unseen/protocol.json` lists them, selected with the
  rules of alfworld's AlfredTWEnv.collect_game_files (task type, no movable/Sliced, game file present and solvable).
- `logic/` — `alfred.pddl` and `alfred.twl2`.

Copied from `~/state-audit-pilot/data/alfworld/` (downloaded with `alfworld-download`).
The train and valid_train splits and the detectors are not included.
Source: https://github.com/alfworld/alfworld (MIT License, copied in `LICENSE`).
