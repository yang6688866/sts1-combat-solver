# 诊断脚本

这些脚本**不是**构建或 CI 的一部分，也永远不会被 `ctest` 或 `overlay/build.py` 调用。它们是排查真机 `state_divergence` 报错时用的工具：把游戏日志里的一次决策重建出来，问引擎它认为结果应该是什么，再和游戏记录的答案对比。

全部用仓库的 3.13 解释器跑：

```bash
.venv/Scripts/python.exe -X utf8 tools/diagnostics/<脚本>.py --help
```

## 目录

| 路径 | 内容 |
| --- | --- |
| `_search_plan.py` | 从一条 `card_play` 记录重建局面，问**真实原生搜索**它的计划是什么 |
| `_plan_cards.py` | 同上，但用游戏数据表修正卡牌费用（日志只存卡名不存费用） |
| `_card_usage.py` | 全牌库统计：每张牌「在手且付得起」vs「实际打出」的次数 |
| `_card_pick.py` | 对出牌率低于下限的牌，找它出现过的局面，问求解器为什么不选它 |
| `_card_stats.py` | 每张牌在真实决策点被提供/被打出的次数 |
| `cases/` | 具体 bug 的复现脚本，按问题分组：`_barrage*` 出牌率、`_cables*` 与 `_floor39*` 的 Cables 伤害、`repro_reboot.py` 的洗牌堆方向、`_cmp_jars.py` 的 jar 比对 |
| `data/` | 从游戏导出的卡牌/药水/能力/遗物数据表，`_plan_cards.py` 用来查费用 |

## 用法前提

日志有两种，路径不同：

- **行为记录**：`C:\Users\yang\Desktop\sts1-dev-defect\sts1-test-<seed>.jsonl`，含每回合的 hand/draw/discard/exhaust 快照，**不含随机数状态**
- **完整请求/回复**：`C:\Users\yang\AppData\Local\STS1CombatSolver\runs\`，含 `rngs`
- **报错全文**：`C:\Users\yang\AppData\Local\STS1CombatSolver\backend.log`
- F6 导出的分歧现场：`sts1-state_divergence-<seed>-F<n>-v<ver>.json`，含真实随机数，可完整重放

重放洗牌类问题必须要带 `rngs` 的来源（F6 导出或 `runs/`），光有行为记录不够。

`cases/` 里的脚本多数把日志绝对路径写死在文件头，换机器或换日志要改那一行。
