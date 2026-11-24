# Action-EDA v0.4：动作前核查的离线对比

对应设计文档 `Agent_Jev_EDA_Method_Design_v0.4.md` 的 §3（核查器）、§5（数据）和 §6.1（对照方法）。

这一版做的是**离线对比**：给定同一组 (claim, 历史前缀) 样本，各方法用同一个决策模型给出判断，再按分层统计和配对 bootstrap 比较。在线接入主 Agent（§6.3）还没写。

## 在 GPU 机器上跑

```bash
git clone <仓库地址> action-eda-v04 && cd action-eda-v04
python -m venv .venv && source .venv/bin/activate
pip install -e ".[hf]"          # 如需特定 CUDA 版本的 torch，先按 pytorch.org 装好 torch 再执行这一行
python -m unittest discover -s tests
python scripts/make_diagnostic.py --out data/diag --n-per-cell 8
DATA=data/diag MODELS="Qwen/Qwen3-4B Qwen/Qwen3.5-4B" CTX="0 1" bash scripts/run_sweep.sh
```

- 第一次运行会从 HuggingFace 下载模型。如果机器上已有缓存，可以加 `HF_HUB_OFFLINE=1`。
- 结果写在 `runs/sweep/diag/<模型>/ctx<k>/`，汇总在 `runs/sweep/diag/summary.md`。
- 有多张卡时，用 `CUDA_VISIBLE_DEVICES` 把不同模型分到不同的卡上，各自跑一次 `run_sweep.sh`，`OUT` 设成同一个目录。
- 显存不够时：`EXTRA="--dtype float16"`，或者用 `METHODS` 减少方法。

## 目录

```
aeda/schema.py       样本（可见输入）与标签（私有）的数据格式，两者分文件存放
aeda/prompts.py      所有提示词模板；改模板时更新 PROMPT_VERSION
aeda/backends.py     决策模型后端：本地 HF 单 token 选项读出 / Jev 占位 / 表格模拟
aeda/verifiers.py    H1 H2 U1 D1 D1f D2 E1 P0 Q0 T0 十种方法
aeda/alfworld.py     ALFWorld 动作解析、确定性跟踪器、公开前置条件
aeda/evaluate.py     分层指标与按 episode 分组的配对 bootstrap
scripts/make_diagnostic.py   生成带标签的合成诊断集（控制顺序、组合、干扰数、指代）
scripts/convert_alfworld.py  ALFWorld 轨迹 → 样本（负对照）
scripts/generate_claims.py   用 LLM 生成动态怀疑，并输出待标注模板
scripts/run_offline.py       跑方法，写 predictions.jsonl 和 run_meta.json
scripts/evaluate.py          对照标签打分，写 report.md / report.json
scripts/run_sweep.sh         模型 × context_k 批量跑 + 评测 + 汇总
scripts/summarize.py         把多个 report.json 汇总成一张表
data/smoke/                  7 个手工构造的冒烟样本和模拟后端答案表
data/alfworld_example/       1 条构造的 ALFWorld 轨迹（仿 ReAct 附录的洗刀例子，文字为自写）
tests/                       逻辑测试（不需要模型）
```

## 方法

| 代码 | 文档 | 做什么 |
|---|---|---|
| `H1` | H1 | 整段历史一次判断 |
| `H2` | H2 | 按实体过滤后的窗口一次判断（与 `D1f` 看同一批记录） |
| `U1` | U1 | 逐条三选项判断，不看顺序：任一条推翻分数 ≥ τ 即 CONTRADICTED |
| `D1` | D1 | 逐条三选项判断，从最新往前扫，最近的非无关记录决定结果 |
| `D1f` | D1-f | D1 只看按实体过滤的窗口 |
| `D2` | D2 | D1 + 弱否定记录的两两补救 |
| `E1` | E1 | 每条记录抽取 (实体, 属性, 值)，代码按最新为准跟踪，再把 claim 映射到 key |
| `P0` | P0 | 找到最近的确立来源后，看之后是否还有提到该实体的记录 |
| `Q0` | Q0 | 原 EDA：二选项 Q-source / Q-delta，`max(-log-odds)` |
| `T0` | T0 | 确定性跟踪器，只对带 `spec` 的 claim 有效（目前是 ALFWorld 的位置/持有） |

没有实现：G1（BlackSwan 式多轮探测，需要在线环境）。

**和 v0.4 文档的一处出入：**文档里 H2 定义为“读 D1 实际判过的同一批记录”。但 D1 已经不按实体过滤、看全部历史，这样 H2 就和 H1 完全一样。代码里 H2 改为和 D1f 共用实体过滤窗口，所以“拆开判断本身”的效应用 `D1f − H2` 测；顺序效应 `D1 − U1` 不受影响。

## 关键参数（`Config`，可在命令行覆盖）

| 参数 | 默认 | 含义 |
|---|---|---|
| `--context-k` | 0 | 单条判断时附上前面 k 条记录，只用来理解指代；D1/D1f/D2/U1/P0 同样生效，Q0 不加 |
| `--tau-conf` | 0.5 | 一条记录/一对记录算“决定性”的最低概率 |
| `--tau-low` / `--tau-high` | 0.15 / 0.5 | D2 弱否定区间 |
| `--max-pairs` | 6 | D2 每个 claim 最多检查的记录对数 |
| `--tau-q0` | 0.0 | Q0 判为 CONTRADICTED 的 `-log-odds` 阈值 |
| `--early-stop` | 1 | D1 找到决定性记录后停止往前扫 |

这些阈值都是占位默认值，需要先在开发集上固定，再跑测试集。

