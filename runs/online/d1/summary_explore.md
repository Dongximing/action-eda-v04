# Online EXPLORE (unvisited places shown) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, EXPLORE (unvisited places shown) 7/12. Rescued: game04, game07, game10. Lost: -.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: EXPLORE (unvisited places shown))

| game | family | baseline | EXPLORE (unvisited places shown) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/27 | 0 | 0 | 0 | 0 | 0 | 0 | 6 |
| game02 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game03 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game04 | pick_cool | - | win | 50/15 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game07 | pick_cool | - | win | 50/25 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | win | 21/15 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/49 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game11 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game12 | pick_cool | win | win | 12/9 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |
