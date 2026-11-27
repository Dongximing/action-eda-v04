# jevexplore: every step of the 12 d1 games

Note = the visited / not-visited list OneJev kept, shown after the latest observation. 'visited' means the agent arrived there, not that it looked inside.

## game01: heat some mug and put it in cabinet. | WON in 33 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a egg 3, a knife 2 |
| 2 | 1 | - | take mug 3 from countertop 1 | You pick up the mug 3 from the countertop 1. |
| 3 | 1 | - | go to microwave 1 | You arrive at microwave 1. The microwave 1 is closed. |
| 4 | 2 | microwave 1 | heat mug 3 with microwave 1 | You heat the mug 3 using the microwave 1. |
| 5 | 2 | microwave 1 | go to cabinet 1 | You arrive at cabinet 1. On the cabinet 1, you see nothing. |
| 6 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 7 | 3 | microwave 1 | close cabinet 1 | Nothing happens. |
| 8 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 9 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 10 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 11 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 12 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 13 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 14 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 15 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 16 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 17 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 18 | 3 | microwave 1 | open cabinet 1 | Nothing happens. |
| 19 | 3 | microwave 1 | open cabinet 10 | Nothing happens. |
| 20 | 4 | microwave 1 | open cabinet 10 | Nothing happens. |
| 21 | 4 | microwave 1 | open cabinet 10 | Nothing happens. |
| 22 | 4 | microwave 1 | open cabinet 10 | Nothing happens. |
| 23 | 4 | microwave 1 | open cabinet 2 | Nothing happens. |
| 24 | 5 | microwave 1 | open cabinet 2 | Nothing happens. |
| 25 | 5 | microwave 1 | open cabinet 3 | Nothing happens. |
| 26 | 6 | microwave 1 | open cabinet 4 | Nothing happens. |
| 27 | 7 | microwave 1 | open cabinet 5 | Nothing happens. |
| 28 | 8 | microwave 1 | open cabinet 6 | Nothing happens. |
| 29 | 9 | microwave 1 | open cabinet 7 | Nothing happens. |
| 30 | 10 | microwave 1 | open cabinet 8 | Nothing happens. |
| 31 | 11 | microwave 1 | go to cabinet 9 | You arrive at cabinet 9. The cabinet 9 is closed. |
| 32 | 12 | microwave 1, cabinet 9 | open cabinet 9 | You open the cabinet 9. The cabinet 9 is open. In it, you see nothing. |
| 33 | 12 | microwave 1 | move mug 3 to cabinet 9 | You move the mug 3 to the cabinet 9. |

## game02: put a hot cup in cabinet. | lost in 50 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to coffeemachine 1 | You arrive at coffeemachine 1. On the coffeemachine 1, you see a mug 1. |
| 2 | 1 | - | take mug 1 from coffeemachine 1 | You pick up the mug 1 from the coffeemachine 1. |
| 3 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 4 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 5 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 6 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 7 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 8 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 9 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 10 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 11 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 12 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 13 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 14 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 15 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 16 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 17 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 18 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 19 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 20 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 21 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 22 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 23 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 24 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 25 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 26 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 27 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 28 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 29 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 30 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 31 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 32 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 33 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 34 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 35 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 36 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 37 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 38 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 39 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 40 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 41 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 42 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 43 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 44 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 45 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 46 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 47 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 48 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 49 | 1 | - | go to coffeemachine 1 | Nothing happens. |
| 50 | 1 | - | go to coffeemachine 1 | Nothing happens. |

