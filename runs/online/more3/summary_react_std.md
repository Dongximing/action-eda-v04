# Online REACT (standard: VBL/ReflAct/MPO) vs baseline on 20 ALFWorld games

Wins: baseline 6/20, REACT (standard: VBL/ReflAct/MPO) 15/20. Rescued: new39, new40, new43, new44, new45, new48, new50, new52, new53, new55. Lost: new37.

Blocked 0 proposals; agent revised 0, kept its action 0; executed despite contradiction 0; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 0; would have shown something new 0. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: REACT (standard: VBL/ReflAct/MPO))

| game | family | baseline | REACT (standard: VBL/ReflAct/MPO) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new37 | pick_clean | win | - | 10/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new38 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new39 | pick_clean | - | win | 50/13 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new40 | pick_clean | - | win | 50/17 | 0 | 0 | 0 | 0 | 0 | 0 | 2 |
| new41 | pick_clean | win | win | 7/9 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new42 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new43 | pick_clean | - | win | 50/35 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new44 | pick_clean | - | win | 50/17 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new45 | pick_clean | - | win | 50/7 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new46 | pick_clean | win | win | 35/16 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new47 | pick_clean | win | win | 22/8 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new48 | pick_cool | - | win | 50/25 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new49 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new50 | pick_cool | - | win | 50/34 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new51 | pick_cool | win | win | 8/19 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new52 | pick_cool | - | win | 50/13 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new53 | pick_cool | - | win | 50/32 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |
| new54 | pick_cool | win | win | 4/5 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| new55 | pick_cool | - | win | 50/10 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
| new56 | pick_cool | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | 3 |
