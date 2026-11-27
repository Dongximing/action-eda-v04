# Place lists offline: decision model (incremental) vs the 9B model's own lists

Server http://127.0.0.1:8012/v1/systemone, model local server. 68 games, 2016 logged selfexplore steps. Answer key: the code's lists from "You arrive at <place>" (code_visited / code_not_visited).

| who writes the lists | steps | unusable answers | not-visited list exact | missing (unvisited places left out) | extra (visited places listed as unvisited) |
|---|---|---|---|---|---|
| decision model, incremental | 2016 | 0 | 1609 (79.8%) | 499 | 34 |
| qwen3.5-9b (selfexplore, logged) | 2016 | 17 | 1314 (65.2%) | 11246 | 66 |

Requests: 874 new, 1074 from cache; 1856s in new requests.
An unusable answer on a record counts as "none" for that record (0 steps affected).