## game03: put a clean butterknife in drawer. | WON in 37 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to drawer 1 | You arrive at drawer 1. The drawer 1 is closed. |
| 2 | 1 | drawer 1 | open drawer 1 | You open the drawer 1. The drawer 1 is open. In it, you see nothing. |
| 3 | 1 | - | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a housepl |
| 4 | 2 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 5 | 3 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see nothing. |
| 6 | 3 | - | go to cabinet 2 | You arrive at cabinet 2. The cabinet 2 is closed. |
| 7 | 4 | cabinet 2 | open cabinet 2 | You open the cabinet 2. The cabinet 2 is open. In it, you see nothing. |
| 8 | 4 | - | go to drawer 2 | You arrive at drawer 2. The drawer 2 is closed. |
| 9 | 5 | drawer 2 | go to drawer 3 | You arrive at drawer 3. The drawer 3 is closed. |
| 10 | 6 | drawer 2, drawer 3 | go to drawer 4 | You arrive at drawer 4. The drawer 4 is closed. |
| 11 | 7 | drawer 2, drawer 3, drawer 4 | go to drawer 5 | Nothing happens. |
| 12 | 8 | drawer 2, drawer 3, drawer 4 | go to drawer 6 | You arrive at drawer 6. The drawer 6 is closed. |
| 13 | 9 | drawer 2, drawer 3, drawer 4, drawer 6 | go to drawer 7 | You arrive at drawer 7. The drawer 7 is closed. |
| 14 | 10 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7 | go to drawer 8 | You arrive at drawer 8. The drawer 8 is closed. |
| 15 | 11 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8 | go to cabinet 3 | You arrive at cabinet 3. The cabinet 3 is closed. |
| 16 | 12 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3 | go to cabinet 4 | You arrive at cabinet 4. The cabinet 4 is closed. |
| 17 | 13 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4 | go to cabinet 5 | You arrive at cabinet 5. The cabinet 5 is closed. |
| 18 | 14 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5 | go to cabinet 6 | You arrive at cabinet 6. The cabinet 6 is closed. |
| 19 | 15 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6 | go to cabinet 7 | You arrive at cabinet 7. The cabinet 7 is closed. |
| 20 | 16 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7 | go to cabinet 8 | Nothing happens. |
| 21 | 17 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7 | go to cabinet 9 | You arrive at cabinet 9. The cabinet 9 is closed. |
| 22 | 18 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9 | go to drawer 9 | You arrive at drawer 9. The drawer 9 is closed. |
| 23 | 19 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a housepl |
| 24 | 19 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9 | go to drawer 10 | You arrive at drawer 10. The drawer 10 is closed. |
| 25 | 20 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a housepl |
| 26 | 20 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10 | go to drawer 11 | You arrive at drawer 11. The drawer 11 is closed. |
| 27 | 21 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a housepl |
| 28 | 21 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a spatula 1, a spoon |
| 29 | 22 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11 | go to drawer 12 | You arrive at drawer 12. The drawer 12 is closed. |
| 30 | 23 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a housepl |
| 31 | 23 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a pot 2. |
| 32 | 24 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | go to countertop 2 | You arrive at countertop 2. On the countertop 2, you see a butterknife 1, a |
| 33 | 25 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | take butterknife 1 from countertop 2 | You pick up the butterknife 1 from the countertop 2. |
| 34 | 25 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a spatula 1, a spoon |
| 35 | 25 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | clean butterknife 1 with sinkbasin 1 | You clean the butterknife 1 using the sinkbasin 1. |
| 36 | 25 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | go to drawer 1 | You arrive at drawer 1. The drawer 1 is open. In it, you see nothing. |
| 37 | 25 | drawer 2, drawer 3, drawer 4, drawer 6, drawer 7, drawer 8, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 9, drawer 9, drawer 10, drawer 11, drawer 12 | move butterknife 1 to drawer 1 | You move the butterknife 1 to the drawer 1. |

## game04: put a cool tomato in microwave. | WON in 15 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 2 | 1 | fridge 1 | open fridge 1 | You open the fridge 1. The fridge 1 is open. In it, you see nothing. |
| 3 | 1 | - | look | You are facing the fridge 1. Next to it, you see nothing. |
| 4 | 1 | - | look | You are facing the fridge 1. Next to it, you see nothing. |
| 5 | 1 | - | look | You are facing the fridge 1. Next to it, you see nothing. |
| 6 | 1 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 7 | 2 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see nothing. |
| 8 | 2 | - | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see nothing. |
| 9 | 3 | - | go to countertop 2 | You arrive at countertop 2. On the countertop 2, you see a bread 2, a butte |
| 10 | 4 | - | take tomato 1 from countertop 2 | You pick up the tomato 1 from the countertop 2. |
| 11 | 4 | - | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see nothing. |
| 12 | 4 | - | cool tomato 1 with fridge 1 | You cool the tomato 1 using the fridge 1. |
| 13 | 4 | - | go to microwave 1 | You arrive at microwave 1. The microwave 1 is closed. |
| 14 | 5 | microwave 1 | open microwave 1 | You open the microwave 1. The microwave 1 is open. In it, you see a apple 1 |
| 15 | 5 | - | move tomato 1 to microwave 1 | You move the tomato 1 to the microwave 1. |

