# Online LLM judge (whole history, free reasoning) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, LLM judge (whole history, free reasoning) 4/12. Rescued: -. Lost: -.

Blocked 11 proposals; agent revised 11, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 4; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 11. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: LLM judge (whole history, free reasoning))

| game | family | baseline | LLM judge (whole history, free reasoning) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 3 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| game03 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game04 | pick_cool | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| game05 | pick_cool | - | - | 50/50 | 19 | 0 | 0 | 0 | 0 | 0 | - |
| game06 | pick_heat | - | - | 50/50 | 4 | 1 | 1 | 0 | 0 | 0 | 8 |
| game07 | pick_cool | - | - | 50/50 | 9 | 1 | 1 | 0 | 0 | 0 | 50 |
| game08 | pick_clean | win | win | 7/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| game09 | pick_heat | win | win | 21/21 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| game10 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| game11 | pick_clean | - | - | 50/50 | 39 | 6 | 6 | 0 | 0 | 4 | 8 |
| game12 | pick_cool | win | win | 12/9 | 4 | 1 | 1 | 0 | 0 | 0 | 8 |
