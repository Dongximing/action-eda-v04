# Online ONE-CALL-USE (lists, then an action based on them, same call) vs baseline on 24 ALFWorld games

Wins: baseline 9/24, ONE-CALL-USE (lists, then an action based on them, same call) 6/24. Rescued: new04, new11. Lost: new01, new07, new16, new17, new23.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 1001 steps, not-visited list identical to the code list at 616; unusable answers 51; code-unvisited places the model left out 2153, places it listed that the code does not 317.

(per-game keys d1_won / d1_steps hold this arm's result: ONE-CALL-USE (lists, then an action based on them, same call))

| game | family | baseline | ONE-CALL-USE (lists, then an action based on them, same call) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new01 | pick_clean | win | - | 17/50 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new02 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new03 | pick_clean | win | win | 16/15 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new04 | pick_clean | - | win | 50/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new05 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new06 | pick_clean | win | win | 9/5 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new07 | pick_clean | win | - | 10/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new08 | pick_clean | win | win | 41/13 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new09 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new10 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new11 | pick_cool | - | win | 50/46 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new12 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new13 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new14 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new15 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new16 | pick_cool | win | - | 17/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new17 | pick_heat | win | - | 15/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new18 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new19 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| new20 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new21 | pick_heat | win | win | 10/13 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| new22 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new23 | pick_heat | win | - | 7/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new24 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
