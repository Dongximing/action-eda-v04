# Online H1 (whole history, multiple choice) vs baseline on 20 ALFWorld games

Wins: baseline 6/20, H1 (whole history, multiple choice) 6/20. Rescued: -. Lost: -.

Blocked 10 proposals; agent revised 9, kept its action 1; executed despite contradiction 1; blocks the tracker calls wrong: 2; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 2, would have failed 8. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: H1 (whole history, multiple choice))

| game | family | baseline | H1 (whole history, multiple choice) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new37 | pick_clean | win | win | 10/9 | 5 | 1 | 1 | 0 | 0 | 0 | 8 |
| new38 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| new39 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new40 | pick_clean | - | - | 50/50 | 8 | 1 | 1 | 0 | 0 | 0 | 43 |
| new41 | pick_clean | win | win | 7/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| new42 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new43 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| new44 | pick_clean | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| new45 | pick_clean | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new46 | pick_clean | win | win | 35/34 | 9 | 1 | 1 | 0 | 0 | 0 | 33 |
| new47 | pick_clean | win | win | 22/16 | 5 | 1 | 1 | 0 | 0 | 0 | 15 |
| new48 | pick_cool | - | - | 50/50 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new49 | pick_cool | - | - | 50/50 | 8 | 1 | 0 | 1 | 1 | 1 | - |
| new50 | pick_cool | - | - | 50/50 | 9 | 0 | 0 | 0 | 0 | 0 | - |
| new51 | pick_cool | win | win | 8/9 | 5 | 1 | 1 | 0 | 0 | 1 | 8 |
| new52 | pick_cool | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new53 | pick_cool | - | - | 50/50 | 26 | 3 | 3 | 0 | 0 | 0 | 30 |
| new54 | pick_cool | win | win | 4/4 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new55 | pick_cool | - | - | 50/50 | 9 | 0 | 0 | 0 | 0 | 0 | - |
| new56 | pick_cool | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
