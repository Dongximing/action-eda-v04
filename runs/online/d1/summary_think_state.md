# Online THINKING AGENT + FULL STATE + NAME CHECK vs baseline on 12 ALFWorld games

Wins: baseline 4/12, THINKING AGENT + FULL STATE + NAME CHECK 7/12. Rescued: game02, game04, game07, game10. Lost: game09.

Blocked 1 proposals; agent revised 0, kept its action 1; executed despite contradiction 1; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 1. Blocked proposals replayed in the env: would have run 1, would have failed 0; would have shown something new 1. Checks where no condition was written: 0.

Model-written place lists: 322 steps, not-visited list identical to the code list at 279; unusable answers 0; code-unvisited places the model left out 120, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: THINKING AGENT + FULL STATE + NAME CHECK)

| game | family | baseline | THINKING AGENT + FULL STATE + NAME CHECK | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/10 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game02 | pick_heat | - | win | 50/13 | 2 | 1 | 0 | 1 | 1 | 0 | 1 |
| game03 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game04 | pick_cool | - | win | 50/10 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game07 | pick_cool | - | win | 50/12 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/7 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game09 | pick_heat | win | - | 21/50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/10 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game11 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game12 | pick_cool | win | win | 12/10 | 1 | 0 | 0 | 0 | 0 | 0 | 9 |