## game05: put a cool tomato in countertop. | lost in 50 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a mug 2,  |
| 2 | 1 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 3 | 2 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see nothing. |
| 4 | 2 | - | go to cabinet 2 | You arrive at cabinet 2. The cabinet 2 is closed. |
| 5 | 3 | cabinet 2 | go to cabinet 3 | You arrive at cabinet 3. The cabinet 3 is closed. |
| 6 | 4 | cabinet 2, cabinet 3 | go to cabinet 4 | You arrive at cabinet 4. On the cabinet 4, you see nothing. |
| 7 | 5 | cabinet 2, cabinet 3 | go to cabinet 5 | You arrive at cabinet 5. On the cabinet 5, you see a bowl 1. |
| 8 | 6 | cabinet 2, cabinet 3 | go to cabinet 6 | You arrive at cabinet 6. The cabinet 6 is closed. |
| 9 | 7 | cabinet 2, cabinet 3, cabinet 6 | go to cabinet 7 | You arrive at cabinet 7. The cabinet 7 is closed. |
| 10 | 8 | cabinet 2, cabinet 3, cabinet 6, cabinet 7 | go to cabinet 8 | You arrive at cabinet 8. The cabinet 8 is closed. |
| 11 | 9 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8 | go to cabinet 9 | You arrive at cabinet 9. The cabinet 9 is closed. |
| 12 | 10 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9 | go to cabinet 10 | You arrive at cabinet 10. The cabinet 10 is closed. |
| 13 | 11 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10 | go to cabinet 11 | You arrive at cabinet 11. The cabinet 11 is closed. |
| 14 | 12 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11 | go to cabinet 12 | You arrive at cabinet 12. The cabinet 12 is closed. |
| 15 | 13 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12 | go to cabinet 13 | You arrive at cabinet 13. The cabinet 13 is closed. |
| 16 | 14 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13 | go to cabinet 14 | Nothing happens. |
| 17 | 15 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13 | go to cabinet 15 | You arrive at cabinet 15. The cabinet 15 is closed. |
| 18 | 16 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15 | go to cabinet 16 | You arrive at cabinet 16. On the cabinet 16, you see nothing. |
| 19 | 17 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15 | go to cabinet 17 | You arrive at cabinet 17. On the cabinet 17, you see a saltshaker 2. |
| 20 | 18 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15 | go to cabinet 18 | You arrive at cabinet 18. The cabinet 18 is closed. |
| 21 | 19 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18 | go to cabinet 19 | You arrive at cabinet 19. The cabinet 19 is closed. |
| 22 | 20 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 23 | 21 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19, fridge 1 | open fridge 1 | You open the fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cup |
| 24 | 21 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a cup 1, a mug 2,  |
| 25 | 21 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 26 | 22 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to countertop 3 | You arrive at countertop 3. On the countertop 3, you see a fork 1, a knife  |
| 27 | 23 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 28 | 23 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to countertop 2 | You arrive at countertop 2. On the countertop 2, you see a bread 1, a butte |
| 29 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 30 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 31 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 32 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 33 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 34 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 35 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 36 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 37 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 38 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 39 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 40 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 41 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 42 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 43 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 44 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 45 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 46 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 47 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 48 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 2, a cu |
| 49 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a apple 1. |
| 50 | 24 | cabinet 2, cabinet 3, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 15, cabinet 18, cabinet 19 | go to countertop 3 | You arrive at countertop 3. On the countertop 3, you see a fork 1, a knife  |

