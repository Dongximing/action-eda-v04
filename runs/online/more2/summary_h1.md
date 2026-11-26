# Online H1 (whole history, multiple choice) vs baseline on 12 ALFWorld games

Wins: baseline 6/12, H1 (whole history, multiple choice) 7/12. Rescued: new27. Lost: -.

Blocked 18 proposals; agent revised 18, kept its action 0; executed despite contradiction 8; blocks the tracker calls wrong: 1; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 1, would have failed 17. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: H1 (whole history, multiple choice))

| game | family | baseline | H1 (whole history, multiple choice) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new25 | pick_clean | win | win | 8/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| new26 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new27 | pick_clean | - | win | 50/20 | 5 | 2 | 2 | 0 | 0 | 0 | 17 |
| new28 | pick_clean | win | win | 19/18 | 4 | 1 | 1 | 0 | 0 | 0 | 17 |
| new29 | pick_cool | win | win | 22/33 | 23 | 12 | 12 | 0 | 8 | 1 | 19 |
| new30 | pick_cool | - | - | 50/50 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new31 | pick_cool | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new32 | pick_cool | - | - | 50/50 | 11 | 2 | 2 | 0 | 0 | 0 | 45 |
| new33 | pick_heat | win | win | 12/12 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new34 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new35 | pick_heat | win | win | 8/8 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new36 | pick_heat | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
