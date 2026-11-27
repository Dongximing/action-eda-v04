# Action-EDA v0.4：动作前核查的离线对比

对应设计文档 [docs/design_v0.4.md](docs/design_v0.4.md) 的 §3（核查器）、§5（数据）和 §6.1（对照方法）。

这一版做的是**离线对比**：给定同一组 (claim, 历史前缀) 样本，各方法用同一个决策模型给出判断，再按分层统计和配对 bootstrap 比较。在线接入主 Agent（§6.3）还没写。

## 当前方法：依赖图回溯（`react_dep_graph`）

**一句话：** agent 是标准 ReAct（同一个 qwen3.5-9b、同一个提示词，不训练）；旁边一段程序把每一步建成一张依赖图（每个动作依赖哪些信念、每个信念有没有游戏回复做证据）。失败时沿图往回走，找到最早那个没有证据的假设，告诉 agent，并且不再执行依赖它的动作。

**动机（我们的分析）：** agent 失败后几乎只怪眼前那一步。ReAct 输掉的局里，只有 2% 的失败解释会追到更早的步骤，赢的局里是 30%（`runs/online/analysis/blame_labels_react_std_t1536.md`）。循环往往就是早期错误一直没被推翻造成的（`runs/online/analysis/c1_audit_react_std_t1536.md`）。

### 代码

| 文件 | 内容 |
|---|---|
| `scripts/dep_graph.py` | 控制器：图（点、带类型的边）、证据等级、动作前检查 `before()`、失败后找罪魁 `after()`、多层回溯 `trace()`、每步整张图 `graph_at()` |
| `scripts/run_online.py` | 运行程序。`--arm react_dep_graph` = ReAct + 控制器（多层回溯）；`react_dep` = 只回溯一层；`react_ptr_{none,recent,random,dep}` = 对照组（同样的时机、同样格式的一句话，只是指向的步骤不同，不拦截） |
| `scripts/dep_ledger.py` | 重放一局，写出每一步的账本（`<组名>_ledger.md`），并核对重放结果和运行时完全一致 |
| `scripts/dep_io_readable.py` | 每一步模型的完整输入和输出 + 游戏回复 + 控制器的决定（`<组名>_io.md`） |
| `scripts/make_stateact_data.py`、`scripts/run_stateact_official.sh` | 用官方 StateAct 代码跑同样的游戏，做对比 |

**图的结构：** 点有四种：动作 `a3`、游戏回复 `r3`、信念（如 `b:bind:handtowel 1`）、任务原文 `task`。边带类型：`needs`（命令的前提）、`relies_on`（命令押的假设，拿起 X 就是押 X 是任务要的东西）、`creates` / `falsifies`（命令让信念变真或变假）、`supports` / `refutes`（回复支持或否定信念）。信念的证据等级：有证据 / 没证据 / 被否定 / 已排除。

**每一步做什么：**
1. **执行前：** 命令依赖的信念如果"已排除"或"被否定"，就不执行，告诉 agent 原因。被否定时还会沿图往回找背后没证据的假设，一并排除；如果手里拿着的正是被排除的东西，就替它放下。
2. **执行后：** 按游戏回复更新图。
3. **失败后**（"Nothing happens"，或东西放进目标位置了任务却没完成）：先看当前状况（在哪、手里拿着什么），有问题就告诉 agent，不排除；然后沿图往回走，把最早那个没证据的假设排除。

**写死的部分（只适用于 ALFWorld）：** 从回复里读信念的格式（"You pick up X"）、每个命令的前提（照 ALFWorld 的动作说明），以及"是不是任务要的东西"用名字比较。"这种家电能不能加热"不是写死的，是从失败里学出来的。

### 怎么跑

准备同下面"准备"一节（`requirements.txt`、`OPENROUTER_API_KEY`）。`runs/online/unseen/protocol.json` 定下 valid_unseen 的 134 局（编号 u001–u134）。

**运行程序不复用任何旧答案**，每一步都重新调用模型。答案仍写进每局的 `calls.sqlite` 作为记录，但不会读回。只有离线补日志的工具（`replay_io.py`、`backfill_io.py`）会读旧答案重建日志，它们不调用接口。每组用一个新的空文件夹（里面放一份 `protocol.json`），这样各次运行完全独立：

```bash
G=u013,u047,u072,u083,u095,u097,u101,u102,u115        # 或全部 134 局：不加 --games
for A in react_std react_dep_graph; do
  mkdir -p runs/online/my_$A && cp runs/online/unseen/protocol.json runs/online/my_$A/
  python scripts/run_online.py --out runs/online/my_$A --arm $A --no-baseline --react-max-tokens 1536 \
      --split-dir data/alfworld/json_2.1.1/valid_unseen --games $G
done
```

