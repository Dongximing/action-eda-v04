# Won-game comparison for blame after failure (hand labels, one annotator, Claude; not blind to the outcome)

Won games with an early premise error: a rule alarm (E1 wrong object, E2 put down early, E2 carried while fetching
the second) on a command that ran. 9 found; u100 and u114 dropped (their alarm was on a command that failed, so no
premise was set). Failures counted from e until the premise was repaired. Every thought after those failures was read.

| game | premise error at e | failures before repair | thought doubts the premise at | doubt acted on |
|---|---|---|---|---|
| u054 | wrong object: butterknife for knife (12) | 17, 22, 23 | 22, 23 ("butterknife is not a valid substitute for knife") | yes: searched, took knife 1 at 29 |
| u098 | apple put in the microwave before heating (7) | 9, 10, 11 | 9 (raised, dismissed), 10 ("the example did not put the egg in first") | yes: takes it out (11-13) |
| u112 | mug put in the microwave before heating (15) | 16, 18, 19 | 19 (same comparison with the example) | yes: takes it out (20-21) |
| u121 | kept keychain 1 while fetching the second (25) | 36-41 | none | repaired at 46 without a stated doubt after a failure |
| u123 | kept peppershaker 3 while fetching the second (4) | 10, 11 | 11 ("put the one I already have into a drawer first") | yes (12-14) |
| u125 | kept peppershaker 4 while fetching the second (5) | 6 | 6 ("put this first peppershaker into a drawer to make progress") | yes (7-9) |
| u127 | kept pillow 1 while fetching the second (3) | 4, 5, 6, 7, 10-14 | 6, 7 ("I cannot hold two objects; I need to free my hands") | yes: tries to set it down (8-16) |

| | won (7 games) | lost (22 games) |
|---|---|---|
| failures after e (won: until repair; lost: first 9 per game) | 27 | 184 |
| thought doubts the earlier premise | 9 (33 pct) | 9 (5 pct) |
| games where it ever does | 6/7 | 7/22 within the first 9 failures (9/22 over all failures) |
| doubts followed by a command that acts on them | 6/9 | 2/17 (all failures) |

Fisher exact, two-sided: games with a doubt p = 0.026; doubts per failure p = 0.00006; doubt acted on p = 0.008.
Caveats: small samples; won and lost games were selected differently (rule alarm vs the C1 audit); labels by one
annotator who knew the outcome; failures within a game are not independent (so the per-failure p is optimistic).
