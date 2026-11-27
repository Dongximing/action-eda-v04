# Online JEV-EXPLORE + NAME CHECK (hard block) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, JEV-EXPLORE + NAME CHECK (hard block) 8/12. Rescued: game03, game04, game07, game10. Lost: -.

Blocked 13 proposals; agent revised 3, kept its action 10; executed despite contradiction 10; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 13. Blocked proposals replayed in the env: would have run 13, would have failed 0; would have shown something new 13. Checks where no condition was written: 0.

Model-written place lists: 389 steps, not-visited list identical to the code list at 307; unusable answers 0; code-unvisited places the model left out 148, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: JEV-EXPLORE + NAME CHECK (hard block))

| game | family | baseline | JEV-EXPLORE + NAME CHECK (hard block) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/33 | 1 | 0 | 0 | 0 | 0 | 0 | 6 |
| game02 | pick_heat | - | - | 50/50 | 8 | 8 | 1 | 7 | 7 | 0 | 1 |
| game03 | pick_clean | - | win | 50/37 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game04 | pick_cool | - | win | 50/15 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game06 | pick_heat | - | - | 50/50 | 1 | 1 | 1 | 0 | 0 | 0 | 1 |
| game07 | pick_cool | - | win | 50/25 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/7 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | win | 21/14 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/49 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game11 | pick_clean | - | - | 50/50 | 4 | 4 | 1 | 3 | 3 | 0 | 2 |
| game12 | pick_cool | win | win | 12/9 | 1 | 0 | 0 | 0 | 0 | 0 | 8 |
