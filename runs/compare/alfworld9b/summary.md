# Summary

Decidable accuracy by stratum (n in parentheses); fb = false-block rate on SUPPORTED gold.

| run | method | all=all | order_sensitive=True | composition=True | indirect=True | ref=anaphoric | fb(all) | unknown(all) | calls/claim |
|---|---|---|---|---|---|---|---|---|---|
| api_adapters_openrouter_chat/ctx0 | D1 | 0.986 (139) | - | - | - | - | 0.000 | 0.014 | 5.633 |
| api_adapters_openrouter_chat/ctx0 | D1f | 0.928 (139) | - | - | - | - | 0.000 | 0.058 | 3.806 |
| api_adapters_openrouter_chat/ctx0 | H1 | 0.978 (139) | - | - | - | - | 0.016 | 0.000 | 1.000 |
| api_adapters_openrouter_chat/ctx0 | H2 | 0.950 (139) | - | - | - | - | 0.000 | 0.029 | 1.000 |
| api_adapters_openrouter_chat/ctx0 | P0 | 0.540 (139) | - | - | - | - | 0.434 | 0.043 | 6.122 |
| api_adapters_openrouter_chat/ctx0 | T0 | 1.000 (139) | - | - | - | - | 0.000 | 0.000 | 0.000 |
| api_adapters_openrouter_chat/ctx0 | U1 | 0.475 (139) | - | - | - | - | 0.566 | 0.000 | 15.626 |

## Runs

| run | decision model | generator | context_k | prompt | wall s | errors | one-hot answers |
|---|---|---|---|---|---|---|---|
| api_adapters_openrouter_chat/ctx0 | api:openrouter/qwen/qwen3.5-9b@parasail | None | 0 | v0.4-p6 | 96 | 0 | 0 |

## Key paired differences (decidable accuracy, episode bootstrap 95% CI)

| run | a | b | stratum | n | diff | CI |
|---|---|---|---|---|---|---|
| api_adapters_openrouter_chat/ctx0 | D1 | P0 | all=all | 139 | +0.446 | [+0.155, +0.660] |
