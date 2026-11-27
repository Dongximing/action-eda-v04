# What the agent blames after a failure (hand labels, one annotator, Claude, outcome known)

Lost games: the first 3 failures from the C1 origin e (the window where the game could still be saved). Won games: every failure from e until the premise was repaired. Each next thought labelled by its main stated cause.

| failures | n | the step just taken | environment / hidden rule | an earlier step | task already done |
|---|---|---|---|---|---|
| lost, all | 94 | 45 (48%) | 44 (47%) | 2 (2%) | 3 (3%) |
| lost, error really earlier (A/B) | 73 | 30 (41%) | 38 (52%) | 2 (3%) | 3 (4%) |
| lost, error really in this step (C) | 21 | 15 (71%) | 6 (29%) | 0 (0%) | 0 (0%) |
| won, until the repair | 27 | 10 (37%) | 9 (33%) | 8 (30%) | 0 (0%) |

In the 7 lost games where the error really was in the step just taken (acting on a place it had not gone to), none of the 21 thoughts says it is not at that place; they blame the target's state ("the fridge is open", "the cabinet is closed").

