# Online MW-v2 (precondition writer + D1) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, MW-v2 (precondition writer + D1) 3/12. Rescued: -. Lost: game09.

Blocked 56 proposals; agent revised 28, kept its action 28; executed despite contradiction 35; blocks the tracker calls wrong: 17; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 5. Blocked proposals replayed in the env: would have run 12, would have failed 44. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: MW-v2 (precondition writer + D1))

| game | family | baseline | MW-v2 (precondition writer + D1) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 3 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 14 | 9 | 5 | 4 | 4 | 6 | 15 |
| game03 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game04 | pick_cool | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| game05 | pick_cool | - | - | 50/50 | 19 | 0 | 0 | 0 | 0 | 0 | - |
| game06 | pick_heat | - | - | 50/50 | 4 | 4 | 2 | 2 | 2 | 0 | 2 |
| game07 | pick_cool | - | - | 50/50 | 9 | 2 | 1 | 1 | 2 | 1 | 49 |
| game08 | pick_clean | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | - | 21/50 | 35 | 28 | 10 | 18 | 20 | 1 | 18 |
| game10 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game11 | pick_clean | - | - | 50/50 | 34 | 10 | 8 | 2 | 6 | 8 | 8 |
| game12 | pick_cool | win | win | 12/10 | 5 | 3 | 2 | 1 | 1 | 1 | 7 |
