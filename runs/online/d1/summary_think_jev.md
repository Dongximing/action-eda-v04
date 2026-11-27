# Online THINKING AGENT + OUR MODULE vs baseline on 12 ALFWorld games

Wins: baseline 4/12, THINKING AGENT + OUR MODULE 8/12. Rescued: game04, game07, game10, game11. Lost: -.

Blocked 21 proposals; agent revised 18, kept its action 3; executed despite contradiction 3; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 21. Blocked proposals replayed in the env: would have run 1, would have failed 20; would have shown something new 1. Checks where no condition was written: 0.

Model-written place lists: 351 steps, not-visited list identical to the code list at 114; unusable answers 0; code-unvisited places the model left out 395, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: THINKING AGENT + OUR MODULE)

| game | family | baseline | THINKING AGENT + OUR MODULE | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/10 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game02 | pick_heat | - | - | 50/50 | 20 | 20 | 18 | 2 | 2 | 0 | 1 |
| game03 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game04 | pick_cool | - | win | 50/31 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game05 | pick_cool | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game07 | pick_cool | - | win | 50/17 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/17 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game09 | pick_heat | win | win | 21/16 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/35 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game11 | pick_clean | - | win | 50/15 | 2 | 1 | 0 | 1 | 1 | 0 | 2 |
| game12 | pick_cool | win | win | 12/10 | 1 | 0 | 0 | 0 | 0 | 0 | 9 |
