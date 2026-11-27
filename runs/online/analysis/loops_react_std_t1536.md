# Loops and their origins: react_std_t1536, 134 games

Stuck = first window of w steps with no new information (every feedback is "Nothing happens" or seen before). Origin = the earliest step that created a condition making a failing command in the window fail (traced from the feedback text). Repeat = k identical commands in a row (secondary).

## Stuck, w = 3

- lost games: 35; stuck: 35; won games that got stuck at some point: 16
- lost and stuck, with an origin step before the window: 26 / 35

## Stuck, w = 5

- lost games: 35; stuck: 34; won games that got stuck at some point: 6
- lost and stuck, with an origin step before the window: 30 / 34

| what explains the stuck window | lost games |
|---|---|
| wrong object taken | 9 |
| task object put down early | 7 |
| earlier failed command | 6 |
| took an object | 5 |
| failures with no earlier origin | 4 |
| put the object down | 3 |

Steps from origin to the start of the stuck window: median 7, range 1-32.

Why the failing commands inside the windows fail (all windows): not at the place 197, not holding that object 93, malformed or unknown command 90, hands full 42, already there 30, already open/closed 6, transform failed (other) 5, placement failed (other) 1

| game | task | stuck from | length | origin step | origin | the agent's next thought (for the audit) | commands in the window |
|---|---|---|---|---|---|---|---|
| u007 | look at bowl under the desklamp. | 9 | 42 | 7 | task object put down early: move bowl 1 to desk 1 | Thought: I have successfully moved the bowl 1 to desk 1. The desklamp 1 is also on desk 1. Now I need to ensure the bowl is positioned "under" the desklamp to satisfy the task "look at bowl under the desklamp". Since I c | use desklamp 1 x42 |
| u008 | look at bowl under the desklamp. | 10 | 41 | 8 | task object put down early: move bowl 1 to shelf 3 | Thought: I have successfully moved bowl 1 to shelf 3, where desklamp 1 is located. The task is to "look at bowl under the desklamp". Since the bowl is now on the shelf under the lamp, I need to use the desklamp to illumi | use desklamp 1 x41 |
| u013 | look at mug under the desklamp. | 18 | 33 | 16 | task object put down early: move mug 1 to desk 1 | Thought: I have placed the mug 1 on desk 1, where the desklamp 1 is also located. The task is to "look at mug under the desklamp". Since I have the mug on the desk with the desklamp, the next logical step to fulfill the  | use desklamp 1 x32; use desklamp 1" and then the interaction x1 |
| u025 | put some peppershaker on drawer. | 22 | 6 | 20 | first failed command: move peppershaker 1 to drawer 1 | Thought: The action "put peppershaker 1 in/on drawer 1" resulted in "Nothing happened". This likely means I cannot place an object directly onto an open drawer in this environment, or the specific interaction requires th | move peppershaker 1 to drawer 1 x2; close drawer 2 x1; close drawer 3 x1; move peppershaker 1 to drawer 2 x1 |
| u030 | put some saltshaker on cabinet. | 13 | 38 | - | failures with no earlier origin | - | move saltshaker 1 to microwave 1 x25; move saltshaker 1 to cabinet 1 x2; move saltshaker 1 to cabinet 3 x1; move saltshaker 1 to cabinet 4 x1 |
| u033 | put some saltshaker on drawer. | 28 | 23 | 20 | first failed command: move saltshaker 1 to drawer 1 | Thought: The action "put saltshaker 1 in/on drawer 1" resulted in "Nothing happened". This might be because the saltshaker is too large to fit inside the drawer, or the system expects the object to be placed "on top" of  | look x8; move saltshaker 1 to drawer 1 x4; close drawer 1 x4; move saltshaker 1 to countertop 1 x1 |
| u042 | put some watch on safe. | 42 | 7 | 37 | wrong object taken: take box 2 from sofa 1 | Thought: I have picked up box 2 from the sofa. Now I need to check if the watch is inside this box. Since I cannot "open" a box with the available actions, I might need to assume the watch is inside and try to take it di | take watch 1 from drawer 5 x6; move watch 1 to safe 1 x1 |
| u043 | clean some bowl and put it in cabinet. | 18 | 11 | - | failures with no earlier origin | - | open cabinet 6 x2; move bowl 1 to cabinet 1 x1; move bowl 1 to cabinet 2 x1; open cabinet 1 x1 |
| u046 | clean some cloth and put it in cabinet. | 22 | 29 | 4 | wrong object taken: take towel 1 from towelholder 1 | Thought: I have successfully picked up the towel 1. The task requires me to clean the cloth and then put it in a cabinet. Now that I have the towel, I need to clean it. A sinkbasin is the appropriate place to clean a clo | clean towel 1 with towelholder 1 x13; clean towel 1 with cabinet 1 x4; take cloth 1 from cabinet 4 x2; clean towel 1 with spraybottle 1 x1 |
| u047 | clean some cloth and put it in cabinet. | 14 | 8 | 3 | wrong object taken: take handtowel 1 from handtowelholder 1 | Thought: I have successfully picked up the handtowel 1. The next step is to clean it. In a household environment, a sinkbasin is the appropriate place to clean a cloth. I will go to sinkbasin 1 to clean the handtowel. Ac | take cloth 1 from cabinet 2 x2; use cloth 1 wait, i can't use an object  x1; open cabinet 2 x1; clean handtowel 1 with sinkbasin 1 x1 |
| u049 | clean some cloth and put it in countertop. | 22 | 29 | 2 | wrong object taken: take handtowel 1 from handtowelholder 1 | Thought: I have successfully picked up the handtowel 1. The task requires me to clean the cloth and then put it on the countertop. Since I have the handtowel, the next logical step is to clean it. The available receptacl | move handtowel 1 to countertop 1 x11; take handtowel 1 from countertop 1 x9; go to countertop 1 x8; use handtowel 1 x1 |
| u055 | put a clean knife in countertop. | 29 | 22 | 20 | wrong object taken: take butterknife 1 from countertop 2 | Thought: I have successfully taken the butterknife 1. Now I need to clean it. The task requires a "clean knife", and the available action for cleaning is "clean obj with recep". I should use the sinkbasin 1 to clean the  | go to countertop 1 x18; none (task completed) x1; move butterknife 1 to countertop 2 x1; move butterknife 1 to countertop 3 x1 |
| u056 | put a clean mug in coffeemachine. | 22 | 29 | 15 | put the object down: move mug 3 to coffeemachine 1 | Thought: The action "put mug 3 in/on coffeemachine 1" was successful, as indicated by the observation "You move the mug 3 to the coffeemachine 1." This means the task "put a clean mug in coffeemachine" has been completed | move mug 3 to coffeemachine 1 x20; clean mug 3 with sinkbasin 1 x3; go to sinkbasin 1 x2; none x1 |
| u072 | clean some spatula and put it in drawer. | 22 | 29 | - | failures with no earlier origin | - | move spatula 1 to drawer 1 x24; open drawer 1 x1; open drawer 2 x1; move spatula 1 to drawer 2 x1 |
| u074 | put a cool bread in countertop. | 17 | 8 | 2 | first failed command: open recep | Thought: The action "open recep" was invalid because the receptacle name was not specified. The available objects include "fridge 1". I need to use the specific object name "fridge 1" to open it. Action: open fridge 1 | cool bread 1 with fridge 1 x2; move bread 1 to fridge 1 x2; close fridge 1 x2; open fridge 1 x1 |
| u079 | cool some lettuce and put it in countertop. | 8 | 11 | 7 | took an object: take lettuce 1 from countertop 2 | Thought: I have successfully picked up lettuce 1. The next step in the task is to cool it. I need to go to the fridge 1 (which I opened earlier) and use the "cool obj with recep" action. Action: cool lettuce 1 with fridg | cool lettuce 1 with fridge 1 x4; move lettuce 1 to fridge 1 x2; close fridge 1 x1; open fridge 1". the example does not use x1 |
| u081 | cool some mug and put it in cabinet. | 9 | 17 | 5 | took an object: take mug 1 from cabinet 3 | Thought: I have successfully picked up mug 1. The next step in the task is to cool the mug. I need to go to the fridge 1 to perform the cooling action. Action: go to fridge 1 | move mug 1 to cabinet 1 x2; move mug 1 to cabinet 4 x2; move mug 1 to cabinet 2 x2; move mug 1 to cabinet 3 x1 |
| u083 | cool some mug and put it in coffeemachine. | 17 | 7 | 10 | wrong object taken: take cup 1 from cabinet 6 | Thought: I have successfully picked up the cup 1. The next step in the task is to cool it. According to the available actions, I can use the fridge to cool an object. I need to go to the fridge 1 and then cool the cup wi | move cup 1 to countertop 1 x2; move cup 1 to drawer 1 x1; move cup 1 to drawer 2 x1; move cup 1 to countertop 2 x1 |
| u095 | heat some apple and put it in fridge. | 6 | 45 | 1 | first failed command: open fridge 1 | Thought: The action "open fridge 1" resulted in "Nothing happens", which is unexpected since the fridge is listed in the environment. However, looking at the available actions, there is no specific "open" action for the  | take obj from stoveburner 1 x25; take obj from garbagecan 1 x2; '". this was a formatting error, not a l x1; '" in the previous turn indicates a stri x1 |
| u097 | heat some apple and put it in fridge. | 1 | 6 | - | failures with no earlier origin | - | open fridge 1 x1; open fridge 1". this is a contradiction. x1; open fridge x1; open cabinet 1 x1 |
| u101 | put a hot cup in cabinet. | 24 | 6 | 15 | wrong object taken: take mug 1 from shelf 2 | Thought: I have successfully taken the mug 1. The task requires a "hot cup", so I need to heat the mug next. The available appliances for heating are the microwave 1 and the stoveburners. I will use the microwave 1 to he | heat mug 1 with stoveburner 1 x1; move mug 1 to cabinet 3 x1; open cabinet 3 x1; open cabinet 4 x1 |
| u102 | put a hot cup in cabinet. | 20 | 16 | 8 | wrong object taken: take mug 3 from countertop 1 | Thought: I have successfully picked up the mug 3. Now I need to heat it. The microwave is a suitable appliance for heating a mug. I will go to the microwave 1 to heat the mug. Action: go to microwave 1 | open microwave 1 x4; move mug 3 to stoveburner 1 x3; move mug 3 to coffeemachine 1 x1; take mug 1 from microwave 1 x1 |
| u103 | put a hot cup in cabinet. | 17 | 7 | 11 | wrong object taken: take mug 1 from countertop 1 | Thought: I have successfully taken the mug 1. Now I need to heat it. The microwave attempts failed, possibly because the object wasn't explicitly taken or the interaction logic requires a specific sequence. Let's try the | none x1; open cabinet 1 x1; move mug 1 to cabinet 2 x1; open cabinet 3 x1 |
| u108 | heat some mug and put it in cabinet. | 20 | 31 | 14 | task object put down early: move mug 1 to microwave 1 | Thought: I have successfully placed the mug 1 into the microwave 1. Now I need to heat it. The action "heat obj with recep" should work here. Action: heat mug 1 with microwave 1 | heat mug 1 with stoveburner 2 x9; heat mug 1 with stoveburner 3 x9; heat mug 1 with stoveburner 4 x9; take mug 1 from microwave 1 x1 |
| u109 | put a hot mug in cabinet. | 29 | 6 | 11 | task object put down early: move mug 1 to microwave 1 | Thought: I have successfully moved the mug 1 into the microwave 1. Now I need to heat it. The available action is "heat obj with recep", so I will heat the mug 1 using the microwave 1. Action: heat mug 1 with microwave 1 | heat mug 1 with coffeemachine 1 x1; move mug 1 to coffeemachine 1 x1; go to stoveburner 1 x1; heat mug 1 with stoveburner 1 x1 |
| u110 | heat some mug and put it in coffeemachine. | 11 | 5 | 4 | put the object down: move mug 2 to coffeemachine 1 | Thought: I have successfully moved the mug 2 into the coffeemachine 1. The task requires me to heat the mug and put it in the coffeemachine. Since the mug is now inside the coffeemachine, the next logical step is to heat | move mug 2 to microwave 1 x1; use coffeemachine 1 x1; use mug 2 x1; use stoveburner 1 x1 |
| u111 | heat some mug and put it in coffeemachine. | 14 | 37 | 13 | took an object: take mug 2 from coffeemachine 1 | Thought: I have successfully picked up the mug 2 from the coffeemachine 1. Now I need to heat it. Since the coffeemachine failed to heat the mug, I will try heating it with the stoveburner 1, which is a standard heating  | take mug 2 from coffeemachine 1 x21; use mug 2 x11; move mug 2 to coffeemachine 1 x2; go to stoveburner 1 x1 |
| u115 | put a hot tomato in garbagecan. | 17 | 7 | 12 | task object put down early: move tomato 1 to microwave 1 | Thought: I have successfully placed the tomato 1 inside the microwave 1. Now, to fulfill the task requirement of having a "hot tomato", I need to heat it using the microwave. Action: heat tomato 1 with microwave 1 | heat tomato 1 with stoveburner 1 x2; go to stoveburner 1 x1; close microwave 1 if that works, then i  x1; close microwave 1 x1 |
| u117 | put a hot tomato in garbagecan. | 20 | 5 | 12 | task object put down early: move tomato 1 to microwave 1 | Thought: I have successfully placed the tomato 1 inside the microwave 1. Now I need to heat it to make it "hot" as required by the task. I will use the microwave to heat the tomato. Action: heat tomato 1 with microwave 1 | heat tomato 1 with stoveburner 1 x2; go to stoveburner 1 x1; move tomato 1 to stoveburner 1 x1; move tomato 1 to garbagecan 1 x1 |
| u119 | find two cd and put them in safe. | 40 | 11 | 39 | put the object down: move cd 3 to safe 1 | Thought: I have successfully put `cd 3` into the safe. Now I need to find and put a second CD into the safe to complete the task. The other CDs (`cd 1` and `cd 2`) were visible on the desks, but the "take" action failed  | move cd 3 to safe 1 x7; take cd 1 from desk 1 x2; go to safe 1 x2 |
| u122 | put two keychain in safe. | 35 | 11 | 9 | took an object: take keychain 3 from drawer 4 | Thought: I have successfully taken keychain 3. Now I need to find the second keychain. I will continue checking the remaining drawers. Next, I will go to drawer 5. Action: go to drawer 5 | take keychain 2 from dresser 1 x3; take keychain 1 from dresser 1 x3; open dresser 1 x3; take box 1 from dresser 1 x1 |
| u124 | put two peppershaker in drawer. | 37 | 14 | 5 | first failed command: take peppershaker 2 from countertop 3 | Thought: The action "take peppershaker 2 from countertop 3" resulted in "Nothing happened", which means I cannot directly pick up the object from the countertop using the "take" action in this specific context, or perhap | look x14 |
| u129 | find two soapbar and put them in cabinet. | 23 | 7 | 4 | took an object: take soapbar 1 from countertop 1 | Thought: I have successfully taken soapbar 1. Now I need to find the second soapbar. Common locations for soapbars include other countertops, cabinets, or near sinks. Since I've checked the sinks and the current countert | move soapbar 1 to cabinet 1 x2; take soapbar 2 from toilet 1 x1; open cabinet 1 x1; move soapbar 1 to cabinet 2 x1 |
| u132 | put two soapbar in garbagecan. | 26 | 25 | 13 | first failed command: take soapbar 4 from countertop 1 | Thought: The action "take soapbar 4 from countertop 1" resulted in "Nothing happened", which means I cannot directly take the object from the countertop in this state. Perhaps I need to interact with the object first or  | use soapbar 1 x18; take soapbar 1 from countertop 1 x3; take soapbar 3 from countertop 1 x2; take soapbar 4 from countertop 1 x2 |

