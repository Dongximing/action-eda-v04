# u097 / react_dep_t1536: the controller's ledger at every step

Task: heat some apple and put it in fridge.  |  result: won in 9 steps

Evidence levels: 有证据 = a game reply says so; 没证据 = only assumed; 被否定 = a game reply contradicts it; 已排除 = chosen as a culprit and ruled out.

## Step 1

- agent's command: `open fridge 1`
- game reply: Nothing happens.
- this command depends on: "you are at fridge 1" 没证据
- **decision after the reply:** This failed. It needs "you are at fridge 1", which no feedback supports: you have not gone anywhere yet.
- ledger after step 1: at **(start)** (step 0), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 2

- agent's command: `go to fridge 1`
- game reply: You arrive at fridge 1. The fridge 1 is closed.
- ledger after step 2: at **fridge 1** (step 2), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 3

- agent's command: `open fridge 1`
- game reply: You open the fridge 1. The fridge 1 is open. In it, you see a apple 1, a bowl 3, a cup 2, a cup 1, a egg 3, a lettuce 1, a potato 2, a potato 1, and a tomato 1.
- this command depends on: "you are at fridge 1" 有证据
- ledger after step 3: at **fridge 1** (step 2), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 4

- agent's command: `take apple 1 from fridge 1`
- game reply: You pick up the apple 1 from the fridge 1.
- this command depends on: "you are at fridge 1" 有证据; "your hands are empty" 有证据; "apple 1 is in/on fridge 1" 有证据
- ledger after step 4: at **fridge 1** (step 2), holding **apple 1** (step 4); taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: -; tools that worked: -; ruled out: -

## Step 5

- agent's command: `go to microwave 1`
- game reply: You arrive at microwave 1. The microwave 1 is closed.
- ledger after step 5: at **microwave 1** (step 5), holding **apple 1** (step 4); taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: -; tools that worked: -; ruled out: -

## Step 6

- agent's command: `open microwave 1`
- game reply: You open the microwave 1. The microwave 1 is open. In it, you see a egg 2.
- this command depends on: "you are at microwave 1" 有证据
- ledger after step 6: at **microwave 1** (step 5), holding **apple 1** (step 4); taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: -; tools that worked: -; ruled out: -

## Step 7

- agent's command: `heat apple 1 with microwave 1`
- game reply: You heat the apple 1 using the microwave 1.
- this command depends on: "you are holding apple 1" 有证据; "you are at microwave 1" 有证据; "apple 1 is the apple the task asks for" 有证据; "a microwave can heat things" 没证据
- ledger after step 7: at **microwave 1** (step 5), holding **apple 1** (step 4); taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: apple 1: heat (step 7); tools that worked: a microwave can heat things (step 7); ruled out: -

## Step 8

- agent's command: `go to fridge 1`
- game reply: You arrive at fridge 1. The fridge 1 is open. In it, you see a bowl 3, a cup 2, a cup 1, a egg 3, a lettuce 1, a potato 2, a potato 1, and a tomato 1.
- ledger after step 8: at **fridge 1** (step 8), holding **apple 1** (step 4); taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: apple 1: heat (step 7); tools that worked: a microwave can heat things (step 7); ruled out: -

## Step 9

- agent's command: `move apple 1 to fridge 1`
- game reply: You move the apple 1 to the fridge 1.
- this command depends on: "you are holding apple 1" 有证据; "you are at fridge 1" 有证据; "fridge 1 is open" 有证据; "apple 1 is the apple the task asks for" 有证据; "apple 1 has been heated" 有证据
- ledger after step 9: at **fridge 1** (step 8), holding **nothing**; taken for the task: apple 1 is the apple the task asks for [有证据, step 4]; done: apple 1: heat (step 7); tools that worked: a microwave can heat things (step 7); ruled out: -

