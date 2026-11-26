# Online ONE-CALL (agent lists places, then acts, same call) vs baseline on 12 ALFWorld games

Wins: baseline 6/12, ONE-CALL (agent lists places, then acts, same call) 6/12. Rescued: -. Lost: -.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 378 steps, not-visited list identical to the code list at 276; unusable answers 7; code-unvisited places the model left out 97, places it listed that the code does not 8.

(per-game keys d1_won / d1_steps hold this arm's result: ONE-CALL (agent lists places, then acts, same call))

| game | family | baseline | ONE-CALL (agent lists places, then acts, same call) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new25 | pick_clean | win | win | 8/14 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new26 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new27 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new28 | pick_clean | win | win | 19/19 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new29 | pick_cool | win | win | 22/19 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new30 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new31 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new32 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new33 | pick_heat | win | win | 12/10 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new34 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new35 | pick_heat | win | win | 8/9 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| new36 | pick_heat | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