## game06: put a hot plate in cabinet. | lost in 50 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a butterknife 2, a |
| 2 | 1 | - | take pan 1 from countertop 1 | You pick up the pan 1 from the countertop 1. |
| 3 | 1 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 4 | 2 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see nothing. |
| 5 | 2 | - | heat pan 1 with stoveburner 1 | Nothing happens. |
| 6 | 3 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a kettle 1. |
| 7 | 3 | - | heat pan 1 with stoveburner 1 | Nothing happens. |
| 8 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 9 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 10 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 11 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 12 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 13 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 14 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 15 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 16 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 17 | 3 | - | go to stoveburner 1 | Nothing happens. |
| 18 | 3 | - | heat pan 1 with stoveburner 1 | Nothing happens. |
| 19 | 3 | - | heat pan 1 with stoveburner 1 | Nothing happens. |
| 20 | 3 | - | go to stoveburner 2 | Nothing happens. |
| 21 | 4 | - | go to stoveburner 3 | You arrive at stoveburner 3. On the stoveburner 3, you see nothing. |
| 22 | 5 | - | heat pan 1 with stoveburner 3 | Nothing happens. |
| 23 | 5 | - | go to stoveburner 4 | Nothing happens. |
| 24 | 6 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a kettle 1. |
| 25 | 6 | - | go to stoveburner 3 | You arrive at stoveburner 3. On the stoveburner 3, you see nothing. |
| 26 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 27 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 28 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 29 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 30 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 31 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 32 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 33 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 34 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 35 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 36 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 37 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 38 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 39 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 40 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 41 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 42 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 43 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 44 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 45 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 46 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 47 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 48 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 49 | 6 | - | go to stoveburner 3 | Nothing happens. |
| 50 | 6 | - | go to stoveburner 3 | Nothing happens. |

## game07: cool some tomato and put it in garbagecan. | WON in 25 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 2 | 1 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see a peppershake |
| 3 | 1 | - | go to cabinet 2 | You arrive at cabinet 2. The cabinet 2 is closed. |
| 4 | 2 | cabinet 2 | go to cabinet 3 | You arrive at cabinet 3. The cabinet 3 is closed. |
| 5 | 3 | cabinet 2, cabinet 3 | go to cabinet 4 | You arrive at cabinet 4. The cabinet 4 is closed. |
| 6 | 4 | cabinet 2, cabinet 3, cabinet 4 | go to cabinet 5 | You arrive at cabinet 5. The cabinet 5 is closed. |
| 7 | 5 | cabinet 2, cabinet 3, cabinet 4, cabinet 5 | go to cabinet 6 | You arrive at cabinet 6. The cabinet 6 is closed. |
| 8 | 6 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6 | go to cabinet 7 | You arrive at cabinet 7. The cabinet 7 is closed. |
| 9 | 7 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7 | go to cabinet 8 | You arrive at cabinet 8. The cabinet 8 is closed. |
| 10 | 8 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8 | go to cabinet 9 | You arrive at cabinet 9. The cabinet 9 is closed. |
| 11 | 9 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9 | go to cabinet 10 | You arrive at cabinet 10. The cabinet 10 is closed. |
| 12 | 10 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10 | go to cabinet 11 | You arrive at cabinet 11. The cabinet 11 is closed. |
| 13 | 11 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11 | go to cabinet 12 | You arrive at cabinet 12. The cabinet 12 is closed. |
| 14 | 12 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12 | go to cabinet 13 | You arrive at cabinet 13. The cabinet 13 is closed. |
| 15 | 13 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13 | go to cabinet 14 | You arrive at cabinet 14. The cabinet 14 is closed. |
| 16 | 14 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14 | go to cabinet 15 | You arrive at cabinet 15. The cabinet 15 is closed. |
| 17 | 15 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a fork 1. |
| 18 | 16 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | go to countertop 2 | You arrive at countertop 2. On the countertop 2, you see a apple 2, a apple |
| 19 | 17 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | go to countertop 3 | You arrive at countertop 3. On the countertop 3, you see a bread 1, a fork  |
| 20 | 18 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | go to countertop 4 | You arrive at countertop 4. On the countertop 4, you see a apple 3, a bread |
| 21 | 19 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | take tomato 2 from countertop 4 | You pick up the tomato 2 from the countertop 4. |
| 22 | 19 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 23 | 20 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15, fridge 1 | cool tomato 2 with fridge 1 | You cool the tomato 2 using the fridge 1. |
| 24 | 20 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15, fridge 1 | go to garbagecan 1 | You arrive at garbagecan 1. On the garbagecan 1, you see a tomato 1. |
| 25 | 21 | cabinet 2, cabinet 3, cabinet 4, cabinet 5, cabinet 6, cabinet 7, cabinet 8, cabinet 9, cabinet 10, cabinet 11, cabinet 12, cabinet 13, cabinet 14, cabinet 15, fridge 1 | move tomato 2 to garbagecan 1 | You move the tomato 2 to the garbagecan 1. |