对照组：把上面的 `A` 换成 `react_ptr_none`（只说"失败了"）、`react_ptr_recent`（指上一步）、`react_ptr_random`（随机指一步）、`react_ptr_dep`（指依赖图找到的那一步）。

官方 StateAct（自己在终端里跑，会下载并运行他们的代码）：

```bash
python scripts/make_stateact_data.py --games $G --out third_party/stateact/alfworld_data_9
ALFWORLD_DATA=third_party/stateact/alfworld_data_9 TRIAL=my_trial NUM=9 bash scripts/run_stateact_official.sh
```

**每局的输出**（在 `<文件夹>/<编号>/`）：

| 文件 | 内容 |
|---|---|
| `<组名>.json` | 结果、游戏历史、控制器的决定（`dep_graph`：说明、拦截、找到的罪魁） |
| `<组名>_graph.jsonl.gz` | 每一步之后的整张图（所有点、所有边、每个信念当时的证据等级），一行一步 |
| `<组名>_io.jsonl.gz` | 每次请求原样的输入和模型原始输出 |

可读版本：`python scripts/dep_ledger.py --run <文件夹> --tag react_dep_graph_t1536`、`python scripts/dep_io_readable.py --run <文件夹> --tag react_dep_graph_t1536`。

### 目前的结果（9 局，独立运行，不复用答案）

这 9 局是 ReAct 曾经输过一次的局（选法有偏）。完整表格见 `runs/online/analysis/nine_games_independent_runs.md`。

| 方法 | 运行次数 | 赢 |
|---|---|---|
| ReAct | 2 | 8/18（44%） |
| StateAct（官方代码） | 3 | 14/27（52%） |
| **ReAct + 依赖图（`react_dep_graph`）** | 2 | **18/18（100%）** |

按局比较：和 ReAct 比，7 局更好、2 局一样、0 局更差（符号检验 p = 0.016）；和 StateAct 比，5 局更好、4 局一样、0 局更差（p = 0.0625）。StateAct 3 次全输的 4 局都是拿错了东西（handtowel 当 cloth、cup 当 mug、mug 当 cup），依赖图在这几局上都是沿图找回到"拿错东西"那一步。

**还没做：** 全部 134 局（看原本能赢的局会不会被打乱）、对照组、第二个环境。

## 怎么跑实验（68 局 ALFWorld 在线实验）

主 agent 是 qwen3.5-9b（OpenRouter，服务商 Parasail），每局最多 50 步，游戏来自 ALFWorld valid_seen 的 clean / heat / cool 三类。每一组（arm）的输入都和 baseline 一样，只在规定的地方加东西。

### 准备

```bash
git clone https://github.com/Dongximing/action-eda-v04.git
cd action-eda-v04
python3.11 -m venv .venv-alf
.venv-alf/bin/pip install -r requirements.txt
export OPENROUTER_API_KEY=...        # 只在跑实验时需要；没有设置，run_online.py 会直接退出
```

下面的 `python` 都指 `.venv-alf/bin/python`。跑实验需要的东西都在仓库里：

| 路径 | 内容 |
|---|---|
| `data/alfworld/json_2.1.1/valid_seen/` | ALFWorld 游戏文件（242 局，原样拷贝） |
| `baseline/runner/` | baseline 的 agent 代码：环境、提示、模型调用、缓存 |
| `baseline/oneshot12/` | baseline 最初 12 局的运行结果。`protocol.json` 定下这 12 局、50 步、模型、温度和示范；`routing.json` 定下服务商（`"selected"`）；`one_shot_examples.json` 是三类游戏各一条示范 |
| `runs/online/{d1,more,more2,more3}/` | 68 局的全部结果，每局一个文件夹，每组一个 `<arm>.json`，`calls.sqlite` 是模型回答的记录（运行时不再复用；只有 `replay_io.py` / `backfill_io.py` 读它重建日志） |

68 局分在四个文件夹：

| 文件夹 | 局数 | 游戏从哪来 | 这些局的 baseline |
|---|---|---|---|
| `d1` | 12 | `baseline/oneshot12/protocol.json` | `baseline/oneshot12/gameXX/natural.json` |
| `more` | 24 | 每类抽 8 局没用过的（`runs/online/more/protocol.json`） | 每局的 `direct.json` |
| `more2` | 12 | 每类抽 4 局，跳过 more 的 | 同上 |
| `more3` | 20 | 每类最多抽 11 局，跳过 more 和 more2 的（剩下的不够） | 同上 |

### 跑一组

```bash
for d in d1 more more2 more3; do
  python scripts/run_online.py --out runs/online/$d --arm selfexplore
done
```

`--arm` 可选：

