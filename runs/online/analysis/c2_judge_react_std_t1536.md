# C2 / E3: judge model (OneJev1.6-4B, local) on react_std_t1536

Scored games: 5 lost with a stuck window (5 with e before the loop), 21 won. Alarm at step t when the score >= threshold. Score: P(yes) of `mistake`, or 1 - P(yes) of `on_track`.

| score | threshold | caught in [e, t_L) (early games) | first alarm before e (lost) | won games with an alarm | alarms per step, won | lead t_L-d (median) |
|---|---|---|---|---|---|---|
| mistake | 0.3 | 5/5 (100%) | 5/5 | 17/21 (81%) | 0.852 | 2 |
| mistake | 0.5 | 4/5 (80%) | 5/5 | 14/21 (67%) | 0.430 | 2.5 |
| mistake | 0.7 | 1/5 (20%) | 1/5 | 2/21 (10%) | 0.035 | 14 |
| mistake | 0.8 | 0/5 (0%) | 1/5 | 0/21 (0%) | 0.000 | - |
| mistake | 0.9 | 0/5 (0%) | 0/5 | 0/21 (0%) | 0.000 | - |
| mistake | 0.95 | 0/5 (0%) | 0/5 | 0/21 (0%) | 0.000 | - |
| not on_track | 0.3 | 5/5 (100%) | 5/5 | 17/21 (81%) | 0.812 | 2 |
| not on_track | 0.5 | 4/5 (80%) | 5/5 | 17/21 (81%) | 0.676 | 2.5 |
| not on_track | 0.7 | 3/5 (60%) | 5/5 | 14/21 (67%) | 0.438 | 2 |
| not on_track | 0.8 | 2/5 (40%) | 5/5 | 9/21 (43%) | 0.289 | 9.0 |
| not on_track | 0.9 | 0/5 (0%) | 2/5 | 4/21 (19%) | 0.066 | - |
| not on_track | 0.95 | 0/5 (0%) | 1/5 | 2/21 (10%) | 0.008 | - |

`mistake`: mean score at the error step e 0.524 (n 5), at steps of won games 0.460 (n 256); AUC (error step vs won-game step) 0.644

`not on_track`: mean score at the error step e 0.584 (n 5), at steps of won games 0.604 (n 256); AUC (error step vs won-game step) 0.449
