# Online T0 (rule tracker) vs baseline on 12 ALFWorld games

Wins: baseline 6/12, T0 (rule tracker) 7/12. Rescued: new27. Lost: -.

Blocked 7 proposals; agent revised 5, kept its action 2; executed despite contradiction 2; blocks the tracker calls wrong: 0; hints shown 0.

(per-game keys d1_won / d1_steps hold this arm's result: T0 (rule tracker))

| game | family | baseline | T0 (rule tracker) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new25 | pick_clean | win | win | 8/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| new26 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new27 | pick_clean | - | win | 50/21 | 5 | 2 | 1 | 1 | 1 | 0 | 17 |
| new28 | pick_clean | win | win | 19/19 | 4 | 1 | 0 | 1 | 1 | 0 | - |
| new29 | pick_cool | win | win | 22/19 | 10 | 1 | 1 | 0 | 0 | 0 | 18 |
| new30 | pick_cool | - | - | 50/50 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new31 | pick_cool | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new32 | pick_cool | - | - | 50/50 | 11 | 2 | 2 | 0 | 0 | 0 | 45 |
| new33 | pick_heat | win | win | 12/12 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new34 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new35 | pick_heat | win | win | 8/8 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new36 | pick_heat | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