| arm | 做法 |
|---|---|
| `explore` | 代码从历史里算出 r0 里列出的地点哪些去过、哪些没去过，附在最新观察后面 |
| `selfexplore` | 同样的提示，但两张表由同一个 9B 模型单独调用一次来写（每步 2 次调用） |
| `jevexplore` | 同样的清单，改由判断模型 OneJev 记账：每走一步只问它一道选择题“这条命令让 agent 到了哪个地方（或都没有）”，答案由代码累加；地点名单是 9B 在开局时列的一次（和 selfexplore 第一步是同一个请求） |
| `jevexplore_name` | jevexplore 加名字核对：agent 要拿某个东西时，如果这个东西的名字（去掉编号）不是任务句子里的一个词，就拦下来，把原因告诉 agent，让它重新选一次（和 d1 组同样的拦截机制）。这是一条固定的名字规则，不用模型，单独报告 |
| `jevexplore_hard` | 同 `jevexplore_name`，但拦截是硬的：agent 重选后还坚持被拦下的 take，这个命令就不执行。游戏里改为执行 look（不改变任何东西，但占一步），agent 看到的这条记录是它自己的命令加上“Not run: the task is …, which does not name …” |
| `think_jev` | 会思考的 agent 加我们的模块：每步一次调用，先写一句想法再给命令（`{"thought","action"}`），之前的想法留在历史里；示范用 ReAct 同一局带想法的版本（`data/fewshot/react_think_examples.json`，由 `scripts/make_think_examples.py` 生成，动作和观察与 baseline 的示范一致）；再加 `jevexplore_hard` 的模块（OneJev 清单 + 名字核对硬拦截）。和 StateAct 比 |
| `statejev` | 不思考的 baseline agent 加完整状态：OneJev 每条新记录答 5 个问题（到了哪、看到了哪里面的东西、反馈是不是在描述东西、反馈是哪一类、手里的东西有什么变化），由代码累加成“现在在哪、手里拿着什么、哪些地方真正看过里面”，写在最新观察后面；加名字核对硬拦截。问题和累加规则在 `scripts/state_ledger.py`，离线检验 `scripts/jev_state_offline.py` |
| `think_state` | 会思考的 agent（同 `think_jev`）加完整状态记事本（同 `statejev`）和名字核对硬拦截。被硬拦截、没执行的动作不交给 OneJev 判断，直接记为“什么都没变” |
| `think_copy` | 同 `think_state`，但 agent 每步先把记事本抄写一遍，再写想法，再给动作（`{"state","thought","action"}`），抄写和想法都留在历史里，像 StateAct 那样。示范 `data/fewshot/react_think_copy_examples.json` 里的状态由 OneJev 自动写出（`scripts/make_copy_examples.py`），不是人工标注 |
| `react_std` | 标准 ReAct baseline，和 VBL 论文（arXiv 2610.41564，附录 F.3）一致：用 ReflAct 附录 K.1 的指令、MPO 项目（github.com/WeiminXiong/MPO，Apache-2.0）的单示范和拼接方式。第一条用户消息 = 指令 + 一个同类型示范 + 当前任务；之后模型输出 “Thought: …\n Action: …” 或 “Action: …”，环境回 “Observation: …”；温度 0，最多 512 token，50 步；没写 Action 也算一步，回 “Error Input”。示范和指令在 `data/fewshot/mpo/` |
| `stateact` | 对照：已发表的 StateAct（arXiv 2410.02810）原样跑在同样的局、模型和 50 步上：用它自己的提示（每类两个带 goal/状态标注的 ReAct 示范），每步一次调用输出目标、去过的地点、当前位置、手里的东西、想法和动作，完整对话记录都在上下文里。它的提示数据没有许可证，不放进仓库，先运行 `scripts/fetch_stateact_prompts.sh` 取到 `third_party/stateact/`（只当数据读取，不执行） |
| `stateact_chat` | 对照：和 `stateact` 完全一样的提示、示范和动作提取，只是对话改成一问一答：它的提示作为系统消息，每条观察作为用户消息，模型之前的输出作为助手消息。原样的“一条消息”格式下，qwen3.5-9b 从第一步起就抄示范里的任务（d1 跑完的 9 局都这样） |
| `onecall` | 对照：同样的记账要求放进 agent 自己选动作的那次调用里，结果不给 agent 看 |
| `onecall_use` | 对照：onecall 的提示里改一句，要求根据两张表选动作 |
| `d1` `t0` `hint` `mw` `h1` `llm` `loop` `llmloop` | 早期的动作前核查各组，见后面各节 |

- 已经有 `<arm>.json` 的局会跳过，所以中断后运行同一条命令就会接着跑。
- 每局的 `calls.sqlite` 记下每次的模型回答，但运行时**不复用**：每一步都重新调用模型（要花钱），所以重跑的结果可能和原来不同（温度 0 时接口也不完全确定）。要不花钱地重建已有运行的日志，用 `scripts/replay_io.py` / `scripts/backfill_io.py`，它们只读存好的回答，不发请求。
- `--workers`（默认 4）是同时跑几局；`--games game01,game02` 只跑这几局。

