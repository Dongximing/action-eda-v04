# Online SELF-EXPLORE (model lists the places) vs baseline on 24 ALFWorld games

Wins: baseline 9/24, SELF-EXPLORE (model lists the places) 15/24. Rescued: new04, new05, new09, new10, new13, new14, new15. Lost: new07.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 679 steps, not-visited list identical to the code list at 413; unusable answers 13; code-unvisited places the model left out 3465, places it listed that the code does not 56.

(per-game keys d1_won / d1_steps hold this arm's result: SELF-EXPLORE (model lists the places))

| game | family | baseline | SELF-EXPLORE (model lists the places) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new01 | pick_clean | win | win | 17/8 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new02 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new03 | pick_clean | win | win | 16/12 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new04 | pick_clean | - | win | 50/13 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| new05 | pick_clean | - | win | 50/10 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new06 | pick_clean | win | win | 9/7 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new07 | pick_clean | win | - | 10/50 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
| new08 | pick_clean | win | win | 41/10 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new09 | pick_cool | - | win | 50/44 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new10 | pick_cool | - | win | 50/22 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new11 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new12 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new13 | pick_cool | - | win | 50/40 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new14 | pick_cool | - | win | 50/12 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new15 | pick_cool | - | win | 50/10 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new16 | pick_cool | win | win | 17/7 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| new17 | pick_heat | win | win | 15/15 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new18 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new19 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new20 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| new21 | pick_heat | win | win | 10/10 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new22 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new23 | pick_heat | win | win | 7/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new24 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
