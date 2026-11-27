# Online REACT (standard: VBL/ReflAct/MPO) vs baseline on 12 ALFWorld games

Wins: baseline 6/12, REACT (standard: VBL/ReflAct/MPO) 10/12. Rescued: new27, new30, new31, new32, new34. Lost: new33.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: REACT (standard: VBL/ReflAct/MPO))

| game | family | baseline | REACT (standard: VBL/ReflAct/MPO) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new25 | pick_clean | win | win | 8/30 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new26 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new27 | pick_clean | - | win | 50/19 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new28 | pick_clean | win | win | 19/34 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new29 | pick_cool | win | win | 22/45 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new30 | pick_cool | - | win | 50/9 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new31 | pick_cool | - | win | 50/44 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new32 | pick_cool | - | win | 50/35 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new33 | pick_heat | win | - | 12/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new34 | pick_heat | - | win | 50/11 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new35 | pick_heat | win | win | 8/10 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new36 | pick_heat | win | win | 7/20 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