### 跑 jevexplore（先起 OneJev 服务）

`scripts/onejev_mac_server.py` 在 Mac 上提供 OneJev1.6-4B 的 System One 接口：模型在 Apple GPU 上跑，拼提示和读概率用 Flide 自带的 OneJev 代码（`flide serve` 只能用 NVIDIA 显卡；有 NVIDIA 显卡时直接用它）。需要一个装了 flide 的环境：`uv pip install flide torchvision`。

```bash
# 终端 1：起服务，一直开着（默认 http://127.0.0.1:8000/v1/systemone）
<装了 flide 的环境>/bin/python scripts/onejev_mac_server.py --model <OneJev1.6-4B 目录>

# 终端 2
for d in d1 more more2 more3; do
  python scripts/run_online.py --out runs/online/$d --arm jevexplore
done
```

不跑游戏、先检验 OneJev 记账准不准：`python3 scripts/jev_places_offline.py --mode incremental`。它拿 selfexplore 存下的每一步问 OneJev，和代码算出的答案比，结果写在 `runs/jev_places/incremental/report.md`（68 局：清单完全正确 79.8%，9B 自己写是 65.2%）。

### 从头复现

从头复现 56 局新游戏的抽取（先跑每局的 baseline，存成 `direct.json`，再跑 d1）。种子都是 0：

```bash
python scripts/run_online.py --out runs/online/more  --new-per-family 8
python scripts/run_online.py --out runs/online/more2 --new-per-family 4  --exclude runs/online/more/protocol.json
python scripts/run_online.py --out runs/online/more3 --new-per-family 11 --exclude runs/online/more/protocol.json,runs/online/more2/protocol.json
```

### 看结果

```bash
python scripts/compare_arms.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3   # -> runs/online/compare.md
python scripts/analyze_losses.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3 --arm selfexplore --out <输出目录>
```

token 用量：`python3 scripts/token_usage.py runs/online/d1 --arms baseline,selfexplore,jevexplore`（写到 `runs/online/d1/tokens.md`）。每次调用都按“重新请求一次”计：缓存命中按原请求的 token 算，失败的请求按它实际用掉的算；只比较这几组都跑过的局。

`compare.md`：每组赢几局、比 baseline 多赢（rescued）和少赢（lost）哪几局、两边都赢的局用了多少步（附符号检验）。`analyze_losses.py`：输掉的局停在哪一步（没找到目标、找到没拿、拿错东西、拿了没处理成功、处理了没放）。

目前的结果（68 局里赢的局数）：baseline 25，explore 44，selfexplore 42，onecall 21。onecall_use 还没跑完。

## 模型角色

| 角色 | 用在哪里 | 怎么指定 |
|---|---|---|
| **决策模型 = Jev** | 所有方法的判断：H1 H2 U1 D1 D1f D2 P0 Q0，以及 E1 的映射和取值判断 | `--backend jev --jev-adapter adapters.jev_adapter:choose` |
| 生成模型 | 只用于 E1 的逐条状态抽取和 `generate_claims.py`。Jev 不生成文本 | `--gen-model <HF 模型>` |
| 对照决策模型（可选） | 以模型本名单独汇报，例如原 EDA 的 Qwen3-4B 单 token 读出 | `--backend hf --model <HF 模型>` |

本地 HF 模型**不是** Jev 的替代品。结果文件 `run_meta.json` 和 `summary.md` 都会写明这次运行实际用的决策模型。

## 第一步：接上 Jev

在 [adapters/jev_adapter.py](adapters/jev_adapter.py) 里实现一个函数：

```python
def choose(context: str, question: str, options: list[tuple[str, str]]) -> dict[str, float] | str
```

- 每个选择题调用一次。`options` 形如 `[("A", "Establishes it: ..."), ("B", "Invalidates it: ..."), ("C", "Neither: ...")]`。
- 返回每个选项字母的分数（会自动归一化）；如果 Jev 只给出选择，就返回选中的字母。
- 只返回字母时，`run_meta.json` 的 `decision_usage.one_hot` 会计数。D2 的弱否定触发和 Q0 的 log-odds 依赖连续分数，这时会退化，结果里要注明。
- 返回未知字母、负分或抛异常：该 claim 记为 UNKNOWN 并带 `error` 字段，`run_offline.py` 以退出码 2 结束（加 `--allow-errors` 可放行）。

先自检，再正式跑：

```bash
python scripts/check_backend.py --backend jev --jev-adapter adapters.jev_adapter:choose
```

它会发出所有方法用到的问题类型，检查返回格式，并逐条打印单条判断的选项概率。冒烟集里有 7 条记录标了“常识上应选的答案”，用来先粗看一下模型的行为。