## game08: clean some spatula and put it in diningtable. | WON in 7 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a bread 2, a bre |
| 2 | 1 | - | take spatula 2 from diningtable 1 | You pick up the spatula 2 from the diningtable 1. |
| 3 | 1 | - | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a cup 2, a fork 2, a |
| 4 | 2 | - | clean spatula 2 with sinkbasin 1 | You clean the spatula 2 using the sinkbasin 1. |
| 5 | 2 | - | move spatula 2 to diningtable 1 | Nothing happens. |
| 6 | 2 | - | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a bread 2, a bre |
| 7 | 2 | - | move spatula 2 to diningtable 1 | You move the spatula 2 to the diningtable 1. |

## game09: put a hot potato in fridge. | WON in 14 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a pot 1. |
| 2 | 1 | - | go to countertop 3 | You arrive at countertop 3. On the countertop 3, you see a bowl 2, a bread  |
| 3 | 2 | - | take potato 1 from countertop 3 | You pick up the potato 1 from the countertop 3. |
| 4 | 2 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a pot 1. |
| 5 | 2 | - | heat potato 1 with stoveburner 1 | Nothing happens. |
| 6 | 2 | - | go to stoveburner 2 | Nothing happens. |
| 7 | 3 | - | go to stoveburner 3 | You arrive at stoveburner 3. On the stoveburner 3, you see a pot 2. |
| 8 | 4 | - | go to stoveburner 4 | Nothing happens. |
| 9 | 5 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see a pot 1. |
| 10 | 5 | - | go to microwave 1 | You arrive at microwave 1. The microwave 1 is closed. |
| 11 | 6 | microwave 1 | heat potato 1 with microwave 1 | You heat the potato 1 using the microwave 1. |
| 12 | 6 | microwave 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 13 | 7 | microwave 1, fridge 1 | open fridge 1 | You open the fridge 1. The fridge 1 is open. In it, you see a apple 1, a bo |
| 14 | 7 | microwave 1 | move potato 1 to fridge 1 | You move the potato 1 to the fridge 1. |

## game10: clean some lettuce and put it in fridge. | WON in 49 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 2 | 1 | - | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 3 | 1 | - | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 4 | 1 | - | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 5 | 1 | - | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 6 | 2 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 7 | 2 | fridge 1 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a cup 1, a spoon 1,  |
| 8 | 3 | fridge 1 | look | You are facing the sinkbasin 1. Next to it, you see nothing. |
| 9 | 3 | fridge 1 | look | You are facing the sinkbasin 1. Next to it, you see nothing. |
| 10 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 11 | 3 | fridge 1 | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 12 | 3 | fridge 1 | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 13 | 3 | fridge 1 | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 14 | 3 | fridge 1 | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 15 | 3 | fridge 1 | look | You are facing the diningtable 1. Next to it, you see nothing. |
| 16 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 17 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 18 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 19 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 20 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 21 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 22 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 23 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 24 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 25 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 26 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 27 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 28 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 29 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 30 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 31 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 32 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 33 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 34 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 35 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 36 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 37 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 38 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 39 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 40 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 41 | 3 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a apple 1, a but |
| 42 | 3 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 43 | 3 | fridge 1 | go to countertop 1 | You arrive at countertop 1. On the countertop 1, you see a bread 1, a butte |
| 44 | 4 | fridge 1 | take lettuce 1 from countertop 1 | You pick up the lettuce 1 from the countertop 1. |
| 45 | 4 | fridge 1 | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see a cup 1, a spoon 1,  |
| 46 | 4 | fridge 1 | clean lettuce 1 with sinkbasin 1 | You clean the lettuce 1 using the sinkbasin 1. |
| 47 | 4 | fridge 1 | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 48 | 4 | fridge 1 | open fridge 1 | You open the fridge 1. The fridge 1 is open. In it, you see a bowl 1, and a |
| 49 | 4 | - | move lettuce 1 to fridge 1 | You move the lettuce 1 to the fridge 1. |

