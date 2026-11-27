# Online JEV-EXPLORE (decision model keeps the places) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, JEV-EXPLORE (decision model keeps the places) 8/12. Rescued: game03, game04, game07, game10. Lost: -.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 389 steps, not-visited list identical to the code list at 276; unusable answers 0; code-unvisited places the model left out 206, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: JEV-EXPLORE (decision model keeps the places))

| game | family | baseline | JEV-EXPLORE (decision model keeps the places) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/33 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| game02 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game03 | pick_clean | - | win | 50/37 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game04 | pick_cool | - | win | 50/15 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game07 | pick_cool | - | win | 50/25 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | win | 21/14 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/49 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game11 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game12 | pick_cool | win | win | 12/9 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