## 在 GPU 机器上跑

```bash
git clone <仓库地址> action-eda-v04 && cd action-eda-v04
python -m venv .venv && source .venv/bin/activate
pip install -e ".[hf]"        # 如需特定 CUDA 版本的 torch，先按 pytorch.org 装好再执行这一行
python -m unittest discover -s tests -t .
python scripts/check_backend.py --backend jev --jev-adapter adapters.jev_adapter:choose
python scripts/make_diagnostic.py --out data/diag --n-per-cell 8
DATA=data/diag JEV_ADAPTER=adapters.jev_adapter:choose GEN_MODEL=Qwen/Qwen3-4B CTX="0 1" bash scripts/run_sweep.sh
```

- 结果写在 `runs/sweep/diag/jev/ctx<k>/`，汇总在 `runs/sweep/diag/summary.md`。
- 加对照决策模型：`COMPARE_MODELS="Qwen/Qwen3-4B"`，会多出 `runs/sweep/diag/hf_Qwen_Qwen3-4B/ctx<k>/`。
- 不跑 E1（也就不需要生成模型）：`METHODS=H1,H2,U1,D1,D1f,D2,P0,Q0`。
- GPU 只用于本地 HF 模型（生成模型、对照模型）。Jev 调用走你的适配器。
- 显存不够：`EXTRA="--dtype float16"`。

## 目录

