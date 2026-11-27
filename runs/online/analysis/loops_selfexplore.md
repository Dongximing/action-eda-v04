# Loops and their origins: selfexplore, 68 games

Stuck = first window of w steps with no new information (every feedback is "Nothing happens" or seen before). Origin = the earliest step that created a condition making a failing command in the window fail (traced from the feedback text). Repeat = k identical commands in a row (secondary).

## Stuck, w = 3

- lost games: 26; stuck: 26; won games that got stuck at some point: 15
- lost and stuck, with an origin step before the window: 18 / 26

## Stuck, w = 5

- lost games: 26; stuck: 25; won games that got stuck at some point: 10
- lost and stuck, with an origin step before the window: 19 / 25

| what explains the stuck window | lost games |
|---|---|
| wrong object taken | 9 |
| earlier failed command | 9 |
| failures with no earlier origin | 4 |
| no failing command (no new information); target not seen yet | 2 |
| took an object | 1 |

Steps from origin to the start of the stuck window: median 7, range 1-16.

Why the failing commands inside the windows fail (all windows): already there 162, not at the place 65, go to failed (place unknown) 47, hands full 25, not holding that object 23, transform failed (other) 6, already open/closed 2, object not there 2, receptacle closed 1

| game | task | stuck from | length | origin step | origin | the agent's next thought (for the audit) | commands in the window |
|---|---|---|---|---|---|---|---|
| game02 | put a hot cup in cabinet. | 3 | 48 | 2 | wrong object taken: take mug 1 from coffeemachine 1 | - | go to coffeemachine 1 x48 |
| game03 | put a clean butterknife in drawer. | 25 | 8 | 11 | first failed command: go to drawer 5 | - | look x4; go to drawer 2 x2; go to countertop 1 x1; go to sinkbasin 1 x1 |
| game05 | put a cool tomato in countertop. | 22 | 29 | - | no failing command (no new information); target not seen yet | - | go to sinkbasin 1 x15; go to fridge 1 x14 |
| game06 | put a hot plate in cabinet. | 7 | 14 | 2 | wrong object taken: take pan 1 from countertop 1 | - | go to stoveburner 1 x10; heat pan 1 with stoveburner 1 x3; go to stoveburner 2 x1 |
| game11 | put a clean cloth in cabinet. | 7 | 20 | 2 | wrong object taken: take towel 1 from towelholder 1 | - | clean towel 1 with sinkbasin 1 x20 |
| new02 | clean some cloth and put it in drawer. | 10 | 22 | 2 | wrong object taken: take towel 1 from towelholder 1 | - | go to towelholder 4 x20; take cloth 1 from drawer 1 x1; go to sinkbasin 1 x1 |
| new07 | put a clean plate in countertop. | 10 | 14 | 5 | first failed command: move plate 3 to countertop 2 | - | go to countertop 2 x6; move plate 3 to countertop 1 x3; go to countertop 1 x3; move plate 3 to countertop 2 x2 |
| new11 | cool some bread and put it in countertop. | 13 | 24 | 2 | first failed command: open toaster 1 | - | go to toaster 1 x24 |
| new12 | put a cool cup in microwave. | 26 | 25 | 14 | wrong object taken: take mug 1 from countertop 1 | - | move mug 1 to microwave 1 x23; take cup 1 from microwave 1 x1; close microwave 1 x1 |
| new18 | put a hot egg in fridge. | 10 | 6 | 4 | first failed command: heat egg 4 with microwave 1 | - | go to microwave 1 x3; go to fridge 1 x2; take egg 4 from fridge 1 x1 |
| new19 | put a hot mug in cabinet. | 20 | 31 | 4 | first failed command: heat mug 1 with stoveburner 1 | - | go to coffeemachine 1 x31 |
| new20 | put a hot mug in coffeemachine. | 12 | 10 | 5 | first failed command: heat mug 1 with coffeemachine 1 | - | go to fridge 1 x5; go to coffeemachine 1 x2; open coffeemachine 1 x2; heat mug 1 with coffeemachine 1 x1 |
| new22 | put a hot plate in diningtable. | 8 | 5 | 2 | wrong object taken: take pan 1 from stoveburner 1 | - | go to stoveburner 2 x5 |
| new24 | put a hot tomato in fridge. | 19 | 7 | - | failures with no earlier origin | - | go to stoveburner 1 x5; take tomato 1 from diningtable 1 x1; go to diningtable 1 x1 |
| new25 | put a clean butterknife in diningtable. | 7 | 26 | 2 | took an object: take butterknife 1 from diningtable 1 | - | go to diningtable 1 x11; take butterknife 1 from diningtable 1 x8; go to sinkbasin 1 x7 |
| new32 | cool some plate and put it in countertop. | 11 | 24 | 2 | first failed command: take plate 1 from countertop 1 | - | go to countertop 1 x12; go to stoveburner 1 x11; take plate 1 from countertop 1 x1 |
| new34 | put a hot potato in fridge. | 9 | 42 | 3 | first failed command: go to stoveburner 2 | - | go to stoveburner 4 x27; go to stoveburner 2 x6; go to stoveburner 1 x5; heat potato 1 with stoveburner 1 x2 |
| new37 | put a clean butterknife in countertop. | 20 | 8 | - | failures with no earlier origin | - | go to drawer 1 x8 |
| new38 | clean some butterknife and put it in drawer. | 45 | 6 | - | failures with no earlier origin | - | go to countertop 2 x5; go to countertop 1 x1 |
| new40 | clean some dishsponge and put it in countertop. | 23 | 28 | - | failures with no earlier origin | - | clean dishsponge 1 with sinkbasin 1 x23; clean dishsponge 1 with bathtubbasin 1 x4; clean dishsponge 1 with sinkbasin 2 x1 |
| new42 | put a clean ladle in countertop. | 12 | 39 | - | no failing command (no new information); target not seen yet | - | go to sinkbasin 1 x19; go to countertop 2 x19; look x1 |
| new43 | clean some plate and put it in fridge. | 25 | 26 | 18 | wrong object taken: take pot 2 from countertop 2 | - | take pan 1 from countertop 2 x15; go to countertop 2 x11 |
| new48 | cool some apple and put it in countertop. | 26 | 5 | 11 | first failed command: take apple 1 from fridge 1 | - | go to fridge 1 x2; open fridge 1 x1; take apple 1 from fridge 1 x1; go to countertop 1 x1 |
| new53 | put a cool mug in coffeemachine. | 25 | 26 | 12 | wrong object taken: take cup 2 from cabinet 6 | - | go to countertop 1 x10; go to cabinet 7 x9; move cup 2 to coffeemachine 1 x7 |
| new55 | put a cool pot in diningtable. | 6 | 6 | 3 | wrong object taken: take pan 1 from stoveburner 2 | - | go to stoveburner 4 x5; take pot 1 from stoveburner 4 x1 |

