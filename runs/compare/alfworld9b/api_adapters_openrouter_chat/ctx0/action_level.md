# Action-level blocking: runs/compare/alfworld9b/api_adapters_openrouter_chat/ctx0

92 proposed actions; tracker-contradicted 10, failed in env 30.

| method | ref | blocked | tp | fp | fn | precision | recall | false-block | actions with UNKNOWN |
|---|---|---|---|---|---|---|---|---|---|
| D1 | tracker | 10 | 10 | 0 | 0 | 1.000 | 1.000 | 0.000 | 2 |
| D1 | env | 10 | 10 | 0 | 20 | 1.000 | 0.333 | 0.000 | 2 |
| D1f | tracker | 2 | 2 | 0 | 8 | 1.000 | 0.200 | 0.000 | 8 |
| D1f | env | 2 | 2 | 0 | 28 | 1.000 | 0.067 | 0.000 | 8 |
| H1 | tracker | 10 | 9 | 1 | 1 | 0.900 | 0.900 | 0.012 | 0 |
| H1 | env | 10 | 9 | 1 | 21 | 0.900 | 0.300 | 0.016 | 0 |
| H2 | tracker | 3 | 3 | 0 | 7 | 1.000 | 0.300 | 0.000 | 4 |
| H2 | env | 3 | 3 | 0 | 27 | 1.000 | 0.100 | 0.000 | 4 |
| P0 | tracker | 43 | 9 | 34 | 1 | 0.209 | 0.900 | 0.415 | 6 |
| P0 | env | 43 | 27 | 16 | 3 | 0.628 | 0.900 | 0.258 | 6 |
| T0 | tracker | 10 | 10 | 0 | 0 | 1.000 | 1.000 | 0.000 | 0 |
| T0 | env | 10 | 10 | 0 | 20 | 1.000 | 0.333 | 0.000 | 0 |
| U1 | tracker | 81 | 10 | 71 | 0 | 0.123 | 1.000 | 0.866 | 0 |
| U1 | env | 81 | 30 | 51 | 0 | 0.370 | 1.000 | 0.823 | 0 |
| direct (no check) | tracker | 0 | 0 | 0 | 10 | - | 0.000 | 0.000 | 0 |
| direct (no check) | env | 0 | 0 | 0 | 30 | - | 0.000 | 0.000 | 0 |