## game11: put a clean cloth in cabinet. | lost in 50 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to towelholder 1 | You arrive at towelholder 1. On the towelholder 1, you see a towel 1. |
| 2 | 1 | - | take towel 1 from towelholder 1 | You pick up the towel 1 from the towelholder 1. |
| 3 | 1 | - | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see nothing. |
| 4 | 2 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 5 | 2 | - | go to cabinet 1 | You arrive at cabinet 1. The cabinet 1 is closed. |
| 6 | 3 | cabinet 1 | open cabinet 1 | You open the cabinet 1. The cabinet 1 is open. In it, you see a soapbottle  |
| 7 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 8 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 9 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 10 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 11 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 12 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 13 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 14 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 15 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 16 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 17 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 18 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 19 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 20 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 21 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 22 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 23 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 24 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 25 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 26 | 3 | - | clean towel 1 with sinkbasin 1 | Nothing happens. |
| 27 | 3 | - | go to bathtubbasin 1 | You arrive at bathtubbasin 1. On the bathtubbasin 1, you see a cloth 2, and |
| 28 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 29 | 4 | - | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see nothing. |
| 30 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 31 | 4 | - | go to bathtubbasin 1 | You arrive at bathtubbasin 1. On the bathtubbasin 1, you see a cloth 2, and |
| 32 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 33 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 34 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 35 | 4 | - | go to sinkbasin 1 | You arrive at sinkbasin 1. On the sinkbasin 1, you see nothing. |
| 36 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 37 | 4 | - | go to bathtubbasin 1 | You arrive at bathtubbasin 1. On the bathtubbasin 1, you see a cloth 2, and |
| 38 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 39 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 40 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 41 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 42 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 43 | 4 | - | go to towelholder 1 | You arrive at towelholder 1. On the towelholder 1, you see nothing. |
| 44 | 4 | - | go to bathtubbasin 1 | You arrive at bathtubbasin 1. On the bathtubbasin 1, you see a cloth 2, and |
| 45 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |
| 46 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 47 | 4 | - | go to bathtubbasin 1 | Nothing happens. |
| 48 | 4 | - | go to towelholder 1 | You arrive at towelholder 1. On the towelholder 1, you see nothing. |
| 49 | 4 | - | go to bathtubbasin 1 | You arrive at bathtubbasin 1. On the bathtubbasin 1, you see a cloth 2, and |
| 50 | 4 | - | take cloth 2 from bathtubbasin 1 | Nothing happens. |

## game12: cool some pan and put it in diningtable. | WON in 9 steps

| step | note: visited (count) | places reached but never opened, counted as visited | action | feedback |
|---|---|---|---|---|
| 1 | 0 | - | go to stoveburner 1 | You arrive at stoveburner 1. On the stoveburner 1, you see nothing. |
| 2 | 1 | - | go to stoveburner 2 | You arrive at stoveburner 2. On the stoveburner 2, you see a kettle 1. |
| 3 | 2 | - | go to stoveburner 3 | You arrive at stoveburner 3. On the stoveburner 3, you see a pot 2. |
| 4 | 3 | - | go to stoveburner 4 | You arrive at stoveburner 4. On the stoveburner 4, you see a pan 1. |
| 5 | 4 | - | take pan 1 from stoveburner 4 | You pick up the pan 1 from the stoveburner 4. |
| 6 | 4 | - | go to fridge 1 | You arrive at fridge 1. The fridge 1 is closed. |
| 7 | 5 | fridge 1 | cool pan 1 with fridge 1 | You cool the pan 1 using the fridge 1. |
| 8 | 5 | fridge 1 | go to diningtable 1 | You arrive at diningtable 1. On the diningtable 1, you see a book 1, a brea |
| 9 | 6 | fridge 1 | move pan 1 to diningtable 1 | You move the pan 1 to the diningtable 1. |