## Stuck, w = 8

- lost games: 35; stuck: 30; won games that got stuck at some point: 0
- lost and stuck, with an origin step before the window: 27 / 30

## Repeat, k = 2

- lost games: 35; with a loop: 32; won games with a loop: 6
- lost games whose loop has an earlier origin step: 10 / 32

## Repeat, k = 3

- lost games: 35; with a loop: 25; won games with a loop: 2
- lost games whose loop has an earlier origin step: 10 / 25

| why the looped command fails | lost games | of them with an earlier origin |
|---|---|---|
| not holding that object | 7 | 7 |
| not at the place | 6 | 0 |
| malformed or unknown command | 4 | 0 |
| succeeds | 3 | 0 |
| hands full | 3 | 3 |
| already there | 2 | 0 |

| origin found | lost games |
|---|---|
| none | 15 |
| put the object down | 7 |
| took an object | 2 |
| wrong object | 1 |

Steps from origin to loop start: median 7, range 2-19.

## Repeat, k = 4

- lost games: 35; with a loop: 23; won games with a loop: 1
- lost games whose loop has an earlier origin step: 8 / 23

## Per game (k = 3)

| game | task | won | loop starts | looped command | why it fails | origin step | origin | first wrong take | target put down early |
|---|---|---|---|---|---|---|---|---|---|
| u001 | examine the alarmclock with the desklamp. | yes | - | - | - | - | - | - | - |
| u002 | examine the alarmclock with the desklamp. | yes | - | - | - | - | - | - | - |
| u003 | look at alarmclock under the desklamp. | yes | - | - | - | - | - | - | - |
| u004 | examine the book with the desklamp. | yes | - | - | - | - | - | - | - |
| u005 | examine the book with the desklamp. | yes | - | - | - | - | - | - | - |
| u006 | examine the book with the desklamp. | yes | - | - | - | - | - | - | - |
| u007 | look at bowl under the desklamp. | no | 8 | use desklamp 1 | succeeds | - | none | - | 7 |
| u008 | look at bowl under the desklamp. | no | 9 | use desklamp 1 | succeeds | - | none | - | 8 |
| u009 | examine the bowl with the desklamp. | yes | - | - | - | - | - | - | - |
| u010 | look at cd under the desklamp. | yes | - | - | - | - | - | - | - |
| u011 | examine the cd with the desklamp. | yes | - | - | - | - | - | - | - |
| u012 | examine the cd with the desklamp. | yes | - | - | - | - | - | - | - |
| u013 | look at mug under the desklamp. | no | 20 | use desklamp 1 | succeeds | - | none | - | 16 |
| u014 | examine the mug with the desklamp. | yes | - | - | - | - | - | - | - |
| u015 | examine the mug with the desklamp. | yes | - | - | - | - | - | - | - |
| u016 | look at pencil under the desklamp. | yes | - | - | - | - | - | - | - |
| u017 | examine the pencil with the desklamp. | yes | - | - | - | - | - | - | - |
| u018 | examine the pencil with the desklamp. | yes | - | - | - | - | - | - | - |
| u019 | put a mug in desk. | yes | - | - | - | - | - | - | - |
| u020 | put some mug on desk. | yes | - | - | - | - | - | - | - |
| u021 | put a mug in desk. | yes | - | - | - | - | - | - | - |
| u022 | put a pencil in shelf. | yes | - | - | - | - | - | - | - |
| u023 | put a pencil in shelf. | yes | - | - | - | - | - | - | - |
| u024 | put a pencil in shelf. | yes | - | - | - | - | - | - | - |
| u025 | put some peppershaker on drawer. | no | - | - | - | - | - | - | - |
| u026 | put a peppershaker in drawer. | yes | - | - | - | - | - | - | - |
| u027 | put some peppershaker on drawer. | yes | - | - | - | - | - | - | - |
| u028 | put some saltshaker on cabinet. | yes | - | - | - | - | - | - | - |
| u029 | put some saltshaker on cabinet. | yes | - | - | - | - | - | - | - |
| u030 | put some saltshaker on cabinet. | no | 25 | move saltshaker 1 to microwave 1 | not at the place | - | none | - | - |
| u031 | put a saltshaker in drawer. | yes | - | - | - | - | - | - | - |
| u032 | put a saltshaker in drawer. | yes | - | - | - | - | - | - | - |
| u033 | put some saltshaker on drawer. | no | - | - | - | - | - | - | - |
| u034 | put some soapbottle on toilet. | yes | - | - | - | - | - | - | - |
| u035 | put a soapbottle in toilet. | yes | - | - | - | - | - | - | - |
| u036 | put a soapbottle in toilet. | yes | - | - | - | - | - | - | - |
| u037 | put a vase in safe. | yes | - | - | - | - | - | - | - |
| u038 | put some vase on safe. | yes | - | - | - | - | - | - | - |
| u039 | put a vase in safe. | yes | - | - | - | - | - | - | - |
| u040 | put some watch on safe. | yes | - | - | - | - | - | - | - |
| u041 | put some watch on safe. | yes | - | - | - | - | - | - | - |
| u042 | put some watch on safe. | no | 42 | take watch 1 from drawer 5 | hands full | 37 | wrong object: take box 2 from sofa 1 | 37 | - |
| u043 | clean some bowl and put it in cabinet. | no | 44 | move bowl 1 to shelf 3 | not at the place | - | none | - | - |
| u044 | put a clean bowl in cabinet. | yes | - | - | - | - | - | - | - |
| u045 | clean some bowl and put it in cabinet. | yes | - | - | - | - | - | - | - |
| u046 | clean some cloth and put it in cabinet. | no | 33 | clean towel 1 with towelholder 1 | not at the place | - | none | 4 | - |
| u047 | clean some cloth and put it in cabinet. | no | 39 | clean handtowel 1 with sinkbasin 1 | not holding that object | 32 | put the object down: move handtowel 1 to sinkbasin 1 | 3 | - |
| u048 | put a clean cloth in countertop. | yes | - | - | - | - | - | - | - |
| u049 | clean some cloth and put it in countertop. | no | - | - | - | - | - | 2 | - |
| u050 | clean some egg and put it in microwave. | yes | - | - | - | - | - | - | - |
| u051 | put a clean egg in microwave. | yes | - | - | - | - | - | - | - |
| u052 | put a clean egg in microwave. | yes | - | - | - | - | - | - | - |
| u053 | clean some knife and put it in countertop. | yes | - | - | - | - | - | - | - |
| u054 | put a clean knife in countertop. | yes | - | - | - | - | - | 12 | - |
| u055 | put a clean knife in countertop. | no | 34 | go to countertop 1 | already there | - | none | 20 | - |
| u056 | put a clean mug in coffeemachine. | no | 34 | move mug 3 to coffeemachine 1 | not holding that object | 15 | put the object down: move mug 3 to coffeemachine 1 | - | - |
| u057 | put a clean mug in coffeemachine. | yes | - | - | - | - | - | - | - |
| u058 | put a clean mug in coffeemachine. | yes | - | - | - | - | - | - | - |
| u059 | clean some pan and put it in countertop. | yes | - | - | - | - | - | - | - |
| u060 | clean some pan and put it in countertop. | yes | - | - | - | - | - | - | - |
| u061 | put a clean pan in countertop. | yes | - | - | - | - | - | - | - |
| u062 | put a clean plate in countertop. | yes | - | - | - | - | - | - | - |
| u063 | put a clean plate in countertop. | yes | - | - | - | - | - | - | - |
| u064 | clean some plate and put it in countertop. | yes | - | - | - | - | - | - | - |
| u065 | clean some soapbar and put it in cabinet. | yes | - | - | - | - | - | - | - |
| u066 | clean some soapbar and put it in cabinet. | yes | - | - | - | - | - | - | - |
| u067 | clean some soapbar and put it in cabinet. | yes | - | - | - | - | - | - | - |
| u068 | put a clean soapbar in countertop. | yes | - | - | - | - | - | - | - |
| u069 | put a clean soapbar in countertop. | yes | - | - | - | - | - | - | - |
| u070 | clean some soapbar and put it in countertop. | yes | 13 | take soapbar 1 from countertop 1 | not at the place | - | none | - | - |
| u071 | put a clean spatula in drawer. | yes | - | - | - | - | - | - | - |
| u072 | clean some spatula and put it in drawer. | no | 29 | move spatula 1 to drawer 1 | not at the place | - | none | - | - |
| u073 | clean some spatula and put it in drawer. | yes | - | - | - | - | - | - | - |
| u074 | put a cool bread in countertop. | no | 43 | go to countertop 1 | already there | - | none | - | 29 |
| u075 | cool some bread and put it in countertop. | yes | - | - | - | - | - | - | - |
| u076 | cool some bread and put it in countertop. | yes | - | - | - | - | - | - | - |
| u077 | cool some lettuce and put it in countertop. | yes | - | - | - | - | - | - | - |
| u078 | put a cool lettuce in countertop. | yes | - | - | - | - | - | - | - |
| u079 | cool some lettuce and put it in countertop. | no | 22 | move lettuce 1 to countertop 2 | not holding that object | 19 | put the object down: move lettuce 1 to countertop 2 | - | - |
| u080 | put a cool mug in cabinet. | yes | - | - | - | - | - | - | - |
| u081 | cool some mug and put it in cabinet. | no | 31 | move mug 1 to countertop 1 | not at the place | - | none | - | - |
| u082 | cool some mug and put it in cabinet. | yes | - | - | - | - | - | - | - |
| u083 | cool some mug and put it in coffeemachine. | no | 34 | move cup 1 to countertop 1 | not holding that object | 30 | put the object down: move cup 1 to countertop 1 | 10 | - |
| u084 | cool some mug and put it in coffeemachine. | yes | - | - | - | - | - | - | - |
| u085 | put a cool mug in coffeemachine. | yes | - | - | - | - | - | - | - |
| u086 | cool some pan and put it in countertop. | yes | - | - | - | - | - | - | - |
| u087 | put a cool pan in countertop. | yes | - | - | - | - | - | - | - |
| u088 | cool some pan and put it in countertop. | yes | - | - | - | - | - | - | - |
| u089 | cool some potato and put it in microwave. | yes | - | - | - | - | - | - | - |
| u090 | cool some potato and put it in microwave. | yes | - | - | - | - | - | - | - |
| u091 | cool some potato and put it in microwave. | yes | - | - | - | - | - | - | - |
| u092 | put a cool tomato in microwave. | yes | - | - | - | - | - | - | - |
| u093 | put a cool tomato in microwave. | yes | - | - | - | - | - | - | - |
| u094 | put a cool tomato in microwave. | yes | - | - | - | - | - | - | - |
| u095 | heat some apple and put it in fridge. | no | 25 | take obj from stoveburner 1 | malformed or unknown command | - | none | - | - |
| u096 | put a hot apple in fridge. | yes | - | - | - | - | - | - | - |
| u097 | heat some apple and put it in fridge. | no | - | - | - | - | - | - | - |
| u098 | heat some apple and put it in garbagecan. | yes | - | - | - | - | - | - | 7 |
| u099 | heat some apple and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u100 | heat some apple and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u101 | put a hot cup in cabinet. | no | - | - | - | - | - | 15 | - |
| u102 | put a hot cup in cabinet. | no | - | - | - | - | - | 8 | - |
| u103 | put a hot cup in cabinet. | no | 35 | move mug 1 to cabinet 1 | not holding that object | 25 | put the object down: move mug 1 to cabinet 1 | 11 | - |
| u104 | heat some egg and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u105 | heat some egg and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u106 | heat some egg and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u107 | put a hot mug in cabinet. | no | - | - | - | - | - | - | 17 |
| u108 | heat some mug and put it in cabinet. | no | - | - | - | - | - | - | 14 |
| u109 | put a hot mug in cabinet. | no | - | - | - | - | - | - | 11 |
| u110 | heat some mug and put it in coffeemachine. | no | 18 | use coffeemachine 1 | malformed or unknown command | - | none | - | - |
| u111 | heat some mug and put it in coffeemachine. | no | 22 | take mug 2 from coffeemachine 1 | hands full | 13 | took an object: take mug 2 from coffeemachine 1 | - | - |
| u112 | put a hot mug in coffeemachine. | yes | - | - | - | - | - | - | 15 |
| u113 | heat some potato and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u114 | put a hot potato in garbagecan. | yes | - | - | - | - | - | - | - |
| u115 | put a hot tomato in garbagecan. | no | 40 | move tomato 1 to stoveburner 1 | not at the place | - | none | - | 12 |
| u116 | heat some tomato and put it in garbagecan. | yes | - | - | - | - | - | - | - |
| u117 | put a hot tomato in garbagecan. | no | 41 | use garbagecan 1 | malformed or unknown command | - | none | - | 12 |
| u118 | put two cd in safe. | yes | - | - | - | - | - | - | - |
| u119 | find two cd and put them in safe. | no | 45 | move cd 3 to safe 1 | not holding that object | 39 | put the object down: move cd 3 to safe 1 | - | - |
| u120 | put two cd in safe. | yes | - | - | - | - | - | - | - |
| u121 | put two keychain in safe. | yes | 36 | take keychain 2 from sofa 1 | hands full | 24 | took an object: take keychain 1 from sidetable 1 | - | - |
| u122 | put two keychain in safe. | no | - | - | - | - | - | - | - |
| u123 | put two peppershaker in drawer. | yes | - | - | - | - | - | - | - |
| u124 | put two peppershaker in drawer. | no | 5 | take peppershaker 2 from countertop 3 | hands full | 3 | took an object: take peppershaker 1 from countertop 2 | - | - |
| u125 | find two peppershaker and put them in drawer. | yes | - | - | - | - | - | - | - |
| u126 | find two pillow and put them in sofa. | yes | - | - | - | - | - | - | - |
| u127 | put two pillow in sofa. | yes | - | - | - | - | - | - | - |
| u128 | put two pillow in sofa. | yes | - | - | - | - | - | - | - |
| u129 | find two soapbar and put them in cabinet. | no | 47 | move soapbar 1 to cabinet 1 | not holding that object | 31 | put the object down: move soapbar 1 to cabinet 1 | - | - |
| u130 | find two soapbar and put them in cabinet. | yes | - | - | - | - | - | - | - |
| u131 | put two soapbar in garbagecan. | yes | - | - | - | - | - | - | - |
| u132 | put two soapbar in garbagecan. | no | 32 | use soapbar 1 | malformed or unknown command | - | none | - | - |
| u133 | put two soapbar in garbagecan. | yes | - | - | - | - | - | - | - |
| u134 | find two toiletpaper and put them in cabinet. | yes | - | - | - | - | - | - | - |
