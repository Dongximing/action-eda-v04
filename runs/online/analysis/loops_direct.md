# Loops and their origins: direct, 56 games

Stuck = first window of w steps with no new information (every feedback is "Nothing happens" or seen before). Origin = the earliest step that created a condition making a failing command in the window fail (traced from the feedback text). Repeat = k identical commands in a row (secondary).

## Stuck, w = 3

- lost games: 35; stuck: 35; won games that got stuck at some point: 8
- lost and stuck, with an origin step before the window: 12 / 35

## Stuck, w = 5

- lost games: 35; stuck: 35; won games that got stuck at some point: 7
- lost and stuck, with an origin step before the window: 14 / 35

| what explains the stuck window | lost games |
|---|---|
| failures with no earlier origin | 12 |
| no failing command (no new information); target not seen yet | 9 |
| wrong object taken | 7 |
| earlier failed command | 7 |

Steps from origin to the start of the stuck window: median 8, range 1-23.

Why the failing commands inside the windows fail (all windows): already there 416, not at the place 59, transform failed (other) 12, hands full 10, go to failed (place unknown) 8, malformed or unknown command 8, placement failed (other) 4, object not there 2, not holding that object 1

| game | task | stuck from | length | origin step | origin | the agent's next thought (for the audit) | commands in the window |
|---|---|---|---|---|---|---|---|
| new02 | clean some cloth and put it in drawer. | 9 | 15 | 2 | wrong object taken: take towel 1 from towelholder 1 | - | clean towel 1 with sinkbasin 2 x12; clean towel 1 with sinkbasin 1 x2; go to sinkbasin 1 x1 |
| new04 | clean some ladle and put it in diningtable. | 3 | 17 | - | no failing command (no new information); target not seen yet | - | look x17 |
| new05 | put a clean lettuce in countertop. | 8 | 43 | - | failures with no earlier origin | - | go to fridge 1 x41; open fridge 1 x1; close fridge 1 x1 |
| new09 | put a cool apple in garbagecan. | 19 | 32 | 4 | first failed command: go to cabinet 1 | - | go to countertop 1 x16; go to fridge 1 x16 |
| new10 | cool some apple and put it in microwave. | 2 | 49 | - | failures with no earlier origin | - | go to cabinet 1 x41; go to cabinet 2 x8 |
| new11 | cool some bread and put it in countertop. | 25 | 26 | 2 | first failed command: open toaster 1 | - | go to toaster 1 x13; go to cabinet 1 x13 |
| new12 | put a cool cup in microwave. | 7 | 44 | 3 | first failed command: go to cabinet 3 | - | go to cabinet 5 x33; go to cabinet 4 x11 |
| new13 | put a cool egg in microwave. | 9 | 42 | - | no failing command (no new information); target not seen yet | - | look x40; close fridge 1 x1; go to microwave 1 x1 |
| new14 | put a cool plate in cabinet. | 8 | 10 | 7 | wrong object taken: take bowl 1 from fridge 1 | - | go to fridge 1 x10 |
| new15 | put a cool tomato in countertop. | 10 | 41 | - | failures with no earlier origin | - | move tomato 2 to countertop 2 x30; move tomato 2 to countertop 1 x10; move tomato 2 to countertop 3 x1 |
| new18 | put a hot egg in fridge. | 14 | 37 | 2 | wrong object taken: take pot 1 from stoveburner 1 | - | go to fridge 1 x18; go to stoveburner 1 x15; take egg 4 from fridge 1 x3; open fridge 1 x1 |
| new19 | put a hot mug in cabinet. | 5 | 7 | - | failures with no earlier origin | - | heat mug 1 with microwave 1 x6; use mug 1 x1 |
| new20 | put a hot mug in coffeemachine. | 5 | 8 | - | failures with no earlier origin | - | use coffeemachine 1 x6; heat mug 1 with coffeemachine 1 x2 |
| new22 | put a hot plate in diningtable. | 7 | 12 | 3 | wrong object taken: take pan 1 from stoveburner 1 | - | heat pan 1 with stoveburner 1 x8; go to diningtable 1 x2; heat plate 1 with stoveburner 1 x1; go to stoveburner 1 x1 |
| new24 | put a hot tomato in fridge. | 4 | 47 | - | failures with no earlier origin | - | go to countertop 3 x36; go to stoveburner 1 x11 |
| new26 | clean some fork and put it in drawer. | 11 | 40 | - | failures with no earlier origin | - | go to drawer 1 x40 |
| new27 | clean some ladle and put it in countertop. | 3 | 12 | - | no failing command (no new information); target not seen yet | - | look x12 |
| new30 | put a cool pan in stoveburner. | 8 | 12 | - | no failing command (no new information); target not seen yet | - | look x11; go to stoveburner 1 x1 |
| new31 | cool some plate and put it in cabinet. | 11 | 40 | 8 | first failed command: go to countertop 1 | - | go to countertop 1 x25; go to stoveburner 1 x15 |
| new32 | cool some plate and put it in countertop. | 11 | 8 | 2 | first failed command: take plate 1 from stoveburner 1 | - | go to stoveburner 1 x3; go to countertop 1 x3; take plate 1 from countertop 1 x2 |
| new34 | put a hot potato in fridge. | 4 | 47 | - | failures with no earlier origin | - | go to stoveburner 2 x42; go to stoveburner 1 x3; go to countertop 3 x2 |
| new38 | clean some butterknife and put it in drawer. | 10 | 27 | - | failures with no earlier origin | - | go to drawer 1 x24; look x2; go to sinkbasin 1 x1 |
| new39 | put a clean dishsponge in cart. | 5 | 46 | - | failures with no earlier origin | - | go to shelf 1 x32; go to sinkbasin 1 x9; go to cart 1 x4; look x1 |
| new40 | clean some dishsponge and put it in countertop. | 3 | 12 | - | no failing command (no new information); target not seen yet | - | look x12 |
| new42 | put a clean ladle in countertop. | 3 | 48 | - | failures with no earlier origin | - | go to sinkbasin 1 x43; look x5 |
| new43 | clean some plate and put it in fridge. | 13 | 19 | - | no failing command (no new information); target not seen yet | - | look x18; go to sinkbasin 1 x1 |
| new44 | put a clean soapbar in cabinet. | 9 | 9 | - | no failing command (no new information); target not seen yet | - | look x9 |
| new45 | put a clean soapbar in toilet. | 6 | 7 | - | no failing command (no new information); target not seen yet | - | look x7 |
| new48 | cool some apple and put it in countertop. | 11 | 28 | 3 | first failed command: take apple from fridge 1 | - | look x27; go to countertop 1 x1 |
| new49 | put a cool apple in microwave. | 5 | 11 | - | no failing command (no new information); target not seen yet | - | look x11 |
| new50 | put a cool bowl in cabinet. | 15 | 36 | 6 | wrong object taken: take pot 2 from fridge 1 | - | go to fridge 1 x29; take apple 1 from fridge 1 x2; go to stoveburner 1 x2; take bread 2 from fridge 1 x2 |
| new52 | put a cool lettuce in countertop. | 4 | 47 | - | failures with no earlier origin | - | go to cabinet 1 x47 |
| new53 | put a cool mug in coffeemachine. | 18 | 7 | 14 | wrong object taken: take cup 2 from cabinet 6 | - | move cup 2 to coffeemachine 1 x4; use coffeemachine 1 x1; go to coffeemachine 1 x1; take mug 1 from coffeemachine 1 x1 |
| new55 | put a cool pot in diningtable. | 13 | 38 | 3 | wrong object taken: take pan 1 from stoveburner 2 | - | go to stoveburner 4 x30; go to diningtable 1 x3; take pot 1 from stoveburner 4 x2; go to fridge 1 x1 |
| new56 | cool some tomato and put it in microwave. | 30 | 14 | 23 | first failed command: go to cabinet 23 | - | go to cabinet 1 x7; go to sinkbasin 1 x7 |

