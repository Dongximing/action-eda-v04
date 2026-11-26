# ALFWorld data (copy)

Unmodified copy of two folders from the ALFWorld release:

- `json_2.1.1/valid_seen/` — the 242 valid_seen games (`game.tw-pddl`, `initial_state.pddl`, `traj_data.json`).
  All 68 games of the online runs (`runs/online/{d1,more,more2,more3}`) come from here; each result file
  stores its game path relative to this folder.
- `logic/` — `alfred.pddl` and `alfred.twl2`.

Copied from `~/state-audit-pilot/data/alfworld/` (downloaded with `alfworld-download`).
The train, valid_train and valid_unseen splits and the detectors are not included.
Source and license: https://github.com/alfworld/alfworld
