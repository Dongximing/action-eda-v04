# C1 audit: lost games of standard ReAct (1536 tokens), valid_unseen 134

One annotator (Claude), reading each trajectory; the design's second annotator and Cohen's kappa are still to do.

- lost: 35; with a stuck window (w = 5): 34
- A, an earlier error of a different kind causes the loop: 25 / 34
- B, the same error, first shown before the window: 2 / 34
- C, the error starts at the loop: 7 / 34
- steps from e to the loop (A and B): median 7, range 2-33
- the rule (analyze_loops) agrees on earlier-origin yes/no in 31 / 34 games

| kind of e | A | B | C |
|---|---|---|---|
| failure misexplained | 1 | 0 | 0 |
| kept carrying | 4 | 0 | 0 |
| put down early | 10 | 0 | 0 |
| skipped navigation | 0 | 2 | 7 |
| skipped pickup | 1 | 0 | 0 |
| wrong object | 9 | 0 | 0 |

| game | task | e | t_L | kind | error | note | first symptom | rule origin |
|---|---|---|---|---|---|---|---|---|
| u007 | look at bowl under the desklamp. | 7 | 9 | A | put down early | put the bowl down next to the lamp instead of holding it while using the lamp | 7 | 7 (task object put down early) |
| u008 | look at bowl under the desklamp. | 8 | 10 | A | put down early | put the bowl on the shelf with the lamp instead of holding it | 8 | 8 (task object put down early) |
| u013 | look at mug under the desklamp. | 16 | 18 | A | put down early | put the mug on the desk with the lamp instead of holding it | 16 | 16 (task object put down early) |
| u025 | put some peppershaker on drawer. | 19 | 22 | A | skipped pickup | saw peppershaker 1 on countertop 3 (step 18) and walked to the drawer without taking it | 20 | 20 (earlier failed command) |
| u030 | put some saltshaker on cabinet. | 13 | 13 | C | skipped navigation | move saltshaker 1 to cabinet 1 while at drawer 1 | 13 | - (failures with no earlier origin) |
| u033 | put some saltshaker on drawer. | 24 | 28 | B | skipped navigation | move saltshaker 1 to drawer 1 while at countertop 3 (repeated in the window) | 24 | 20 (earlier failed command) |
| u042 | put some watch on safe. | 37 | 42 | A | wrong object | took box 2 while searching for the watch; hands full when the watch is found | 42 | 37 (wrong object taken) |
| u043 | clean some bowl and put it in cabinet. | 18 | 18 | C | skipped navigation | move bowl 1 to cabinet 1 while at the sink | 18 | - (failures with no earlier origin) |
| u046 | clean some cloth and put it in cabinet. | 4 | 22 | A | wrong object | took towel 1; the task is cloth | 4 | 4 (wrong object taken) |
| u047 | clean some cloth and put it in cabinet. | 3 | 14 | A | wrong object | took handtowel 1; the task is cloth | 3 | 3 (wrong object taken) |
| u049 | clean some cloth and put it in countertop. | 2 | 22 | A | wrong object | took handtowel 1; the task is cloth | 2 | 2 (wrong object taken) |
| u055 | put a clean knife in countertop. | 20 | 29 | A | wrong object | took butterknife 1; the task is knife | 20 | 20 (wrong object taken) |
| u056 | put a clean mug in coffeemachine. | 15 | 22 | A | put down early | put the mug in the coffeemachine (goal) before cleaning it | 15 | 15 (put the object down) |
| u072 | clean some spatula and put it in drawer. | 22 | 22 | C | skipped navigation | move spatula 1 to drawer 1 while at the sink | 22 | - (failures with no earlier origin) |
| u074 | put a cool bread in countertop. | 17 | 17 | C | skipped navigation | cool bread 1 with fridge 1 while at countertop 3 | 17 | 2 (earlier failed command) |
| u079 | cool some lettuce and put it in countertop. | 8 | 8 | C | skipped navigation | cool lettuce 1 with fridge 1 while at countertop 2 | 8 | 7 (took an object) |
| u081 | cool some mug and put it in cabinet. | 9 | 9 | C | skipped navigation | move mug 1 to cabinet 3 while at the fridge | 9 | 5 (took an object) |
| u083 | cool some mug and put it in coffeemachine. | 10 | 17 | A | wrong object | took cup 1; the task is mug | 10 | 10 (wrong object taken) |
| u095 | heat some apple and put it in fridge. | 1 | 6 | A | failure misexplained | open fridge 1 from the middle of the room; the next thought blames the action list, then the outputs break format | 1 | 1 (earlier failed command) |
| u097 | heat some apple and put it in fridge. | 1 | 1 | C | skipped navigation | open fridge 1 from the middle of the room, then the outputs break format | 1 | - (failures with no earlier origin) |
| u101 | put a hot cup in cabinet. | 15 | 24 | A | wrong object | took mug 1; the task is cup | 15 | 15 (wrong object taken) |
| u102 | put a hot cup in cabinet. | 8 | 20 | A | wrong object | took mug 3; the task is cup | 8 | 8 (wrong object taken) |
| u103 | put a hot cup in cabinet. | 11 | 17 | A | wrong object | took mug 1; the task is cup | 11 | 11 (wrong object taken) |
| u107 | put a hot mug in cabinet. | 3 | - | - | skipped pickup | no stuck window: many different errors (skipped pickup, put in microwave before heating, coffeemachine) | 4 | - (-) |
| u108 | heat some mug and put it in cabinet. | 14 | 20 | A | put down early | put the mug in the microwave, then heat fails (not held); stoveburner tried at step 11 | 14 | 14 (task object put down early) |
| u109 | put a hot mug in cabinet. | 11 | 29 | A | put down early | put the mug in the microwave, then heat fails (not held); stoveburner tried at step 7 | 11 | 11 (task object put down early) |
| u110 | heat some mug and put it in coffeemachine. | 4 | 11 | A | put down early | put the mug in the coffeemachine (goal) before heating it | 4 | 4 (put the object down) |
| u111 | heat some mug and put it in coffeemachine. | 7 | 14 | A | put down early | put the mug in the coffeemachine (goal) before heating it; tried to heat with the coffeemachine at step 6 | 7 | 13 (took an object) |
| u115 | put a hot tomato in garbagecan. | 12 | 17 | A | put down early | put the tomato in the microwave, then heat fails (not held); stoveburner tried at step 8 | 12 | 12 (task object put down early) |
| u117 | put a hot tomato in garbagecan. | 12 | 20 | A | put down early | put the tomato in the microwave, then heat fails (not held); stoveburner tried at step 8 | 12 | 12 (task object put down early) |
| u119 | find two cd and put them in safe. | 12 | 40 | A | kept carrying | two-object task: kept cd 3 in hand while trying to take the second cd (hands full) | 23 | 39 (put the object down) |
| u122 | put two keychain in safe. | 10 | 35 | A | kept carrying | two-object task: kept keychain 3 in hand while searching for the second | 35 | 9 (took an object) |
| u124 | put two peppershaker in drawer. | 4 | 37 | A | kept carrying | two-object task: kept peppershaker 1 in hand, then take peppershaker 2 fails (hands full) | 5 | 5 (earlier failed command) |
| u129 | find two soapbar and put them in cabinet. | 5 | 23 | A | kept carrying | two-object task: kept soapbar 1 in hand (did not put it in the open cabinet 1) | 17 | 4 (took an object) |
| u132 | put two soapbar in garbagecan. | 19 | 26 | B | skipped navigation | take soapbar 1 from countertop 1 while at the garbagecan (repeated in the window) | 19 | 13 (earlier failed command) |
