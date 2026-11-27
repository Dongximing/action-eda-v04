# StateAct (qwen35_9b_unseen_lost35): written state vs the state in the feedback

| game | type | result | steps | early stop | location wrong | inventory wrong | acts away from its written location | transform/put with written inventory None |
|---|---|---|---|---|---|---|---|---|
| u115 | heat | won | 9 | - | 0 | 0 | 0 | 0 |
| u047 | clean | lost | 49 | ENV_ERROR: Too many (5) consecutive repetitions. | 2 | 0 | 17 | 0 |
| u095 | heat | won | 27 | - | 0 | 0 | 0 | 0 |
| u083 | cool | lost | 34 | ENV_ERROR: Too many (5) consecutive repetitions. | 0 | 0 | 2 | 1 |
| u013 | look_at_obj_in_light | won | 15 | - | 2 | 0 | 0 | 0 |
| u102 | heat | lost | 50 | - | 0 | 0 | 4 | 5 |
| u097 | heat | won | 8 | - | 0 | 0 | 0 | 0 |
| u101 | heat | lost | 42 | ENV_ERROR: Too many (5) consecutive repetitions. | 5 | 0 | 5 | 0 |
| u072 | clean | lost | 45 | - | 2 | 0 | 0 | 0 |

All finished games: 279 turns; written location wrong 11, written inventory wrong 0, acts away from its own written location 28, transform/put with its own written inventory None 6.
