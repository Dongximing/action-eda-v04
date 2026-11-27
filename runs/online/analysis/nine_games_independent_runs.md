# 9 games, independent runs (no reused answers), qwen3.5-9b, valid_unseen, 50 steps

The 9 games are those of the first official StateAct run on the 35 games standard ReAct lost once (selected by
that loss). ReAct and ours: runs/online/{fresh,run2}_{react_std,react_dep_graph}/ (each in its own folder, every
answer fresh). StateAct: official code (no answer cache), trials qwen35_9b_unseen_lost35, qwen35_9b_9games_run2,
qwen35_9b_9games_run3; games matched to our ids by the trace's room, task and receptacle contents
(runs/online/analysis/stateact_9games_results.json). StateAct's own code ends a game after 5 identical actions in a row.

| game | ReAct 1 | ReAct 2 | StateAct 1 | StateAct 2 | StateAct 3 | ours 1 | ours 2 |
|---|---|---|---|---|---|---|---|
| u013 look at mug | won | won | won | won | won | won | won |
| u047 clean cloth | lost | lost | lost | lost | lost | won | won |
| u072 clean spatula | won | lost | lost | won | won | won | won |
| u083 cool mug | lost | lost | lost | lost | lost | won | won |
| u095 heat apple | won | lost | won | won | won | won | won |
| u097 heat apple | won | won | won | won | won | won | won |
| u101 hot cup | won | lost | lost | lost | lost | won | won |
| u102 hot cup | lost | lost | lost | lost | lost | won | won |
| u115 hot tomato | lost | won | won | won | won | won | won |
| total | 5/9 | 3/9 | 4/9 | 5/9 | 5/9 | 9/9 | 9/9 |

All runs: ReAct 8/18 (44%), StateAct 14/27 (52%), ours 18/18 (100%).
Per game, ours vs ReAct: better in 7, equal in 2, worse in 0 (sign test p = 0.016).
Per game, ours vs StateAct: better in 5, equal in 4, worse in 0 (sign test p = 0.0625).
Caveats: 9 games, chosen because ReAct lost them once; the full 134 games and the control arms are not run yet.
