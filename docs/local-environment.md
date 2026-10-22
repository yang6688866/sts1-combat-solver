# 这台机器上的开发环境

仓库之外还有一套东西，都在 `E:\sts-devkit\`。这里说清它们是什么、什么时候用，免得下一个接手的人（或下一个会话的我自己）到处翻。

完整说明见 `E:\sts-devkit\README.md`，这里只记会影响**排查和验证**的部分。

## 关键路径

| 路径 | 是什么 |
| --- | --- |
| `E:\games\sts1-combat-solver-main` | 仓库本体 |
| `E:\sts-devkit\decompiled\` | **反编译的原版游戏字节码**，查游戏行为的唯一权威 |
| `E:\sts-devkit\test-logs\` | 玩家真机测试导出的 jsonl / F6 分歧现场 / 历史 jar |
| `E:\sts-devkit\bin\` | `cmake.bat`（去掉 `-A x64`）、`msvc-env.sh` |
| `E:\sts-devkit\cache-reports\` | prompt 缓存账本存档 |

## 游戏日志：三种来源，记录的东西不一样

| 来源 | 位置 | 含什么 |
| --- | --- | --- |
| 行为记录 | `E:\sts-devkit\test-logs\sts1-test-<seed>.jsonl` | 每回合手牌/抽牌/弃牌/消耗快照、出牌、怪物血量。**不含 RNG** |
| F6 分歧现场 | `E:\sts-devkit\test-logs\sts1-state_divergence-*.json` | 完整状态 + **真实 RNG**，可精确重放 |
| 报错全文 | `C:\Users\yang\AppData\Local\STS1CombatSolver\backend.log` | `state_divergence` 的 diff 原文 |
| 完整请求/回复 | `C:\Users\yang\AppData\Local\STS1CombatSolver\runs\` | 带 `rngs` 的原始请求 |

**重放洗牌类问题必须要有 RNG**，光有行为记录不够，得让玩家按 F6 导出，或者去 `runs/` 里找。

## 查游戏行为：别信导出表

`sts_cards.json`、`sts_potions.json` 这类从 Mod 导出的表**只有最终数值，没有逻辑**。卡牌到底按 `costForTurn` 还是 printed cost 计算、被 Confusion 改成 0 费后走哪个分支、`addToBot` 和 `addToTop` 谁先执行 —— 表里全看不出来。

**F55 的 Recycle bug 就是被这种表误导的**：表上写着"获得等于费用的能量"，实际字节码里，费用被改写后走的是另一条分支。

要查就解字节码：

```bash
E:/sts-devkit/decompiled/decompile.sh com/megacrit/cardcrawl/cards/blue/Recycle
```

已解过的类跳过，输出到 `E:\sts-devkit\decompiled\classes\`。那份 README 里记着已解类索引和几个用真 bug 换来的坑（`CardGroup.group` 是顶在前、`costForTurn` 与 `cost` 是两个字段等）。

## 构建：两个必踩的坑

1. **链接的是 `sts_core.lib`，不是新编译的目标文件。** `overlay/build_native.py` 只编译打过补丁的那几个 `.cpp`，其余引擎代码全从 `sts_core.lib` 静态链接。改了别的文件会出现"链接成功但行为不变"，先查这个库是不是旧的（新库在 `Release/` 子目录里）。
2. **游戏运行时 pyd 被 java.exe 锁着**，链接报 `LNK1104`。需要玩家完全退出游戏。

## 改完必须跑的三项

```bash
cmake --build candidates/sts-ironclad-agent/build/engine
ctest --test-dir candidates/sts-ironclad-agent/build/engine -C Release
.venv/Scripts/python.exe tools/check_solver_runtime.py
```

最后一项会校验 pyd 哈希与 `candidates/sts-ironclad-agent/runtime/live-manifest.json` 是否一致。**手工重链后哈希会变，必须重算 manifest**，否则游戏启动即报 `frozen live engine changed`。正常情况下用 `tools/build_solver_runtime.py` 重建，它会一并更新。

解释器一律用 `.venv/Scripts/python.exe`（3.13）。系统 python 是 3.11，import 不到 `slaythespire`。
