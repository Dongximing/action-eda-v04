# Official StateAct on the games standard ReAct lost: first 9 of 35 (run stopped by hand)

Trial qwen35_9b_unseen_lost35; games third_party/stateact/alfworld_data_lost35 (games.json). Table of written vs real
state: stateact_state_qwen35_9b_unseen_lost35.md (scripts/stateact_state_check.py). Reading below by one annotator (Claude).

Won 4 of 9 (u013, u095, u097, u115); lost 5 (u047, u072, u083, u101, u102).

Written state (279 turns): inventory never wrong; location wrong in 11 turns (after a failed "go to"/"open" it wrote the
new place anyway). Commands that contradict the agent's own written state: 34, all in the 5 lost games, none in the 4 won
games (acting on a place other than its written location 28; heat/put with its written inventory None 6).

| game | task | what went wrong (first unrepaired error) | did its written state show it? |
|---|---|---|---|
| u047 | clean cloth | took handtowel 1 at step 2 (wrong object), as ReAct did | inventory "handtowel 1" is right; the state has no line comparing it with the task's cloth |
| u101 | hot cup in cabinet | took mug 1 at 14 (wrong object), heated it, put it in the cabinet, then "done" x10 | same: inventory right, no line for "is this the task's object" |
| u102 | hot cup in cabinet | took mug 2 at 3; put it in the microwave, then "heat" with an empty hand (x3); later the same with mug 3 and cup 2 | yes: it wrote "current inventory: None" right before each "heat" |
| u083 | cool mug, put in coffeemachine | put the mug in the fridge and closed it as if that cooled it; took it out, put it in the coffeemachine, "done" | no line for "cooled or not" |
| u072 | clean spatula | never visited countertop 3, where the spatula was (ReAct found it there) | "locations visited" listed the places, it still did not go there |
