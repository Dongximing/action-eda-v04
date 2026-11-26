# Summary

Decidable accuracy by stratum (n in parentheses); fb = false-block rate on SUPPORTED gold.

| run | method | all=all | order_sensitive=True | composition=True | indirect=True | ref=anaphoric | fb(all) | unknown(all) | calls/claim |
|---|---|---|---|---|---|---|---|---|---|
| api_adapters_openrouter_chat/ctx0 | D1 | 0.942 (139) | - | - | - | - | 0.000 | 0.058 | 5.633 |
| api_adapters_openrouter_chat/ctx0 | T0 | 1.000 (139) | - | - | - | - | 0.000 | 0.000 | 0.000 |

## Runs

| run | decision model | generator | context_k | prompt | wall s | errors | one-hot answers |
|---|---|---|---|---|---|---|---|
| api_adapters_openrouter_chat/ctx0 | api:openrouter/qwen/qwen3.5-9b@parasail | None | 0 | v0.4-p5 | 21 | 0 | 0 |

## Key paired differences (decidable accuracy, episode bootstrap 95% CI)

| run | a | b | stratum | n | diff | CI |
|---|---|---|---|---|---|---|
