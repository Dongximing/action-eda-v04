# Online SELF-EXPLORE (model lists the places) vs baseline on 12 ALFWorld games

Wins: baseline 6/12, SELF-EXPLORE (model lists the places) 8/12. Rescued: new27, new30, new31. Lost: new25.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 317 steps, not-visited list identical to the code list at 252; unusable answers 1; code-unvisited places the model left out 359, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: SELF-EXPLORE (model lists the places))

| game | family | baseline | SELF-EXPLORE (model lists the places) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new25 | pick_clean | win | - | 8/50 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| new26 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| new27 | pick_clean | - | win | 50/17 | 0 | 0 | 0 | 0 | 0 | 0 | 9 |
| new28 | pick_clean | win | win | 19/14 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
| new29 | pick_cool | win | win | 22/41 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new30 | pick_cool | - | win | 50/9 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new31 | pick_cool | - | win | 50/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new32 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new33 | pick_heat | win | win | 12/12 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new34 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new35 | pick_heat | win | win | 8/8 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new36 | pick_heat | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
