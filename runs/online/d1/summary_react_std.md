# Online REACT (standard: VBL/ReflAct/MPO) vs baseline on 12 ALFWorld games

Wins: baseline 4/12, REACT (standard: VBL/ReflAct/MPO) 6/12. Rescued: game03, game04, game07, game10. Lost: game01, game09.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: REACT (standard: VBL/ReflAct/MPO))

| game | family | baseline | REACT (standard: VBL/ReflAct/MPO) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win | - | 6/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game02 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game03 | pick_clean | - | win | 50/34 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game04 | pick_cool | - | win | 50/12 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game05 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game06 | pick_heat | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game07 | pick_cool | - | win | 50/41 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game08 | pick_clean | win | win | 7/27 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game09 | pick_heat | win | - | 21/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game10 | pick_clean | - | win | 50/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| game11 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| game12 | pick_cool | win | win | 12/10 | 0 | 0 | 0 | 0 | 0 | 0 | 7 |
