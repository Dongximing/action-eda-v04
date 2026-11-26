# Online ONE-CALL (agent lists places, then acts, same call) vs baseline on 20 ALFWorld games

Wins: baseline 6/20, ONE-CALL (agent lists places, then acts, same call) 6/20. Rescued: new38, new40, new53, new56. Lost: new37, new41, new46, new47.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

Model-written place lists: 818 steps, not-visited list identical to the code list at 665; unusable answers 0; code-unvisited places the model left out 460, places it listed that the code does not 46.

(per-game keys d1_won / d1_steps hold this arm's result: ONE-CALL (agent lists places, then acts, same call))

| game | family | baseline | ONE-CALL (agent lists places, then acts, same call) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new37 | pick_clean | win | - | 10/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new38 | pick_clean | - | win | 50/12 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new39 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new40 | pick_clean | - | win | 50/20 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new41 | pick_clean | win | - | 7/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new42 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new43 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new44 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new45 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new46 | pick_clean | win | - | 35/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new47 | pick_clean | win | - | 22/50 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new48 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new49 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new50 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new51 | pick_cool | win | win | 8/13 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new52 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new53 | pick_cool | - | win | 50/42 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new54 | pick_cool | win | win | 4/7 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new55 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new56 | pick_cool | - | win | 50/24 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
