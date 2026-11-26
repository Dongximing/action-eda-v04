# Online ONE-CALL (agent lists places, then acts, same call) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, ONE-CALL (agent lists places, then acts, same call) 2/12. Rescued: -. Lost: game09, game12.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 518 steps, not-visited list identical to the code list at 242; unusable answers 2; code-unvisited places the model left out 684, places it listed that the code does not 53.

(per-game keys d1_won / d1_steps hold this arm's result: ONE-CALL (agent lists places, then acts, same call))

| game | family | baseline | ONE-CALL (agent lists places, then acts, same call) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/7 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| game02 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game03 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game04 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game07 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game08 | pick_clean | win | win | 7/11 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game09 | pick_heat | win | - | 21/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 5 |
| game11 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game12 | pick_cool | win | - | 12/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
