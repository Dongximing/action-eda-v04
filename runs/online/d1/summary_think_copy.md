# Online COPY STATE + THINK + NAME CHECK vs baseline on 12 ALFWorld games

Wins: baseline 4/12, COPY STATE + THINK + NAME CHECK 7/12. Rescued: game03, game04, game07, game10, game11. Lost: game08, game09.

Blocked 84 proposals; agent revised 81, kept its action 3; executed despite contradiction 3; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 84. Blocked proposals replayed in the env: would have run 84, would have failed 0; would have shown something new 84. Checks where no condition was written: 0.

Model-written place lists: 380 steps, not-visited list identical to the code list at 380; unusable answers 0; code-unvisited places the model left out 0, places it listed that the code does not 0.

(per-game keys d1_won / d1_steps hold this arm's result: COPY STATE + THINK + NAME CHECK)

| game | family | baseline | COPY STATE + THINK + NAME CHECK | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/7 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game02 | pick_heat | - | - | 50/50 | 42 | 42 | 41 | 1 | 1 | 0 | 1 |
| game03 | pick_clean | - | win | 50/8 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game04 | pick_cool | - | win | 50/11 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 7 | 7 | 7 | 0 | 0 | 0 | 1 |
| game06 | pick_heat | - | - | 50/50 | 31 | 31 | 31 | 0 | 0 | 0 | 2 |
| game07 | pick_cool | - | win | 50/37 | 1 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | - | 7/50 | 2 | 0 | 0 | 0 | 0 | 0 | 1 |
| game09 | pick_heat | win | - | 21/50 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/39 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| game11 | pick_clean | - | win | 50/19 | 6 | 4 | 2 | 2 | 2 | 0 | 2 |
| game12 | pick_cool | win | win | 12/9 | 1 | 0 | 0 | 0 | 0 | 0 | 8 |
