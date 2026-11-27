# u013 / react_dep_t1536: the controller's ledger at every step

Task: look at mug under the desklamp.  |  result: won in 18 steps

Evidence levels: 有证据 = a game reply says so; 没证据 = only assumed; 被否定 = a game reply contradicts it; 已排除 = chosen as a culprit and ruled out.

## Step 1

- agent's command: `go to drawer 1`
- game reply: You arrive at drawer 1. The drawer 1 is closed.
- ledger after step 1: at **drawer 1** (step 1), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 2

- agent's command: `open drawer 1`
- game reply: You open the drawer 1. The drawer 1 is open. In it, you see a creditcard 2.
- this command depends on: "you are at drawer 1" 有证据
- ledger after step 2: at **drawer 1** (step 1), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 3

- agent's command: `go to drawer 2`
- game reply: You arrive at drawer 2. On the drawer 2, you see a cd 1.
- ledger after step 3: at **drawer 2** (step 3), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 4

- agent's command: `open drawer 2`
- game reply: Nothing happens.
- this command depends on: "you are at drawer 2" 有证据
- ledger after step 4: at **drawer 2** (step 3), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 5

- agent's command: `go to drawer 3`
- game reply: Nothing happens.
- ledger after step 5: at **drawer 2** (step 3), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 6

- agent's command: `go to desk 1`
- game reply: You arrive at desk 1. On the desk 1, you see a creditcard 1, a desklamp 1, a laptop 1, a pencil 2, and a pencil 1.
- ledger after step 6: at **desk 1** (step 6), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 7

- agent's command: `go to drawer 3`
- game reply: You arrive at drawer 3. On the drawer 3, you see nothing.
- ledger after step 7: at **drawer 3** (step 7), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 8

- agent's command: `go to drawer 4`
- game reply: You arrive at drawer 4. The drawer 4 is closed.
- ledger after step 8: at **drawer 4** (step 8), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 9

- agent's command: `open drawer 4`
- game reply: You open the drawer 4. The drawer 4 is open. In it, you see nothing.
- this command depends on: "you are at drawer 4" 有证据
- ledger after step 9: at **drawer 4** (step 8), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 10

- agent's command: `go to drawer 5`
- game reply: You arrive at drawer 5. On the drawer 5, you see a cd 3, and a cellphone 3.
- ledger after step 10: at **drawer 5** (step 10), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 11

- agent's command: `open drawer 5`
- game reply: Nothing happens.
- this command depends on: "you are at drawer 5" 有证据
- ledger after step 11: at **drawer 5** (step 10), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 12

- agent's command: `go to shelf 1`
- game reply: You arrive at shelf 1. On the shelf 1, you see a pen 1.
- ledger after step 12: at **shelf 1** (step 12), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 13

- agent's command: `go to shelf 2`
- game reply: You arrive at shelf 2. On the shelf 2, you see a mug 1.
- ledger after step 13: at **shelf 2** (step 13), holding **nothing**; taken for the task: -; done: -; tools that worked: -; ruled out: -

## Step 14

- agent's command: `take mug 1 from shelf 2`
- game reply: You pick up the mug 1 from the shelf 2.
- this command depends on: "you are at shelf 2" 有证据; "your hands are empty" 有证据; "mug 1 is in/on shelf 2" 有证据
- ledger after step 14: at **shelf 2** (step 13), holding **mug 1** (step 14); taken for the task: mug 1 is the mug the task asks for [有证据, step 14]; done: -; tools that worked: -; ruled out: -

## Step 15

- agent's command: `go to desk 1`
- game reply: You arrive at desk 1. On the desk 1, you see a creditcard 1, a desklamp 1, a laptop 1, a pencil 2, and a pencil 1.
- ledger after step 15: at **desk 1** (step 15), holding **mug 1** (step 14); taken for the task: mug 1 is the mug the task asks for [有证据, step 14]; done: -; tools that worked: -; ruled out: -

## Step 16

- agent's command: `move mug 1 to desk 1`
- game reply: You move the mug 1 to the desk 1.
- this command depends on: "you are holding mug 1" 有证据; "you are at desk 1" 有证据; "desk 1 is open" 有证据
- ledger after step 16: at **desk 1** (step 15), holding **nothing**; taken for the task: mug 1 is the mug the task asks for [有证据, step 14]; done: -; tools that worked: -; ruled out: -

## Step 17

- agent's command: `use desklamp 1`
- game reply: You turn on the desklamp 1.
- this command depends on: "you are at desk 1" 有证据
- **decision after the reply:** The task is not finished. It needs "you are holding mug 1", but step 16: "You move the mug 1 to the desk 1.".
- ledger after step 17: at **desk 1** (step 15), holding **nothing**; taken for the task: mug 1 is the mug the task asks for [有证据, step 14]; done: -; tools that worked: -; ruled out: -

## Step 18

- agent's command: `take mug 1 from desk 1`
- game reply: You pick up the mug 1 from the desk 1.
- this command depends on: "you are at desk 1" 有证据; "your hands are empty" 有证据; "mug 1 is in/on desk 1" 有证据
- ledger after step 18: at **desk 1** (step 15), holding **mug 1** (step 18); taken for the task: mug 1 is the mug the task asks for [有证据, step 14]; done: -; tools that worked: -; ruled out: -

