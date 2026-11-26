# Action-level blocking: runs/alfworld9b/tracker

92 proposed actions; tracker-contradicted 10, failed in env 30.

| method | ref | blocked | tp | fp | fn | precision | recall | false-block | actions with UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|
| T0 | tracker | 10 | 10 | 0 | 0 | 1.000 | 1.000 | 0.000 | 0 |
| T0 | env | 10 | 10 | 0 | 20 | 1.000 | 0.333 | 0.000 | 0 |
| direct (no check) | tracker | 0 | 0 | 0 | 10 | - | 0.000 | 0.000 | 0 |
| direct (no check) | env | 0 | 0 | 0 | 30 | - | 0.000 | 0.000 | 0 |
