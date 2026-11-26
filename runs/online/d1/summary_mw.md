# Online MW (model-written conditions + D1) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, MW (model-written conditions + D1) 4/12. Rescued: -. Lost: -.

Blocked 5 proposals; agent revised 4, kept its action 1; executed despite contradiction 1; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 5. Blocked proposals replayed in the env: would have run 0, would have failed 5. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: MW (model-written conditions + D1))

| game | family | baseline | MW (model-written conditions + D1) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 3 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 16 | 2 | 2 | 0 | 0 | 0 | 18 |
| game03 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game04 | pick_cool | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| game05 | pick_cool | - | - | 50/50 | 19 | 0 | 0 | 0 | 0 | 0 | - |
| game06 | pick_heat | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| game07 | pick_cool | - | - | 50/50 | 9 | 1 | 1 | 0 | 0 | 0 | 50 |
| game08 | pick_clean | win | win | 7/7 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | win | 21/21 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| game10 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game11 | pick_clean | - | - | 50/50 | 25 | 1 | 0 | 1 | 1 | 0 | - |
| game12 | pick_cool | win | win | 12/10 | 5 | 1 | 1 | 0 | 0 | 0 | 9 |
