# Online LOOP, up to 3 revisions vs baseline on 12 ALFWorld games

Wins: baseline 4/12, LOOP, up to 3 revisions 3/12. Rescued: -. Lost: game09.

Blocked 197 proposals; agent revised 197, kept its action 0; executed despite contradiction 99; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 197. Blocked proposals replayed in the env: would have run 126, would have failed 71; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: LOOP, up to 3 revisions)

| game | family | baseline | LOOP, up to 3 revisions | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 17 | 17 | 17 | 0 | 4 | 0 | 14 |
| game03 | pick_clean | - | - | 50/50 | 7 | 7 | 7 | 0 | 5 | 0 | 7 |
| game04 | pick_cool | - | - | 50/50 | 26 | 26 | 26 | 0 | 17 | 0 | 11 |
| game05 | pick_cool | - | - | 50/50 | 41 | 41 | 41 | 0 | 38 | 0 | 9 |
| game06 | pick_heat | - | - | 50/50 | 26 | 26 | 26 | 0 | 4 | 0 | 10 |
| game07 | pick_cool | - | - | 50/50 | 8 | 8 | 8 | 0 | 2 | 0 | 25 |
| game08 | pick_clean | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | - | 21/50 | 25 | 25 | 25 | 0 | 3 | 0 | 7 |
| game10 | pick_clean | - | - | 50/50 | 17 | 17 | 17 | 0 | 4 | 0 | 8 |
| game11 | pick_clean | - | - | 50/50 | 29 | 29 | 29 | 0 | 22 | 0 | 9 |
| game12 | pick_cool | win | win | 12/10 | 1 | 1 | 1 | 0 | 0 | 0 | 9 |
