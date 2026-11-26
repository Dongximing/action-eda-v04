# Online H1 (whole history, multiple choice) vs baseline on 24 ALFWorld games

Wins: baseline 9/24, H1 (whole history, multiple choice) 10/24. Rescued: new15, new19. Lost: new21.

Blocked 30 proposals; agent revised 26, kept its action 4; executed despite contradiction 4; blocks the tracker calls wrong: 4; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 4, would have failed 26. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: H1 (whole history, multiple choice))

| game | family | baseline | H1 (whole history, multiple choice) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new01 | pick_clean | win | win | 17/10 | 6 | 3 | 2 | 1 | 1 | 1 | 7 |
| new02 | pick_clean | - | - | 50/50 | 44 | 0 | 0 | 0 | 0 | 0 | - |
| new03 | pick_clean | win | win | 16/15 | 4 | 1 | 1 | 0 | 0 | 0 | 14 |
| new04 | pick_clean | - | - | 50/50 | 13 | 3 | 3 | 0 | 0 | 0 | 24 |
| new05 | pick_clean | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new06 | pick_clean | win | win | 9/7 | 5 | 1 | 1 | 0 | 0 | 0 | 6 |
| new07 | pick_clean | win | win | 10/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| new08 | pick_clean | win | win | 41/41 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new09 | pick_cool | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new10 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new11 | pick_cool | - | - | 50/50 | 7 | 1 | 0 | 1 | 1 | 1 | - |
| new12 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new13 | pick_cool | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new14 | pick_cool | - | - | 50/50 | 34 | 2 | 1 | 1 | 1 | 1 | 21 |
| new15 | pick_cool | - | win | 50/11 | 7 | 1 | 1 | 0 | 0 | 0 | 10 |
| new16 | pick_cool | win | win | 17/7 | 5 | 1 | 1 | 0 | 0 | 0 | 6 |
| new17 | pick_heat | win | win | 15/15 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| new18 | pick_heat | - | - | 50/50 | 10 | 1 | 0 | 1 | 1 | 0 | - |
| new19 | pick_heat | - | win | 50/9 | 6 | 2 | 2 | 0 | 0 | 0 | 6 |
| new20 | pick_heat | - | - | 50/50 | 24 | 8 | 8 | 0 | 0 | 0 | 15 |
| new21 | pick_heat | win | - | 10/50 | 10 | 3 | 3 | 0 | 0 | 1 | 4 |
| new22 | pick_heat | - | - | 50/50 | 45 | 2 | 2 | 0 | 0 | 0 | 5 |
| new23 | pick_heat | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new24 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