**注意：**`context_k > 0` 后，单条判断不再严格只看一条记录，对 D1 和 U1 同样生效，所以两者的对比仍然公平。但汇报时要写明 k。

## 诊断集（`make_diagnostic.py`）

4 个领域（预订、文件、订单、账户），中英文各一套模板。每条样本一个 claim，标签自动生成，全部标为 `synthetic: true`。

| cell | 事件序列 | 正确答案 | 标签维度 |
|---|---|---|---|
| `est` | 确立 | 成立 | |
| `inv` | 确立 → 推翻 | 不成立 | |
| `reest` | 确立 → 推翻 → 重新确立 | 成立 | order_sensitive |
| `reest_inv` | 确立 → 推翻 → 重新确立 → 推翻 | 不成立 | order_sensitive |
| `comp` | 确立 → A → B（A、B 合起来才推翻） | 不成立 | composition |
| `comp_ctrl` | 确立 → A | 成立 | 与 comp 配对 |
| `def_none` / `def_withdraw` / `def_resume` | “某事没发生”类条件 | 成立 / 不成立 / 成立 | default，resume 为 order_sensitive |

交叉的两个因素：
- **事件之间的干扰记录数**（`--distract`，默认 0,3,8）；
- **推翻/重新确立的记录是否点名实体**：`explicit` 点名；`anaphoric` 只用指代，比如“先别取消”，标为 `indirect`。

`extra` 里记录了 `cell / n_distract / ref / lang / domain`，评测时会作为额外的分层维度。

## ALFWorld 负对照（`convert_alfworld.py`）

输入是每个 episode 一行的 JSONL：

```json
{"episode_id": "...", "task": "...", "init_obs": "...", "steps": [{"action": "go to countertop 1", "observation": "You arrive at ..."}]}
```

- 每个会改变状态的动作（take/put/open/close/clean/heat/cool）生成一个样本。记录只包含这一步**之前**的历史；claim 是公开动作语义推出的前置条件（位置、持有）。
- 标签由同一前缀上的确定性跟踪器给出（`label_source: tracker`），所以 T0 按定义全对。这个对照要回答的是：用模型的方法能不能达到跟踪器的水平。
- 这一步实际是否成功（Nothing happens）存在 `extra.action_succeeded` 里，只用于分析，不给核查器看。

## 动态怀疑（`generate_claims.py`）

用生成模型为每个样本补充最多 K 条动态怀疑（`origin: dynamic`），同时输出 `to_label.jsonl` 待人工标注。标好 `gold` 后并入 `labels.jsonl`，就能用 `origin=dynamic/fixed` 分层，检验 P2（带条件判断的效应）。

## 接 Jev

在 `aeda/backends.py` 的 `JevBackend.options` 里填真实调用，返回 `{选项字母: 概率}`。如果接口只返回一个选项，就返回 one-hot；这时 D2 的弱信号触发和 Q0 的 log-odds 会退化，结果里需要注明。

## 样本格式

`samples.jsonl`（核查器能看到的全部输入）：

```json
{"sid": "s1", "episode_id": "ep1", "task": "...", "proposed_action": "cancel_reservation(R123)",
 "action_reversible": false, "window_complete": true,
 "records": [{"rid": 1, "source": "user", "text": "...", "entities": ["R123"]}],
 "claims": [{"cid": "c1", "text": "...", "kind": "state", "origin": "dynamic", "entities": ["R123"], "spec": null}]}
```

`labels.jsonl`（只给评测脚本）：

```json
{"sid": "s1", "cid": "c1", "gold": "SUPPORTED", "order_sensitive": true, "composition": false,
 "indirect": false, "implicit_order": null, "synthetic": false, "extra": {}}
```

- 预测中的 `SUPPORTED_DEFAULT` 在打分时算作 `SUPPORTED`，比例单独报告。
- 在样本里写入标签字段会直接报错。

## 成本记录

- `predictions.jsonl` 的 `calls` 是该方法对该 claim 发出的逻辑调用数，缓存命中也算在内。
- `run_meta.json` 的 `backend_usage` 是实际计算量：前向次数、缓存命中、输入 token 和耗时。
- E1 的抽取每个样本只做一次，成本记在第一个 claim 上。

## 本机冒烟结果（Qwen3-4B，Mac MPS，7 个构造 claim，不是实验结论）

| context_k | U1 | D1 | D1f | D2 | P0 |
|---|---|---|---|---|---|
| 0 | 4/7 | 4/7 | 5/7 | 4/7 | 3/7 |
| 1 | 5/7 | 5/7 | 5/7 | 5/7 | 3/7 |
| 2 | 4/7 | 4/7 | 5/7 | 4/7 | 3/7 |

看到的现象：
- 不加上下文时，“好，还是取消吧”被判成推翻；加上一条上下文后，判对为确立。
- 但“先别取消”不管加不加上下文，都被判为无关，所以“撤回取消”（c3）所有方法都判错。
- 组合例子（c4）加了上下文后，清理记录被正确判为推翻。这说明 context_k 和 D2 的两两补救在功能上有重叠。
- Qwen3-4B 的选项概率大多接近 0 或 1，D2 的弱否定区间（0.15–0.5）几乎不会被触发。

## 下一步

1. 在 GPU 上跑完整诊断集，先看 P1（顺序敏感样本上 D1 vs U1、H1）和 P3（组合样本上 D2 vs D1）。
2. 选定主环境，写轨迹 → 样本的转换脚本，并人工标注。
3. 在开发集上固定阈值和 context_k，再跑测试集。
