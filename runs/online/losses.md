# Where lost games get stuck (llm and baseline)

## llm: 40 lost games, 2000 steps

| stage reached | games |
|---|---|
| not_found | 22 |
| found | 0 |
| wrong_object | 16 |
| taken | 1 |
| transformed | 1 |

| wasted steps | steps | share of all steps |
|---|---|---|
| "Nothing happens" | 747 | 37% |
| repeated look / inventory | 323 | 16% |
| after the last new observation | 1071 | 54% |

Games with the same action 10+ times in a row: 28/40; with a stuck tail of 20+ steps: 27/40; with a closed receptacle reached but never opened: 12/40.

## baseline (same games, lost there too): 40 lost games, 2000 steps

| stage reached | games |
|---|---|
| not_found | 22 |
| found | 0 |
| wrong_object | 16 |
| taken | 1 |
| transformed | 1 |

| wasted steps | steps | share of all steps |
|---|---|---|
| "Nothing happens" | 726 | 36% |
| repeated look / inventory | 345 | 17% |
| after the last new observation | 1038 | 52% |

Games with the same action 10+ times in a row: 28/40; with a stuck tail of 20+ steps: 28/40; with a closed receptacle reached but never opened: 10/40.

## Per game

| game | task | stage | wrong object | Nothing happens | stuck tail | longest repeat | baseline stage |
|---|---|---|---|---|---|---|---|
| game02 | put a hot cup in cabinet. | wrong_object | mug 1 | 45 | 44 | 44x `go to cabinet 1` | wrong_object |
| game03 | put a clean butterknife in drawer. | not_found | - | 1 | 0 | 9x `look` | not_found |
| game04 | put a cool tomato in microwave. | not_found | - | 0 | 30 | 5x `look` | not_found |
| game05 | put a cool tomato in countertop. | not_found | - | 0 | 29 | 1x `go to countertop 1` | not_found |
| game06 | put a hot plate in cabinet. | wrong_object | kettle 1 | 42 | 42 | 42x `go to stoveburner 1` | wrong_object |
| game07 | cool some tomato and put it in garbagecan. | transformed | - | 0 | 0 | 1x `go to cabinet 1` | transformed |
| game10 | clean some lettuce and put it in fridge. | not_found | - | 0 | 24 | 20x `look` | not_found |
| game11 | put a clean cloth in cabinet. | wrong_object | towel 1 | 31 | 13 | 23x `clean towel 1 with sinkbasin 1` | wrong_object |
| new02 | clean some cloth and put it in drawer. | wrong_object | towel 1 | 25 | 39 | 5x `go to drawer 1` | wrong_object |
| new04 | clean some ladle and put it in diningtable. | wrong_object | spoon 3 | 17 | 26 | 18x `look` | wrong_object |
| new05 | put a clean lettuce in countertop. | not_found | - | 40 | 39 | 40x `go to fridge 1` | not_found |
| new09 | put a cool apple in garbagecan. | not_found | - | 4 | 32 | 2x `go to cabinet 2` | not_found |
| new10 | cool some apple and put it in microwave. | not_found | - | 49 | 48 | 12x `go to cabinet 1` | not_found |
| new11 | cool some bread and put it in countertop. | not_found | - | 1 | 26 | 1x `go to toaster 1` | not_found |
| new12 | put a cool cup in microwave. | not_found | - | 24 | 44 | 10x `go to cabinet 5` | not_found |
| new13 | put a cool egg in microwave. | not_found | - | 0 | 42 | 32x `look` | not_found |
| new14 | put a cool plate in cabinet. | wrong_object | bowl 1 | 37 | 27 | 28x `close cabinet 12` | wrong_object |
| new18 | put a hot egg in fridge. | wrong_object | pot 1 | 5 | 37 | 4x `go to fridge 1` | wrong_object |
| new20 | put a hot mug in coffeemachine. | taken | - | 21 | 32 | 5x `use coffeemachine 1` | taken |
| new22 | put a hot plate in diningtable. | wrong_object | pan 1 | 40 | 42 | 21x `heat pan 1 with stoveburner 1` | wrong_object |
| new24 | put a hot tomato in fridge. | not_found | - | 24 | 23 | 25x `go to countertop 3` | not_found |
| new26 | clean some fork and put it in drawer. | not_found | - | 40 | 39 | 41x `go to drawer 1` | not_found |
| new30 | put a cool pan in stoveburner. | wrong_object | pot 1 | 24 | 23 | 20x `reset` | wrong_object |
| new31 | cool some plate and put it in cabinet. | not_found | - | 12 | 40 | 11x `go to countertop 1` | not_found |
| new32 | cool some plate and put it in countertop. | wrong_object | pan 1 | 9 | 0 | 18x `look` | wrong_object |
| new34 | put a hot potato in fridge. | not_found | - | 41 | 40 | 42x `go to stoveburner 2` | not_found |
| new38 | clean some butterknife and put it in drawer. | not_found | - | 37 | 13 | 24x `go to drawer 1` | not_found |
| new39 | put a clean dishsponge in cart. | not_found | - | 18 | 17 | 19x `go to shelf 1` | not_found |
| new40 | clean some dishsponge and put it in countertop. | wrong_object | cloth 2 | 5 | 6 | 13x `look` | wrong_object |
| new42 | put a clean ladle in countertop. | not_found | - | 43 | 42 | 43x `go to sinkbasin 1` | not_found |
| new43 | clean some plate and put it in fridge. | not_found | - | 0 | 18 | 18x `look` | not_found |
| new44 | put a clean soapbar in cabinet. | wrong_object | soapbottle 2 | 1 | 0 | 10x `look` | wrong_object |
| new45 | put a clean soapbar in toilet. | wrong_object | soapbottle 1 | 1 | 32 | 8x `look` | wrong_object |
| new48 | cool some apple and put it in countertop. | not_found | - | 2 | 11 | 28x `look` | not_found |
| new49 | put a cool apple in microwave. | not_found | - | 1 | 18 | 13x `look` | not_found |
| new50 | put a cool bowl in cabinet. | wrong_object | pot 2 | 11 | 36 | 11x `go to fridge 1` | wrong_object |
| new52 | put a cool lettuce in countertop. | not_found | - | 47 | 46 | 47x `go to cabinet 1` | not_found |
| new53 | put a cool mug in coffeemachine. | wrong_object | cup 2 | 19 | 7 | 3x `move cup 2 to coffeemachine 1` | wrong_object |
| new55 | put a cool pot in diningtable. | wrong_object | pan 1 | 29 | 38 | 16x `go to stoveburner 4` | wrong_object |
| new56 | cool some tomato and put it in microwave. | not_found | - | 1 | 6 | 1x `go to cabinet 1` | not_found |
