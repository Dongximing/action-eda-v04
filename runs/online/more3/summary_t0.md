# Online T0 (rule tracker) vs baseline on 20 ALFWorld games

Wins: baseline 6/20, T0 (rule tracker) 6/20. Rescued: -. Lost: -.

Blocked 37 proposals; agent revised 32, kept its action 5; executed despite contradiction 26; blocks the tracker calls wrong: 0; hints shown 0.

(per-game keys d1_won / d1_steps hold this arm's result: T0 (rule tracker))

| game | family | baseline | T0 (rule tracker) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
|---|---|---|---|---|---|---|---|---|---|---|---|
| new37 | pick_clean | win | win | 10/11 | 7 | 3 | 3 | 0 | 2 | 0 | 8 |
| new38 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| new39 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new40 | pick_clean | - | - | 50/50 | 10 | 2 | 1 | 1 | 2 | 0 | 50 |
| new41 | pick_clean | win | win | 7/6 | 4 | 1 | 1 | 0 | 0 | 0 | 5 |
| new42 | pick_clean | - | - | 50/50 | 0 | 0 | 0 | 0 | 0 | 0 | - |
| new43 | pick_clean | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
| new44 | pick_clean | - | - | 50/50 | 6 | 0 | 0 | 0 | 0 | 0 | - |
| new45 | pick_clean | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new46 | pick_clean | win | win | 35/34 | 9 | 1 | 1 | 0 | 0 | 0 | 33 |
| new47 | pick_clean | win | win | 22/16 | 5 | 1 | 1 | 0 | 0 | 0 | 15 |
| new48 | pick_cool | - | - | 50/50 | 5 | 0 | 0 | 0 | 0 | 0 | - |
| new49 | pick_cool | - | - | 50/50 | 8 | 0 | 0 | 0 | 0 | 0 | - |
| new50 | pick_cool | - | - | 50/50 | 10 | 1 | 1 | 0 | 0 | 0 | 16 |
| new51 | pick_cool | win | win | 8/8 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new52 | pick_cool | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new53 | pick_cool | - | - | 50/50 | 37 | 24 | 24 | 0 | 18 | 0 | 24 |
| new54 | pick_cool | win | win | 4/4 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new55 | pick_cool | - | - | 50/50 | 9 | 4 | 0 | 4 | 4 | 0 | - |
| new56 | pick_cool | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