## Stuck, w = 8

- lost games: 35; stuck: 35; won games that got stuck at some point: 3
- lost and stuck, with an origin step before the window: 16 / 35

## Repeat, k = 2

- lost games: 35; with a loop: 33; won games with a loop: 7
- lost games whose loop has an earlier origin step: 0 / 33

## Repeat, k = 3

- lost games: 35; with a loop: 32; won games with a loop: 7
- lost games whose loop has an earlier origin step: 0 / 32

| why the looped command fails | lost games | of them with an earlier origin |
|---|---|---|
| succeeds | 19 | 0 |
| already there | 7 | 0 |
| not at the place | 3 | 0 |
| malformed or unknown command | 1 | 0 |
| transform failed (other) | 1 | 0 |
| placement failed (other) | 1 | 0 |

| origin found | lost games |
|---|---|
| none | 32 |

## Repeat, k = 4

- lost games: 35; with a loop: 31; won games with a loop: 7
- lost games whose loop has an earlier origin step: 0 / 31

## Per game (k = 3)

| game | task | won | loop starts | looped command | why it fails | origin step | origin | first wrong take | target put down early |
|---|---|---|---|---|---|---|---|---|---|
| new01 | put a clean butterknife in drawer. | yes | 10 | move butterknife 2 to drawer 1 | not at the place | - | none | - | - |
| new02 | clean some cloth and put it in drawer. | no | 11 | clean towel 1 with sinkbasin 2 | not at the place | - | none | 2 | - |
| new03 | put a clean ladle in diningtable. | yes | 2 | look | succeeds | - | none | - | - |
| new04 | clean some ladle and put it in diningtable. | no | 2 | look | succeeds | - | none | - | - |
| new05 | put a clean lettuce in countertop. | no | 11 | go to fridge 1 | already there | - | none | - | - |
| new06 | clean some mug and put it in coffeemachine. | yes | - | - | - | - | - | - | - |
| new07 | put a clean plate in countertop. | yes | - | - | - | - | - | - | - |
| new08 | put a clean soapbar in drawer. | yes | 2 | look | succeeds | - | none | - | - |
| new09 | put a cool apple in garbagecan. | no | - | - | - | - | - | - | - |
| new10 | cool some apple and put it in microwave. | no | 3 | go to cabinet 1 | already there | - | none | - | - |
| new11 | cool some bread and put it in countertop. | no | - | - | - | - | - | - | - |
| new12 | put a cool cup in microwave. | no | 11 | go to cabinet 5 | succeeds | - | none | - | - |
| new13 | put a cool egg in microwave. | no | 10 | look | succeeds | - | none | - | - |
| new14 | put a cool plate in cabinet. | no | 8 | go to fridge 1 | already there | - | none | 7 | - |
| new15 | put a cool tomato in countertop. | no | 12 | move tomato 2 to countertop 2 | not at the place | - | none | - | - |
| new16 | cool some winebottle and put it in diningtable. | yes | 10 | move winebottle 1 to diningtable 1 | not at the place | - | none | - | - |
| new17 | heat some apple and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new18 | put a hot egg in fridge. | no | 35 | go to fridge 1 | succeeds | - | none | 2 | - |
| new19 | put a hot mug in cabinet. | no | 6 | heat mug 1 with microwave 1 | not at the place | - | none | - | - |
| new20 | put a hot mug in coffeemachine. | no | 7 | use coffeemachine 1 | malformed or unknown command | - | none | - | - |
| new21 | put a hot mug in sidetable. | yes | - | - | - | - | - | - | - |
| new22 | put a hot plate in diningtable. | no | 10 | heat pan 1 with stoveburner 1 | transform failed (other) | - | none | 3 | - |
| new23 | heat some tomato and put it in diningtable. | yes | - | - | - | - | - | - | - |
| new24 | put a hot tomato in fridge. | no | 26 | go to countertop 3 | succeeds | - | none | - | - |
| new25 | put a clean butterknife in diningtable. | yes | - | - | - | - | - | - | - |
| new26 | clean some fork and put it in drawer. | no | 2 | look | succeeds | - | none | - | - |
| new27 | clean some ladle and put it in countertop. | no | 2 | look | succeeds | - | none | - | - |
| new28 | clean some ladle and put it in diningtable. | yes | 2 | look | succeeds | - | none | - | - |
| new29 | cool some lettuce and put it in countertop. | yes | - | - | - | - | - | - | - |
| new30 | put a cool pan in stoveburner. | no | 7 | look | succeeds | - | none | - | - |
| new31 | cool some plate and put it in cabinet. | no | 29 | go to countertop 1 | succeeds | - | none | - | - |
| new32 | cool some plate and put it in countertop. | no | 7 | go to stoveburner 3 | already there | - | none | - | - |
| new33 | heat some egg and put it in countertop. | yes | - | - | - | - | - | - | - |
| new34 | put a hot potato in fridge. | no | 9 | go to stoveburner 2 | succeeds | - | none | - | - |
| new35 | heat some tomato and put it in fridge. | yes | - | - | - | - | - | - | - |
| new36 | heat some tomato and put it in fridge. | yes | - | - | - | - | - | - | - |
| new37 | put a clean butterknife in countertop. | yes | - | - | - | - | - | - | - |
| new38 | clean some butterknife and put it in drawer. | no | 2 | look | succeeds | - | none | - | - |
| new39 | put a clean dishsponge in cart. | no | 32 | go to shelf 1 | succeeds | - | none | - | - |
| new40 | clean some dishsponge and put it in countertop. | no | 2 | look | succeeds | - | none | - | - |
| new41 | put a clean fork in countertop. | yes | - | - | - | - | - | - | - |
| new42 | put a clean ladle in countertop. | no | 2 | look | succeeds | - | none | - | - |
| new43 | clean some plate and put it in fridge. | no | 2 | look | succeeds | - | none | - | - |
| new44 | put a clean soapbar in cabinet. | no | 2 | look | succeeds | - | none | - | - |
| new45 | put a clean soapbar in toilet. | no | 1 | look | succeeds | - | none | - | - |
| new46 | put a clean soapbar in toilet. | yes | 2 | look | succeeds | - | none | - | - |
| new47 | clean some tomato and put it in countertop. | yes | 2 | look | succeeds | - | none | - | - |
| new48 | cool some apple and put it in countertop. | no | 10 | look | succeeds | - | none | - | - |
| new49 | put a cool apple in microwave. | no | 4 | look | succeeds | - | none | - | - |
| new50 | put a cool bowl in cabinet. | no | 26 | go to fridge 1 | already there | - | none | 6 | - |
| new51 | put a cool cup in sidetable. | yes | - | - | - | - | - | - | - |
| new52 | put a cool lettuce in countertop. | no | 4 | go to cabinet 1 | already there | - | none | - | - |
| new53 | put a cool mug in coffeemachine. | no | 20 | move cup 2 to coffeemachine 1 | placement failed (other) | - | none | 14 | - |
| new54 | cool some pan and put it in stoveburner. | yes | - | - | - | - | - | - | - |
| new55 | put a cool pot in diningtable. | no | 17 | go to stoveburner 4 | already there | - | none | 3 | - |
| new56 | cool some tomato and put it in microwave. | no | - | - | - | - | - | - | - |
