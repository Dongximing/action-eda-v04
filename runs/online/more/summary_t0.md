# Online T0 (rule tracker) vs baseline on 24 ALFWorld games

Wins: baseline 9/24, T0 (rule tracker) 11/24. Rescued: new15, new19. Lost: -.

Blocked 51 proposals; agent revised 39, kept its action 12; executed despite contradiction 17; blocks the tracker calls wrong: 0; hints shown 0.

(per-game keys d1_won / d1_steps hold this arm's result: T0 (rule tracker))

| game | family | baseline | T0 (rule tracker) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new01 | pick_clean | win | win | 17/10 | 6 | 2 | 2 | 0 | 0 | 0 | 7 |
| new02 | pick_clean | - | - | 50/50 | 19 | 10 | 6 | 4 | 6 | 0 | 7 |
| new03 | pick_clean | win | win | 16/15 | 4 | 1 | 1 | 0 | 0 | 0 | 14 |
| new04 | pick_clean | - | - | 50/50 | 10 | 9 | 3 | 6 | 7 | 0 | 22 |
| new05 | pick_clean | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new06 | pick_clean | win | win | 9/7 | 5 | 1 | 1 | 0 | 0 | 0 | 6 |
| new07 | pick_clean | win | win | 10/9 | 6 | 3 | 2 | 1 | 3 | 0 | 6 |
| new08 | pick_clean | win | win | 41/41 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new09 | pick_cool | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new10 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new11 | pick_cool | - | - | 50/50 | 7 | 0 | 0 | 0 | 0 | 0 | - |
| new12 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new13 | pick_cool | - | - | 50/50 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new14 | pick_cool | - | - | 50/50 | 34 | 2 | 2 | 0 | 0 | 0 | 21 |
| new15 | pick_cool | - | win | 50/11 | 7 | 1 | 1 | 0 | 0 | 0 | 10 |
| new16 | pick_cool | win | win | 17/7 | 5 | 1 | 1 | 0 | 0 | 0 | 6 |
| new17 | pick_heat | win | win | 15/15 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| new18 | pick_heat | - | - | 50/50 | 6 | 2 | 1 | 1 | 1 | 0 | 8 |
| new19 | pick_heat | - | win | 50/9 | 6 | 2 | 2 | 0 | 0 | 0 | 6 |
| new20 | pick_heat | - | - | 50/50 | 28 | 13 | 13 | 0 | 0 | 0 | 15 |
| new21 | pick_heat | win | win | 10/17 | 9 | 2 | 2 | 0 | 0 | 0 | 4 |
| new22 | pick_heat | - | - | 50/50 | 46 | 2 | 2 | 0 | 0 | 0 | 5 |
| new23 | pick_heat | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new24 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
