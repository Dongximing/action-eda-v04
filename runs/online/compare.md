# Online arms on 68 ALFWorld games

| arm | games | baseline wins | arm wins | rescued | lost | both won: steps base/arm | faster | slower | sign p (steps) | blocked | new actor requests | judge calls |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| D1 (per record, choice) | 68 | 25 | 26 | new15 | - | 350/317 (25 games) | 12 | 1 | 0.00342 | 70 | 449 | 2123 |
| H1 (whole history, choice) | 68 | 25 | 27 | new15, new19, new27 | new21 | 340/312 (24 games) | 13 | 2 | 0.00739 | 65 | 316 | 887 |
| LLM (whole history, reasoning) | 68 | 25 | 28 | new15, new19, new27 | - | 350/317 (25 games) | 14 | 1 | 0.000977 | 98 | 132 | 504 |
| LOOP (repeat block) | 35 | 13 | 13 | new15, new19 | game09, new08 | 126/109 (11 games) | 4 | 0 | 0.125 | 660 | 1546 | 0 |
| LLM + LOOP | 12 | 4 | 3 | - | game09 | 25/21 (3 games) | 2 | 0 | 0.5 | 264 | 231 | 21 |
| LOOP r3 | 12 | 4 | 3 | - | game09 | 25/23 (3 games) | 1 | 0 | 1 | 197 | 557 | 0 |
| EXPLORE (unvisited list) | 68 | 25 | 44 | game04, game07, game10, new04, new05, new09, new14, new15, new19, new27, new30, new31, new32, new39, new42, new44, new45, new49, new50, new52, new56 | new25, new37 | 332/254 (23 games) | 12 | 5 | 0.143 | 0 | 1910 | 0 |
| SELF-EXPLORE (model's list) | 68 | 25 | 42 | game04, game07, game10, new04, new05, new09, new10, new13, new14, new15, new27, new30, new31, new39, new44, new45, new49, new50, new52, new56 | new07, new25, new37 | 322/238 (22 games) | 12 | 3 | 0.0352 | 0 | 1124 | 2016 |
| ONE-CALL (lists + action, one call) | 68 | 25 | 21 | new04, new11, new38, new40, new53, new56 | game09, game12, new01, new07, new16, new17, new37, new41, new46, new47 | 184/201 (15 games) | 4 | 9 | 0.267 | 0 | 2384 | 0 |
| T0 (rule tracker) | 68 | 25 | 28 | new15, new19, new27 | - | 350/320 (25 games) | 12 | 2 | 0.0129 | 103 | 245 | 0 |
| failure hint | 68 | 25 | 24 | new15 | game09, new37 | 319/318 (23 games) | 4 | 6 | 0.754 | 0 | 1551 | 0 |
| MW (model-written + D1) | 12 | 4 | 4 | - | - | 46/44 (4 games) | 1 | 0 | 1 | 5 | 139 | 953 |
| MW-v2 (+ D1) | 12 | 4 | 3 | - | game09 | 25/23 (3 games) | 1 | 0 | 1 | 56 | 365 | 831 |

Missing: d1 0; h1 0; llm 0; loop 33; llmloop 56; loop_r3 56; explore 0; selfexplore 0; onecall 0; llmloop_r3 68; t0 0; hint 0; mw 56; mw_v2 56; mw_v2demo 68

## Games where any arm's result differs from the baseline

| game | family | baseline | D1 (per record, choice) | H1 (whole history, choice) | LLM (whole history, reasoning) | LOOP (repeat block) | LLM + LOOP | LOOP r3 | EXPLORE (unvisited list) | SELF-EXPLORE (model's list) | ONE-CALL (lists + action, one call) | LLM + LOOP r3 | T0 (rule tracker) | failure hint | MW (model-written + D1) | MW-v2 (+ D1) | MW-v2demo (+ D1) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| game01 | pick_heat | win 6 | win 6 | win 6 | win 6 | win 6 | win 6 | win 6 | win 27 | win 6 | win 7 | n/a | win 6 | win 6 | win 6 | win 6 | n/a |
| game04 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | win 15 | win 15 | - 50 | n/a | - 50 | - 50 | - 50 | - 50 | n/a |
| game07 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | win 25 | win 40 | - 50 | n/a | - 50 | - 50 | - 50 | - 50 | n/a |
| game08 | pick_clean | win 7 | win 6 | win 6 | win 6 | win 7 | win 6 | win 7 | win 7 | win 7 | win 11 | n/a | win 6 | win 8 | win 7 | win 7 | n/a |
| game09 | pick_heat | win 21 | win 21 | win 21 | win 21 | - 50 | - 50 | - 50 | win 15 | win 14 | - 50 | n/a | win 21 | - 50 | win 21 | - 50 | n/a |
| game10 | pick_clean | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | - 50 | win 49 | win 49 | - 50 | n/a | - 50 | - 50 | - 50 | - 50 | n/a |
| game12 | pick_cool | win 12 | win 9 | win 9 | win 9 | win 10 | win 9 | win 10 | win 9 | win 9 | - 50 | n/a | win 9 | win 11 | win 10 | win 10 | n/a |
| new01 | pick_clean | win 17 | win 11 | win 10 | win 10 | win 13 | n/a | n/a | win 8 | win 8 | - 50 | n/a | win 10 | win 19 | n/a | n/a | n/a |
| new03 | pick_clean | win 16 | win 15 | win 15 | win 15 | win 10 | n/a | n/a | win 12 | win 12 | win 18 | n/a | win 15 | win 17 | n/a | n/a | n/a |
| new04 | pick_clean | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | win 13 | win 13 | win 9 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new05 | pick_clean | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | win 10 | win 10 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new06 | pick_clean | win 9 | win 7 | win 7 | win 7 | win 9 | n/a | n/a | win 7 | win 7 | win 5 | n/a | win 7 | win 10 | n/a | n/a | n/a |
| new07 | pick_clean | win 10 | win 9 | win 6 | win 9 | win 10 | n/a | n/a | win 14 | - 50 | - 50 | n/a | win 9 | win 10 | n/a | n/a | n/a |
| new08 | pick_clean | win 41 | win 41 | win 41 | win 41 | - 50 | n/a | n/a | win 10 | win 10 | win 23 | n/a | win 41 | win 41 | n/a | n/a | n/a |
| new09 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | win 27 | win 44 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new10 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | - 50 | win 22 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new11 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | - 50 | - 50 | win 33 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new13 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | - 50 | win 40 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new14 | pick_cool | - 50 | - 50 | - 50 | - 50 | - 50 | n/a | n/a | win 12 | win 12 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new15 | pick_cool | - 50 | win 11 | win 11 | win 11 | win 19 | n/a | n/a | win 10 | win 10 | - 50 | n/a | win 11 | win 15 | n/a | n/a | n/a |
| new16 | pick_cool | win 17 | win 10 | win 7 | win 7 | win 12 | n/a | n/a | win 7 | win 7 | - 50 | n/a | win 7 | win 9 | n/a | n/a | n/a |
| new17 | pick_heat | win 15 | win 15 | win 15 | win 15 | win 15 | n/a | n/a | win 15 | win 15 | - 50 | n/a | win 15 | win 15 | n/a | n/a | n/a |
| new19 | pick_heat | - 50 | - 50 | win 9 | win 9 | win 13 | n/a | n/a | win 18 | - 50 | - 50 | n/a | win 9 | - 50 | n/a | n/a | n/a |
| new21 | pick_heat | win 10 | win 10 | - 50 | win 17 | win 10 | n/a | n/a | win 10 | win 10 | win 16 | n/a | win 17 | win 16 | n/a | n/a | n/a |
| new23 | pick_heat | win 7 | win 7 | win 7 | win 7 | win 7 | n/a | n/a | win 9 | win 9 | win 23 | n/a | win 7 | win 7 | n/a | n/a | n/a |
| new25 | pick_clean | win 8 | win 6 | win 6 | win 6 | n/a | n/a | n/a | - 50 | - 50 | win 14 | n/a | win 6 | win 7 | n/a | n/a | n/a |
| new27 | pick_clean | - 50 | - 50 | win 20 | win 21 | n/a | n/a | n/a | win 17 | win 17 | - 50 | n/a | win 21 | - 50 | n/a | n/a | n/a |
| new28 | pick_clean | win 19 | win 19 | win 18 | win 18 | n/a | n/a | n/a | win 14 | win 14 | win 19 | n/a | win 19 | win 20 | n/a | n/a | n/a |
| new29 | pick_cool | win 22 | win 19 | win 33 | win 19 | n/a | n/a | n/a | win 23 | win 41 | win 19 | n/a | win 19 | win 22 | n/a | n/a | n/a |
| new30 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 8 | win 9 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new31 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 9 | win 9 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new32 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 47 | - 50 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new33 | pick_heat | win 12 | win 12 | win 12 | win 12 | n/a | n/a | n/a | win 12 | win 12 | win 10 | n/a | win 12 | win 12 | n/a | n/a | n/a |
| new35 | pick_heat | win 8 | win 8 | win 8 | win 8 | n/a | n/a | n/a | win 8 | win 8 | win 9 | n/a | win 8 | win 8 | n/a | n/a | n/a |
| new37 | pick_clean | win 10 | win 11 | win 9 | win 9 | n/a | n/a | n/a | - 50 | - 50 | - 50 | n/a | win 11 | - 50 | n/a | n/a | n/a |
| new38 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | - 50 | - 50 | win 12 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new39 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 19 | win 19 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new40 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | - 50 | - 50 | win 20 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new41 | pick_clean | win 7 | win 6 | win 6 | win 6 | n/a | n/a | n/a | win 6 | win 6 | - 50 | n/a | win 6 | win 7 | n/a | n/a | n/a |
| new42 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 37 | - 50 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new44 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 36 | win 38 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new45 | pick_clean | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 7 | win 9 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new46 | pick_clean | win 35 | win 34 | win 34 | win 34 | n/a | n/a | n/a | win 14 | win 16 | - 50 | n/a | win 34 | win 35 | n/a | n/a | n/a |
| new47 | pick_clean | win 22 | win 16 | win 16 | win 16 | n/a | n/a | n/a | win 8 | win 8 | - 50 | n/a | win 16 | win 19 | n/a | n/a | n/a |
| new49 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 21 | win 36 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new50 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 13 | win 13 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new51 | pick_cool | win 8 | win 8 | win 9 | win 8 | n/a | n/a | n/a | win 7 | win 7 | win 13 | n/a | win 8 | win 8 | n/a | n/a | n/a |
| new52 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 32 | win 30 | - 50 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new53 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | - 50 | - 50 | win 42 | n/a | - 50 | - 50 | n/a | n/a | n/a |
| new54 | pick_cool | win 4 | win 4 | win 4 | win 4 | n/a | n/a | n/a | win 5 | win 5 | win 7 | n/a | win 4 | win 4 | n/a | n/a | n/a |
| new56 | pick_cool | - 50 | - 50 | - 50 | - 50 | n/a | n/a | n/a | win 31 | win 43 | win 24 | n/a | - 50 | - 50 | n/a | n/a | n/a |
