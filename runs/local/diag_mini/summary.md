# Summary

Decidable accuracy by stratum (n in parentheses); fb = false-block rate on SUPPORTED gold.

| run | method | all=all | order_sensitive=True | composition=True | indirect=True | ref=anaphoric | fb(all) | unknown(all) | calls/claim |
|---|---|---|---|---|---|---|---|---|---|
| Qwen_Qwen3-4B/ctx0 | D1 | 0.658 (120) | 0.518 (56) | 0.375 (8) | 0.538 (52) | 0.568 (44) | 0.357 | 0.017 | 2.217 |
| Qwen_Qwen3-4B/ctx0 | D1f | 0.558 (120) | 0.571 (56) | 0.000 (8) | 0.308 (52) | 0.364 (44) | 0.143 | 0.017 | 2.225 |
| Qwen_Qwen3-4B/ctx0 | D2 | 0.658 (120) | 0.518 (56) | 0.375 (8) | 0.538 (52) | 0.568 (44) | 0.357 | 0.017 | 2.217 |
| Qwen_Qwen3-4B/ctx0 | E1 | 0.133 (120) | 0.089 (56) | 0.000 (8) | 0.135 (52) | 0.159 (44) | 0.321 | 0.708 | 5.100 |
| Qwen_Qwen3-4B/ctx0 | H1 | 0.567 (120) | 0.482 (56) | 0.125 (8) | 0.423 (52) | 0.477 (44) | 0.214 | 0.000 | 1.000 |
| Qwen_Qwen3-4B/ctx0 | H2 | 0.517 (120) | 0.500 (56) | 0.000 (8) | 0.308 (52) | 0.364 (44) | 0.143 | 0.000 | 1.000 |
| Qwen_Qwen3-4B/ctx0 | P0 | 0.583 (120) | 0.536 (56) | 0.875 (8) | 0.577 (52) | 0.523 (44) | 0.607 | 0.017 | 3.492 |
| Qwen_Qwen3-4B/ctx0 | Q0 | 0.617 (120) | 0.607 (56) | 0.375 (8) | 0.481 (52) | 0.500 (44) | 0.196 | 0.000 | 4.517 |
| Qwen_Qwen3-4B/ctx0 | U1 | 0.625 (120) | 0.446 (56) | 0.375 (8) | 0.538 (52) | 0.568 (44) | 0.446 | 0.008 | 4.100 |
| Qwen_Qwen3-4B/ctx0 | _meta_ | backend=hf:Qwen/Qwen3-4B ctx=0 prompt=v0.4-p2 wall=535s errors=0 | | | | | | | |
| Qwen_Qwen3-4B/ctx1 | D1 | 0.650 (120) | 0.464 (56) | 0.625 (8) | 0.558 (52) | 0.545 (44) | 0.429 | 0.008 | 2.283 |
| Qwen_Qwen3-4B/ctx1 | D1f | 0.542 (120) | 0.536 (56) | 0.000 (8) | 0.308 (52) | 0.364 (44) | 0.214 | 0.017 | 2.342 |
| Qwen_Qwen3-4B/ctx1 | D2 | 0.650 (120) | 0.464 (56) | 0.625 (8) | 0.558 (52) | 0.545 (44) | 0.429 | 0.008 | 2.283 |
| Qwen_Qwen3-4B/ctx1 | E1 | 0.133 (120) | 0.089 (56) | 0.000 (8) | 0.135 (52) | 0.159 (44) | 0.321 | 0.708 | 5.100 |
| Qwen_Qwen3-4B/ctx1 | H1 | 0.567 (120) | 0.482 (56) | 0.125 (8) | 0.423 (52) | 0.477 (44) | 0.214 | 0.000 | 1.000 |
| Qwen_Qwen3-4B/ctx1 | H2 | 0.517 (120) | 0.500 (56) | 0.000 (8) | 0.308 (52) | 0.364 (44) | 0.143 | 0.000 | 1.000 |
| Qwen_Qwen3-4B/ctx1 | P0 | 0.550 (120) | 0.446 (56) | 1.000 (8) | 0.577 (52) | 0.500 (44) | 0.696 | 0.017 | 3.792 |
| Qwen_Qwen3-4B/ctx1 | Q0 | 0.617 (120) | 0.607 (56) | 0.375 (8) | 0.481 (52) | 0.500 (44) | 0.196 | 0.000 | 4.517 |
| Qwen_Qwen3-4B/ctx1 | U1 | 0.642 (120) | 0.446 (56) | 0.625 (8) | 0.558 (52) | 0.545 (44) | 0.464 | 0.008 | 4.100 |
| Qwen_Qwen3-4B/ctx1 | _meta_ | backend=hf:Qwen/Qwen3-4B ctx=1 prompt=v0.4-p2 wall=558s errors=0 | | | | | | | |

## Key paired differences (decidable accuracy, episode bootstrap 95% CI)

| run | a | b | stratum | n | diff | CI |
|---|---|---|---|---|---|---|
| Qwen_Qwen3-4B/ctx0 | D1 | U1 | order_sensitive=True | 56 | +0.071 | [-0.018, +0.161] |
| Qwen_Qwen3-4B/ctx0 | D1 | H1 | order_sensitive=True | 56 | +0.036 | [-0.143, +0.214] |
| Qwen_Qwen3-4B/ctx0 | D2 | D1 | composition=True | 8 | +0.000 | [+0.000, +0.000] |
| Qwen_Qwen3-4B/ctx0 | D1 | E1 | all=all | 120 | +0.525 | [+0.425, +0.625] |
| Qwen_Qwen3-4B/ctx0 | D1 | P0 | all=all | 120 | +0.075 | [-0.042, +0.183] |
| Qwen_Qwen3-4B/ctx0 | D1 | Q0 | all=all | 120 | +0.042 | [-0.058, +0.142] |
| Qwen_Qwen3-4B/ctx1 | D1 | U1 | order_sensitive=True | 56 | +0.018 | [-0.036, +0.089] |
| Qwen_Qwen3-4B/ctx1 | D1 | H1 | order_sensitive=True | 56 | -0.018 | [-0.196, +0.161] |
| Qwen_Qwen3-4B/ctx1 | D2 | D1 | composition=True | 8 | +0.000 | [+0.000, +0.000] |
| Qwen_Qwen3-4B/ctx1 | D1 | E1 | all=all | 120 | +0.517 | [+0.417, +0.617] |
| Qwen_Qwen3-4B/ctx1 | D1 | P0 | all=all | 120 | +0.100 | [-0.008, +0.208] |
| Qwen_Qwen3-4B/ctx1 | D1 | Q0 | all=all | 120 | +0.033 | [-0.067, +0.133] |
