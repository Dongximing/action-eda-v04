# Online LOOP (block repeats with no new observation) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, LOOP (block repeats with no new observation) 3/12. Rescued: -. Lost: game09.

Blocked 251 proposals; agent revised 251, kept its action 0; executed despite contradiction 219; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 251. Blocked proposals replayed in the env: would have run 173, would have failed 78; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: LOOP (block repeats with no new observation))

| game | family | baseline | LOOP (block repeats with no new observation) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | win | 6/6 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game02 | pick_heat | - | - | 50/50 | 30 | 30 | 30 | 0 | 28 | 0 | 14 |
| game03 | pick_clean | - | - | 50/50 | 3 | 3 | 3 | 0 | 2 | 0 | 7 |
| game04 | pick_cool | - | - | 50/50 | 28 | 28 | 28 | 0 | 21 | 0 | 11 |
| game05 | pick_cool | - | - | 50/50 | 41 | 41 | 41 | 0 | 38 | 0 | 9 |
| game06 | pick_heat | - | - | 50/50 | 36 | 36 | 36 | 0 | 34 | 0 | 10 |
| game07 | pick_cool | - | - | 50/50 | 26 | 26 | 26 | 0 | 25 | 0 | 25 |
| game08 | pick_clean | win | win | 7/7 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| game09 | pick_heat | win | - | 21/50 | 38 | 38 | 38 | 0 | 35 | 0 | 7 |
| game10 | pick_clean | - | - | 50/50 | 13 | 13 | 13 | 0 | 6 | 0 | 8 |
| game11 | pick_clean | - | - | 50/50 | 35 | 35 | 35 | 0 | 30 | 0 | 9 |
| game12 | pick_cool | win | win | 12/10 | 1 | 1 | 1 | 0 | 0 | 0 | 9 |
