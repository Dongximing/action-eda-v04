# Online LLM judge (whole history, free reasoning) vs baseline on 20 ALFWorld games

Wins: baseline 6/20, LLM judge (whole history, free reasoning) 6/20. Rescued: -. Lost: -.

Blocked 15 proposals; agent revised 12, kept its action 3; executed despite contradiction 7; blocks the tracker calls wrong: 0; hints shown 0.

Blocks the tracker cannot score (free-text conditions only): 0. Blocked proposals replayed in the env: would have run 0, would have failed 15. Checks where no condition was written: 0.

(per-game keys d1_won / d1_steps hold this arm's result: LLM judge (whole history, free reasoning))

| game | family | baseline | LLM judge (whole history, free reasoning) | steps b/arm | checks | blocked | revised | kept | despite | false blocks | diverged at |
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
| new49 | pick_cool | - | - | 50/50 | 8 | 0 | 0 | 0 | 0 | 0 | - |
| new50 | pick_cool | - | - | 50/50 | 10 | 1 | 1 | 0 | 0 | 0 | 16 |
| new51 | pick_cool | win | win | 8/8 | 4 | 0 | 0 | 0 | 0 | 0 | - |
| new52 | pick_cool | - | - | 50/50 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new53 | pick_cool | - | - | 50/50 | 25 | 6 | 6 | 0 | 4 | 0 | 24 |
| new54 | pick_cool | win | win | 4/4 | 2 | 0 | 0 | 0 | 0 | 0 | - |
| new55 | pick_cool | - | - | 50/50 | 9 | 3 | 0 | 3 | 3 | 0 | - |
| new56 | pick_cool | - | - | 50/50 | 1 | 0 | 0 | 0 | 0 | 0 | - |
