# Online REACT (standard, 1536-token outputs) vs baseline on 9 ALFWorld games

Wins: baseline None/9, REACT (standard, 1536-token outputs) 5/9. Rescued: -. Lost: -.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: REACT (standard, 1536-token outputs))

| game | family | baseline | REACT (standard, 1536-token outputs) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| u013 | look_at_obj_in_light | - | win | None/22 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u047 | pick_clean | - | - | None/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u072 | pick_clean | - | win | None/24 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u083 | pick_cool | - | - | None/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u095 | pick_heat | - | win | None/27 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u097 | pick_heat | - | win | None/33 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u101 | pick_heat | - | win | None/15 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u102 | pick_heat | - | - | None/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| u115 | pick_heat | - | - | None/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
