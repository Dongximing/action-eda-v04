# ReAct + dependency graph (react_dep_t1536) on the 9 games of the StateAct run

All 9 were lost by standard ReAct (react_std_t1536). Same model, prompt and settings; the controller is
scripts/dep_graph.py. Each run follows ReAct's path exactly (same cached answers) until the controller's first
message, then diverges. Reading by one annotator (Claude).

| game | ReAct | StateAct | react_dep | what the controller did | the win comes from |
|---|---|---|---|---|---|
| u047 clean cloth | lost | lost | won (20) | step 7: failure traced back to step 3, "handtowel 1 is the cloth" ruled out; step 12: take cloth while holding the handtowel not run; agent put the handtowel down (14), took cloth 1 (15) | the controller |
| u083 cool mug | lost | lost | won (34) | step 15: failure traced back to step 10, "cup 1 is the mug" ruled out; step 23: take while holding the cup not run; agent dropped the cup (28), took mug 1 (30) | the controller |
| u013 look at mug | lost | won | won (18) | step 17: lamp on but the task did not finish -> "needs you holding mug 1, step 16 you put it down"; agent took it (18) | the controller |
| u072 clean spatula | lost | lost | won (24) | step 22: put into drawer 1 from the sink failed -> "you are not at drawer 1"; agent went there (23) | the controller |
| u095 heat apple | lost | won | won (40) | step 1 location note (path changes); 23: stoveburner ruled out; 27: heat after putting the apple in the microwave not run ("you moved it in at step 26"); agent took it out (30); 32: stoveburner blocked; 34: toaster ruled out; microwave heat (38) | the controller (several times) |
| u115 hot tomato | lost | won | won (15) | step 1 location note (path changes); 6: heat before taking the tomato not run; 10: stoveburner ruled out -> microwave (13) | partly (path changed at step 1) |
| u102 hot cup | lost | lost | won (14) | step 1 location note (path changes, it takes cup 1 this time instead of a mug); 9: stoveburner ruled out -> microwave (12) | partly (the wrong object never happened) |
| u101 hot cup | lost | lost | won (19) | only the step 1 location note; afterwards it takes cup 2 and wins without help | not the controller: a different path after a small change |
| u097 heat apple | lost | won | won (9) | only the step 1 location note; then a direct win | not the controller |

Totals: ReAct 0/9, StateAct 4/9, react_dep 9/9. Wins with a clear chain from a controller decision: 5 (u047, u083,
u013, u072, u095); partly: 2 (u115, u102); after only a trivial early note: 2 (u101, u097).
Selection caveat: the 9 games were chosen because ReAct lost them, so any change can win some back (u101, u097).
Needed: a placebo arm with content-free notes at failures, and the full 134 games (does it hurt won games?).