```
aeda/schema.py       样本（可见输入）与标签（私有）的数据格式，两者分文件存放
aeda/prompts.py      所有问题模板（选择题拆成 上下文 / 问题 / 选项）；改模板时更新 PROMPT_VERSION
aeda/backends.py     JevBackend（适配器）/ HFOptionBackend / TableBackend（测试）
aeda/verifiers.py    H1 H2 U1 D1 D1f D2 E1 P0 Q0 T0
aeda/alfworld.py     ALFWorld 动作解析、确定性跟踪器、公开前置条件
aeda/evaluate.py     分层指标与按 episode 分组的配对 bootstrap
adapters/jev_adapter.py      Jev 接入点（需要填写）
scripts/check_backend.py     决策模型接口自检
scripts/make_diagnostic.py   生成带标签的合成诊断集
scripts/convert_alfworld.py  ALFWorld 轨迹 → 样本（负对照）
scripts/generate_claims.py   用生成模型补充动态怀疑，并输出待标注模板
scripts/run_offline.py       跑方法，写 predictions.jsonl 和 run_meta.json
scripts/evaluate.py          对照标签打分，写 report.md / report.json
scripts/run_sweep.sh         Jev × context_k（+ 可选对照模型）批量跑 + 评测 + 汇总
scripts/summarize.py         汇总多个 report.json
data/smoke/                  7 个手工构造的冒烟样本和测试用答案表
data/alfworld_example/       1 条构造的 ALFWorld 轨迹（仿 ReAct 附录的洗刀例子，文字为自写）
data/alfworld/               ALFWorld json_2.1.1 的 valid_seen（242 局）和 logic 原样拷贝；68 局在线实验都出自这里，run_online.py 默认读它
tests/                       逻辑测试（不需要模型；fake_jev.py 是测试用的假适配器）
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
| `E1` | E1 | 生成模型逐条抽取 (实体, 属性, 值)，代码按最新为准跟踪；决策模型选出对应的 key 并判断取值 |
| `P0` | P0 | 找到最近的确立来源后，看之后是否还有提到该实体的记录 |
| `Q0` | Q0 | 原 EDA 的问题形式：二选项 Q-source / Q-delta，`max(-log-odds)` |
| `T0` | T0 | 确定性跟踪器，只对带 `spec` 的 claim 有效（目前是 ALFWorld 的位置/持有），不调用模型 |

没有实现：G1（BlackSwan 式多轮探测，需要在线环境）。

**和 v0.4 文档的一处出入：**文档里 H2 定义为“读 D1 实际判过的同一批记录”。但 D1 已经不按实体过滤、看全部历史，这样 H2 就和 H1 完全一样。代码里 H2 改为和 D1f 共用实体过滤窗口，所以“拆开判断本身”的效应用 `D1f − H2` 测；顺序效应 `D1 − U1` 不受影响。

**关于 Q0：**Q0 是原 EDA 的问题形式和聚合规则。用 Jev 跑 Q0，得到的是“Jev + 原 EDA 规则”；要复现原论文的 Qwen3-4B 读出，用 `COMPARE_MODELS="Qwen/Qwen3-4B"` 再跑一次。

## 关键参数（`Config`，可在命令行覆盖）

| 参数 | 默认 | 含义 |
|---|---|---|
| `--context-k` | 0 | 单条判断时附上前面 k 条记录，只用来理解指代；D1/D1f/D2/U1/P0 和 E1 抽取同样生效，Q0 不加 |
| `--tau-conf` | 0.5 | 一条记录/一对记录算“决定性”的最低概率 |
| `--tau-low` / `--tau-high` | 0.15 / 0.5 | D2 弱否定区间（最可能的读法是“确立”的记录不算） |
| `--max-pairs` | 6 | D2 每个 claim 最多检查的记录对数 |
| `--tau-q0` | 0.0 | Q0 判为 CONTRADICTED 的 `-log-odds` 阈值 |
| `--early-stop` | 1 | D1 找到决定性记录后停止往前扫 |

这些阈值都是占位默认值，需要先在开发集上固定，再跑测试集。`context_k > 0` 后单条判断不再严格只看一条记录，汇报时要写明 k。

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

`extra` 里的 `cell / n_distract / ref / lang / domain` 会作为额外的分层维度。

## ALFWorld 负对照（`convert_alfworld.py`）

输入是每个 episode 一行的 JSONL：

```json
{"episode_id": "...", "task": "...", "init_obs": "...", "steps": [{"action": "go to countertop 1", "observation": "You arrive at ..."}]}
```

- 每个会改变状态的动作（take/put/open/close/clean/heat/cool）生成一个样本。记录只包含这一步之前的历史；claim 是公开动作语义推出的前置条件（位置、持有）。
- 标签由同一前缀上的确定性跟踪器给出（`label_source: tracker`），所以 T0 按定义全对。这个对照要回答的是：用模型的方法能不能达到跟踪器的水平。
- 这一步实际是否成功（Nothing happens）存在 `extra.action_succeeded`，只用于分析，不给核查器看。

## 动态怀疑（`generate_claims.py`）

用生成模型为每个样本补充最多 K 条动态怀疑（`origin: dynamic`），同时输出 `to_label.jsonl` 待人工标注。标好 `gold` 后并入 `labels.jsonl`，就能用 `origin=dynamic/fixed` 分层，检验 P2（带条件判断的效应）。

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

- `predictions.jsonl` 的 `calls` 是该方法对该 claim 发出的决策调用数，缓存命中也算在内；`gen_calls` 是生成调用数。
- `run_meta.json` 的 `decision_usage` / `generator_usage` 是实际计算量，包括真实调用、缓存命中、token、耗时和 one-hot 次数。
- E1 的抽取每个样本只做一次，成本记在第一个 claim 上。

## 开发时观察到的情况（Mac 上用 Qwen3-4B 读出，只用来调试代码，不是 Jev 的结果）

- 单独看一条省略了对象的用户话时，模型会判错。“先别取消”被判为无关，“还是取消吧”被判为推翻。这促成了 `--context-k` 选项。
- 模型的选项概率大多接近 0 或 1，D2 的弱否定区间几乎触发不了。换成 Jev 后要先看一下它的分数分布。
- E1 第一版的抽取提示词漏掉了“用户的请求”，导致大部分样本一个 key 都抽不到。现在的提示词已经补上，但还没有用 Jev 加生成模型重新跑过。

## 下一步

1. 填写 Jev 适配器，跑 `check_backend.py`。
2. 在 GPU 上跑诊断集，先看 P1（顺序敏感样本上 D1 vs U1、H1）和 P3（组合样本上 D2 vs D1）。
3. 选定主环境，写轨迹 → 样本的转换脚本，并人工标注。
4. 在开发集上固定阈值和 context_k，再跑测试集。

## ALFWorld 9B 单示范 12 局（outputs/alfworld-9b-oneshot-alternate）

数据来自另一套在线实验的 direct 组自然轨迹：qwen3.5-9b 单示范主 agent，12 局 valid_seen，赢 4 局。`data/alfworld9b/` 由下面的命令生成，已提交：

```bash
python scripts/convert_paired_outputs.py --out data/alfworld9b
```

样本单位是主 agent 提出的每个改变状态的动作（take/move/open/close/clean/heat/cool），共 92 个。记录只包含该动作之前的步骤。claims 是固定前置条件（在哪、拿着什么、手是否空），共 139 条。gold 由 tracker 给出；该动作在环境里是否真的执行（是否返回 "Nothing happens"）记在 `labels.extra.action_succeeded`，核查器看不到。

- 92 个动作里 30 个在环境中失败，其中 10 个违反了位置或持物前置条件，tracker 全部抓到，0 误拦。
- 另外 20 个失败不在固定 claims 的范围内：game11 任务要 cloth，agent 拿了 towel，反复 clean 失败；game09 用 stoveburner 加热。所以在 env 参照下，只靠这些 claims，召回上限是 10/30。

用 Jev 跑（TypeSafe systemone 接口，与 altprovider runner 里的 NativeJev 请求一致；只需 API key，不需要 GPU）：

```bash
export TYPESAFE_API_KEY=...   # 或 JEV_API_KEY；JEV_MODEL 默认 jev-1.14.0
python scripts/check_backend.py --backend jev --jev-adapter adapters.typesafe_jev:choose
DATA=data/alfworld9b JEV_ADAPTER=adapters.typesafe_jev:choose METHODS=T0,H1,H2,U1,D1,D1f,D2,P0,Q0 CTX="0 1" bash scripts/run_sweep.sh
```

每个 run 目录下有 `report.md`（claim 级分层指标）和 `action_level.md`。后者的规则是：只要有一条 claim 判为 CONTRADICTED 就拦下这个动作，再分别和 tracker、环境真实结果比较。若 Jev 响应带 `probabilities`，adapter 会用作分数；否则只返回选项，`run_meta.json` 记为 one-hot，此时 D2 的弱信号触发和 Q0 的 log-odds 会退化。

### 不用 Jev：OpenRouter qwen3.5-9b 作为决策模型

结果记为 `api:openrouter/qwen/qwen3.5-9b@parasail`，不算 Jev 的结果。提示与本地 HF 后端相同；如果供应商返回 logprobs，就用来给选项打分，否则只取答案字母（one-hot）。

```bash
export OPENROUTER_API_KEY=...
python scripts/check_backend.py --backend api --adapter adapters.openrouter_chat:choose
DATA=data/alfworld9b SKIP_JEV=1 API_ADAPTER=adapters.openrouter_chat:choose METHODS=T0,H1,H2,U1,D1,D1f,D2,P0,Q0 CTX="0 1" bash scripts/run_sweep.sh
```

在 context_k=0 时，去掉方法之间共享的相同问题后，最多约 3000 次不同的请求；D1 提前停止会再少一些。`WORKERS` 默认 8 个并发。

`action_level.md` 里的 `direct (no check)` 行就是"什么都不加、直接执行"的基线，对应原实验的 direct 组，12 局赢 4 局。T0 是用规则重放历史的参考上限，不属于这种基线。

### 给判断模型加 few-shot

逐条判断时，先给模型看 8 道标好答案的例题：3 道 A、3 道 B、2 道 C。例题取自主 agent 看过的那 3 条 ReAct Act-only 示范，属于别的游戏，和测试的 12 局不重叠。答案由 tracker 比较这条记录前后的状态自动标出，不是人工挑的。

```bash
python scripts/make_fewshot.py --out data/fewshot/alfworld_record_fewshot.json
DATA=data/alfworld9b SKIP_JEV=1 API_ADAPTER=adapters.openrouter_chat:choose METHODS=T0,D1 CTX="0" \
  OUT=runs/fewshot EXTRA="--fewshot data/fewshot/alfworld_record_fewshot.json" bash scripts/run_sweep.sh