## Stuck, w = 8

- lost games: 26; stuck: 24; won games that got stuck at some point: 3
- lost and stuck, with an origin step before the window: 20 / 24

## Repeat, k = 2

- lost games: 26; with a loop: 24; won games with a loop: 17
- lost games whose loop has an earlier origin step: 1 / 24

## Repeat, k = 3

- lost games: 26; with a loop: 24; won games with a loop: 13
- lost games whose loop has an earlier origin step: 1 / 24

| why the looped command fails | lost games | of them with an earlier origin |
|---|---|---|
| succeeds | 11 | 0 |
| already there | 7 | 0 |
| not at the place | 2 | 0 |
| go to failed (place unknown) | 2 | 0 |
| not holding that object | 1 | 1 |
| already open/closed | 1 | 0 |

| origin found | lost games |
|---|---|
| none | 23 |
| put the object down | 1 |

Steps from origin to loop start: median 4, range 4-4.

## Repeat, k = 4

- lost games: 26; with a loop: 22; won games with a loop: 11
- lost games whose loop has an earlier origin step: 1 / 22

## Per game (k = 3)

| game | task | won | loop starts | looped command | why it fails | origin step | origin | first wrong take | target put down early |
|---|---|---|---|---|---|---|---|---|---|
| game01 | heat some mug and put it in cabinet. | yes | - | - | - | - | - | - | - |
| game02 | put a hot cup in cabinet. | no | 3 | go to coffeemachine 1 | already there | - | none | 2 | - |
| game03 | put a clean butterknife in drawer. | no | 28 | look | succeeds | - | none | - | - |
| game04 | put a cool tomato in microwave. | yes | 3 | look | succeeds | - | none | - | - |
| game05 | put a cool tomato in countertop. | no | - | - | - | - | - | - | - |
| game06 | put a hot plate in cabinet. | no | 8 | go to stoveburner 1 | already there | - | none | 2 | - |
| game07 | cool some tomato and put it in garbagecan. | yes | 32 | close garbagecan 1 | already open/closed | - | none | - | - |
| game08 | clean some spatula and put it in diningtable. | yes | - | - | - | - | - | - | - |
| game09 | put a hot potato in fridge. | yes | 6 | go to stoveburner 1 | already there | - | none | - | - |
| game10 | clean some lettuce and put it in fridge. | yes | 2 | look | succeeds | - | none | - | - |
| game11 | put a clean cloth in cabinet. | no | 7 | clean towel 1 with sinkbasin 1 | not at the place | - | none | 2 | - |
| game12 | cool some pan and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new01 | put a clean butterknife in drawer. | yes | - | - | - | - | - | - | - |
| new02 | clean some cloth and put it in drawer. | no | 12 | go to towelholder 4 | go to failed (place unknown) | - | none | 2 | - |
| new03 | put a clean ladle in diningtable. | yes | 2 | look | succeeds | - | none | - | - |
| new04 | clean some ladle and put it in diningtable. | yes | 2 | look | succeeds | - | none | - | - |
| new05 | put a clean lettuce in countertop. | yes | - | - | - | - | - | - | - |
| new06 | clean some mug and put it in coffeemachine. | yes | - | - | - | - | - | - | - |
| new07 | put a clean plate in countertop. | no | 35 | go to diningtable 1 | already there | - | none | - | - |
| new08 | put a clean soapbar in drawer. | yes | - | - | - | - | - | - | - |
| new09 | put a cool apple in garbagecan. | yes | - | - | - | - | - | - | - |
| new10 | cool some apple and put it in microwave. | yes | - | - | - | - | - | - | - |
| new11 | cool some bread and put it in countertop. | no | 13 | go to toaster 1 | succeeds | - | none | - | - |
| new12 | put a cool cup in microwave. | no | 28 | move mug 1 to microwave 1 | not holding that object | 24 | put the object down: move mug 1 to microwave 1 | 14 | - |
| new13 | put a cool egg in microwave. | yes | 3 | look | succeeds | - | none | - | - |
| new14 | put a cool plate in cabinet. | yes | - | - | - | - | - | - | - |
| new15 | put a cool tomato in countertop. | yes | - | - | - | - | - | - | - |
| new16 | cool some winebottle and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new17 | heat some apple and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new18 | put a hot egg in fridge. | no | 23 | close fridge 1 | already open/closed | - | none | - | - |
| new19 | put a hot mug in cabinet. | no | 19 | go to coffeemachine 1 | succeeds | - | none | - | - |
| new20 | put a hot mug in coffeemachine. | no | 13 | go to fridge 1 | already there | - | none | - | - |
| new21 | put a hot mug in sidetable. | yes | - | - | - | - | - | - | - |
| new22 | put a hot plate in diningtable. | no | 7 | go to stoveburner 2 | succeeds | - | none | 2 | - |
| new23 | heat some tomato and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new24 | put a hot tomato in fridge. | no | 21 | go to stoveburner 1 | already there | - | none | - | - |
| new25 | put a clean butterknife in diningtable. | no | 33 | look | succeeds | - | none | - | - |
| new26 | clean some fork and put it in drawer. | no | 2 | look | succeeds | - | none | - | - |
| new27 | clean some ladle and put it in countertop. | yes | 2 | look | succeeds | - | none | - | - |
| new28 | clean some ladle and put it in diningtable. | yes | 2 | look | succeeds | - | none | - | - |
| new29 | cool some lettuce and put it in countertop. | yes | 35 | go to countertop 1 | already there | - | none | - | - |
| new30 | put a cool pan in stoveburner. | yes | - | - | - | - | - | - | - |
| new31 | cool some plate and put it in cabinet. | yes | - | - | - | - | - | - | - |
| new32 | cool some plate and put it in countertop. | no | 46 | move plate 1 to countertop 3 | not at the place | - | none | - | - |
| new33 | heat some egg and put it in countertop. | yes | - | - | - | - | - | - | - |
| new34 | put a hot potato in fridge. | no | 15 | go to stoveburner 4 | go to failed (place unknown) | - | none | - | - |
| new35 | heat some tomato and put it in fridge. | yes | - | - | - | - | - | - | - |
| new36 | heat some tomato and put it in fridge. | yes | - | - | - | - | - | - | - |
| new37 | put a clean butterknife in countertop. | no | 20 | go to drawer 1 | succeeds | - | none | - | - |
| new38 | clean some butterknife and put it in drawer. | no | 2 | look | succeeds | - | none | - | - |
| new39 | put a clean dishsponge in cart. | yes | - | - | - | - | - | - | - |
| new40 | clean some dishsponge and put it in countertop. | no | 2 | look | succeeds | - | none | - | - |
| new41 | put a clean fork in countertop. | yes | - | - | - | - | - | - | - |
| new42 | put a clean ladle in countertop. | no | 2 | look | succeeds | - | none | - | - |
| new43 | clean some plate and put it in fridge. | no | 2 | look | succeeds | - | none | - | - |
| new44 | put a clean soapbar in cabinet. | yes | 2 | look | succeeds | - | none | - | - |
| new45 | put a clean soapbar in toilet. | yes | - | - | - | - | - | - | - |
| new46 | put a clean soapbar in toilet. | yes | - | - | - | - | - | - | - |
| new47 | clean some tomato and put it in countertop. | yes | - | - | - | - | - | - | - |
| new48 | cool some apple and put it in countertop. | no | 21 | go to fridge 1 | already there | - | none | - | - |
| new49 | put a cool apple in microwave. | yes | 5 | look | succeeds | - | none | - | - |
| new50 | put a cool bowl in cabinet. | yes | - | - | - | - | - | - | - |
| new51 | put a cool cup in sidetable. | yes | - | - | - | - | - | - | - |
| new52 | put a cool lettuce in countertop. | yes | 25 | move lettuce 1 to countertop 1 | not at the place | - | none | - | - |
| new53 | put a cool mug in coffeemachine. | no | - | - | - | - | - | 12 | - |
| new54 | cool some pan and put it in stoveburner. | yes | - | - | - | - | - | - | - |
| new55 | put a cool pot in diningtable. | no | 7 | go to stoveburner 4 | already there | - | none | 3 | - |
| new56 | cool some tomato and put it in microwave. | yes | - | - | - | - | - | - | - |
