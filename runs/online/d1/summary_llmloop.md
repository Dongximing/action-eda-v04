# Online LLM judge + LOOP vs baseline on 12 ALFWorld games

Wins: baseline 4/12, LLM judge + LOOP 3/12. Rescued: -. Lost: game09.

Blocked 264 proposals; agent revised 264, kept its action 0; executed despite contradiction 232; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 259. Blocked proposals replayed in the env: would have run 170, would have failed 94; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: LLM judge + LOOP)

| game | family | baseline | LLM judge + LOOP | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 3 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 39 | 32 | 32 | 0 | 27 | 0 | 5 |
| game03 | pick_clean | - | - | 50/50 | 5 | 3 | 3 | 0 | 2 | 0 | 7 |
| game04 | pick_cool | - | - | 50/50 | 34 | 28 | 28 | 0 | 22 | 0 | 11 |
| game05 | pick_cool | - | - | 50/50 | 45 | 41 | 41 | 0 | 38 | 0 | 9 |
| game06 | pick_heat | - | - | 50/50 | 42 | 39 | 39 | 0 | 35 | 0 | 8 |
| game07 | pick_cool | - | - | 50/50 | 32 | 26 | 26 | 0 | 26 | 0 | 25 |
| game08 | pick_clean | win | win | 7/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| game09 | pick_heat | win | - | 21/50 | 44 | 38 | 38 | 0 | 35 | 0 | 7 |
| game10 | pick_clean | - | - | 50/50 | 15 | 13 | 13 | 0 | 6 | 0 | 8 |
| game11 | pick_clean | - | - | 50/50 | 48 | 42 | 42 | 0 | 41 | 0 | 8 |
| game12 | pick_cool | win | win | 12/9 | 4 | 1 | 1 | 0 | 0 | 0 | 8 |
