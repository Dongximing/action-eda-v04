# ALFWorld 同题型单示范实验

在与无示范实验相同的 12 个 valid_seen 游戏上，先跑完直接执行的 9B，再跑同一 9B 做风险选择与 EDA。每局最多 50 个环境动作，关闭 thinking，温度为 0，OpenRouter 使用 qwen/qwen3.5-9b。优先对 Parasail 发两个真实请求，再依次尝试 SiliconFlow、Darkbloom 和 Together。第一个确认模型、供应商、完整 JSON、关闭 thinking 和 token 用量的节点固定用于这次全部 24 局。实际节点见 routing.json。

## 示范

每个题型固定使用公开 ReAct 提示库中的第一个仅含动作和观察的例子。清洗示范把洗净的生菜放到餐桌，加热示范把加热的鸡蛋放到餐桌，冷却示范把冷却的平底锅放到炉面。从这三条例子生成与当前 agent 相同的 JSON 动作格式，并把放置命令映射为本地 ALFWorld 接受的 `move ITEM to DEST`。示范命令、观察和来源在 [one_shot_examples.json](one_shot_examples.json) 中。

这一设置沿用 [Verify–Backtrack Loop 附录 F.3](https://arxiv.org/html/2610.41564v1) 的按题型单示范设计，具体三条取自 [ReAct 的固定版本](https://github.com/ysymyth/ReAct/blob/6bdb3a1fd38b8188fc7ba4102969fe483df8fdc9/prompts/alfworld_3prompts.json)。两组主 agent 每次提出动作时收到相同的题型示范。EDA 的记录编号和审计证据只来自当前局。复核仍使用上一轮的提示。

## 启动

在终端中运行 `python3 run_one_shot.py`，按提示输入 OpenRouter key。启动器会在后台依次跑两组，完成后退出。中断后用同一条命令续跑。输出保存在相邻的 `alfworld-9b-oneshot-alternate` 目录。

`baseline.summary.json` 保存 baseline 阶段的汇总。`summary.json` 汇总当前两组的成功数、单独运行的输入和输出 token，以及服务端实际回报的调用用量。两组遇到相同输入时复用相同动作，各自的独立用量仍计入产生该动作的请求。每局逐步记录写入 `gameXX/episode_start/*.trajectory.jsonl`，包含示范 ID、执行动作、环境返回、审计、终局和用量。