```

`--fewshot` 只作用于逐条判断，也就是 D1、D1f、D2、U1、P0。`run_meta.json` 的 config 里会记下所用文件。

### 逐条判断改成"问状态"（`--record-style state`）

D1 的流程和裁决规则都不变，只改每条记录的问法：
- 默认（effect）问"这条记录对条件做了什么"；
- state 问"这条记录之后，agent 在哪 / 拿着什么"，选项是"就是条件里那个 / 是别的 / 这条看不出"，分别对应 A/B/C，含义和默认问法一样。

few-shot 例题沿用同一套，按同样的问法改写后展示。

```bash
DATA=data/alfworld9b SKIP_JEV=1 API_ADAPTER=adapters.openrouter_chat:choose METHODS=T0,D1 CTX="0" OUT=runs/state \
  EXTRA="--fewshot data/fewshot/alfworld_record_fewshot.json --record-style state" bash scripts/run_sweep.sh
```

## 在线：12 局 baseline vs D1（`scripts/run_online.py`）

主 agent、示范、路由、温度、50 步上限都和 baseline（原实验的 direct 组）相同，actor 也复用同一份缓存。D1 拦下一个动作之前，两组走的每一步完全一样。在 state-changing 动作执行前，用 D1 核查前提：
- 结果为 CONTRADICTED：拦下动作，把不成立的前提和对应的记录编号交给 agent 修改，最多修改 1 次，修改后的动作重新核查；
- 其余结果：直接执行。

```bash
export OPENROUTER_API_KEY=...
python scripts/run_online.py --out runs/online/d1
```

结果写在 `runs/online/d1/summary.md`，内容是两组各赢几局、哪几局被救回或输掉，以及拦截次数和误拦次数。误拦次数用 tracker 在同一段历史上核对得出。

### Repetition check (loop, llmloop)

Why: all 40 games the llm arm loses end at the 50-step limit, 28 of them with the same command
10+ times in a row (`scripts/analyze_losses.py` -> `runs/online/losses.md`). The fixed-condition
checks never see `go to` / `look`, so they cannot touch these loops.

* `loop`: `run_online.loop_check`, no judge and no task knowledge. A command is blocked when it was
  already run, no observation since its last run is new (new = not "Nothing happens" and not seen
  earlier in the episode), and the latest record that did something is the same now as then. The
  agent gets the baseline's revise call with the reason. Offline on the 68 baseline trajectories it
  would block 86 of 350 steps in won games and 1386 of 2150 in lost games; in only 1 case would the
  blocked command actually have shown something new.
* `llmloop`: `loop` first, then the `llm` check for commands that are not a blocked repeat.
* Blocked proposals are replayed: `proposal_would_succeed` and `proposal_would_be_new`.
* `--max-revisions 3` (written as `loop_r3.json` / `llmloop_r3.json`): with one revision 457 of 518
  blocks ended with a replacement that was itself a blocked repeat (executed anyway), so the agent
  alternated between two repeats. From the second revision on, the feedback also lists every command
  already rejected at this step (`rejected_at_this_step`).

    for d in d1 more more2 more3; do for arm in loop llmloop; do
      python scripts/run_online.py \
        --out runs/online/$d --arm $arm
    done; done

### Unvisited-places reminder (explore)

The loop arms did not rescue lost games: blocked agents moved between the same 2-5 places. `explore`
blocks nothing; after the latest observation the agent sees which places listed in the opening
observation it has not visited yet (`run_online.explored`, from the history only).

    python scripts/run_online.py \
      --out runs/online/d1 --arm explore

* `selfexplore`: the same note, but the two lists are written each step by the agent model in a
  separate call (`SELF_PLACES`, operation `judge-places`).
* `onecall` (ablation of selfexplore): no note and no extra call. The agent's own action call gets the
  baseline prompt plus the same bookkeeping request and answers `{"visited", "not_visited", "action"}`
  (`ONECALL_ACTION`, operation `actor-onecall`). The lists are only logged and scored. A step whose
  onecall reply is unusable (e.g. the lists run past the 2048-token limit) uses the baseline's own
  action call instead and is logged with `fallback` in `place_lists`. If onecall wins
  about as many games as selfexplore, splitting bookkeeping from acting is not what helps.
* `onecall_use`: onecall with one sentence changed, "Then propose the command." becomes "Then, based on
  these two lists, propose the command." (`ONECALL_USE_ACTION`, operation `actor-onecall-use`).

    for d in d1 more more2 more3; do
      python scripts/run_online.py \
        --out runs/online/$d --arm onecall
    done

### Online control arms (T0 rule tracker, failure hint)

Same games, actor, cache and 50-step budget as D1; results go next to `d1.json` in the same folders.

    for d in d1 more more2 more3; do for arm in t0 hint; do
      python scripts/run_online.py \
        --out runs/online/$d --arm $arm
    done; done
    python scripts/compare_arms.py runs/online/d1 runs/online/more runs/online/more2 runs/online/more3

* `t0`: block / revise exactly like D1, but the preconditions are decided by `aeda.alfworld.replay`
  (no judge calls). Feedback cites the record that last set the location / the hand.
* `hint`: nothing is checked or blocked; failed steps are shown to the agent with a fixed hint
  (`run_online.HINT`) appended. The environment history is unchanged.
* `compare_arms.py` writes `runs/online/compare.md`: wins, rescued / lost games, steps on games both
  won (with an exact sign test), blocks, new actor requests and judge calls per arm.

### Online arm with model-written conditions (mw)

    python scripts/run_online.py \
      --out runs/online/d1 --arm mw

Before a checked command the agent model writes up to `--mw-k` (3) conditions with the baseline's own
`models.GPUChat.risks()`; D1 verifies each free-text condition (the judge sees only the text, examples
in the same yes/no form). Block / revise as for D1. Scoring: conditions that parse as location / hand
conditions (`aeda.alfworld.parse_claim`) are checked by the tracker; every blocked proposal is replayed
in a fresh env (`proposal_would_succeed`). Results in `<out>/<id>/mw.json`, `<out>/summary_mw.md`.

### Condition writers (aeda/conditions.py) and their offline benchmark

    python scripts/eval_conditions.py --writers risks,v2,v2demo   # -> runs/conditions/report.md
    python scripts/run_online.py --out runs/online/d1 --arm mw --mw-writer v2demo

`risks` = the baseline's own risk generator; `v2` = precondition-only instruction (no effects, goal or later
steps; most-likely-false first); `v2demo` = v2 plus the agent's own one-shot demonstration for the task
family (same text and wording as the agent gets; nothing else is added). The benchmark scores 160 baseline checkpoints (80 failed in the env) against the tracker: required
location / hand conditions covered, failures explained, false-alarm conditions, effects written as conditions.
Online results go to `<out>/<id>/mw_<writer>.json` and `<out>/summary_mw_<writer>.md`.
