# Tokens per arm on 12 games (runs/online/d1)

Every call counted as if made fresh (cache hits at the size of the original request). Ratios are against baseline.

| arm | wins | steps | 9B requests | 9B input tokens | 9B output tokens | 9B tokens vs baseline | 9B cost (USD) | decision-model requests | decision-model input tokens | failed requests (counted) | calls with no token record |
|---|---|---|---|---|---|---|---|---|---|---|---|
| baseline | 4 | 446 | 446 | 925,798 | 4,574 | 1.00x | 0.0937 | 0 | 0 | 0 | 0 |
| selfexplore | 7 | 390 | 780 | 1,372,222 | 121,868 | 1.61x | 0.1677 | 0 | 0 | 0 | 0 |
| jevexplore | 8 | 389 | 401 | 894,879 | 7,967 | 0.97x | 0.0915 | 377 | 229,824 | 0 | 0 |

## Per operation (all games)

| arm | operation | requests | input tokens | output tokens |
|---|---|---|---|---|
| baseline | actor | 446 | 925,798 | 4,574 |
| selfexplore | actor | 390 | 930,615 | 4,398 |
| selfexplore | judge-places | 390 | 441,607 | 117,470 |
| jevexplore | actor | 389 | 890,602 | 4,420 |
| jevexplore | judge-jev-arrived | 377 | 229,824 | 0 |
| jevexplore | judge-places | 12 | 4,277 | 3,547 |

## Per game

| game | baseline (win, steps, 9B tokens) | selfexplore (win, steps, 9B tokens) | jevexplore (win, steps, 9B tokens) |
|---|---|---|---|
| d1/game01 | win 6 8,266 | win 6 13,839 | win 33 63,922 |
| d1/game02 | - 50 123,784 | - 50 171,156 | - 50 111,926 |
| d1/game03 | - 50 112,454 | - 50 234,541 | win 37 98,092 |
| d1/game04 | - 50 97,804 | win 15 40,263 | win 15 27,425 |
| d1/game05 | - 50 111,517 | - 50 213,783 | - 50 126,660 |
| d1/game06 | - 50 105,354 | - 50 180,331 | - 50 115,209 |
| d1/game07 | - 50 103,809 | win 40 155,479 | win 25 49,030 |
| d1/game08 | win 7 10,204 | win 7 16,516 | win 7 12,467 |
| d1/game09 | win 21 32,646 | win 14 36,118 | win 14 26,344 |
| d1/game10 | - 50 113,375 | win 49 248,495 | win 49 150,367 |
| d1/game11 | - 50 94,608 | - 50 161,288 | - 50 105,507 |
| d1/game12 | win 12 16,551 | win 9 22,281 | win 9 15,897 |
