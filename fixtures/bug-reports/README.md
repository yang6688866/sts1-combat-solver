# 真机夹具

真实游戏里抓到的分歧现场，用来防止"单元测试写错了假设"这类翻车。

## 格式

全部是 `sts1-run-v1`：面板上的 F6 导出按钮直接写出的文件。结构是

```
{format, purpose, seed, metadata, events, recent_battles, shop_history}
```

其中 `events` 是时间线，关键的两类：

- `request` / `reply`：求解器收到的局面和它给出的答案，**带完整 RNG 状态**（`rngs`）
- `fault`：`state_divergence` 的原文，`message` 里是被判为不一致的字段

所以一个夹具既能重放"当时求解器看到了什么"，也能看到"它算错了多少"。

## 为什么需要它

单元测试断言的是**开发者以为的游戏规则**。Reboot 的第一次修复就是教训：测试断言"手牌按顺序进抽牌堆"，测试全绿，但游戏实际是随机的——错的假设被测试保护了起来。

真机夹具断言的是**游戏实际干了什么**，不受开发者理解偏差影响。

## 现有夹具

| 文件 | 楼层 | 对应 bug | fault 里的判据 |
| --- | --- | --- | --- |
| `sts1-state_divergence-...-F39-v0.9.1-1021-2230.json` | 39 | Cables 第二次被动延后入队 | `/monsters/0/hp` 游戏 24 vs 模拟 21 |
| `sts1-state_divergence-...-F39-v0.9.1-1021-2333.json` | 39 | 同上，第二次复现（含 2 个 fault） | 同上 |
| `sts1-state_divergence-...-F55-v0.9.1-1022-0006.json` | 55 | X 费 / Recycle 选牌 | `/player/energy` 游戏 0 vs 模拟 -2 |
| `sts1-run-3727704048308229936-F18-v0.7.0-*.json` | 18 | v0.7.0 时期的历史夹具（两个时间点） | — |

前三个是 v0.9.1 时期、修复前抓的。**修复后没有重新抓**：修复的验证靠的是单元测试和 `ctest`，夹具的作用是留下"当时错成什么样"的证据。

## 怎么用

目前 `ctest` 不跑夹具（它们体积大、需要人工判断）。要复现时手动来：

```bash
# 看某个夹具里所有 fault
.venv/Scripts/python.exe -c "
import json, sys
d = json.load(open(sys.argv[1], encoding='utf-8'))
for e in d['events']:
    if e['k'] == 'fault':
        print(e['f'], e['message'][:120])
" fixtures/bug-reports/<文件>
```

要重放到引擎里，照 `tools/diagnostics/_search_plan.py` 的写法重建局面：从 `events` 里挑一条 `reply` 取完整状态和 `rngs`，喂给 `slaythespire.BattleContext`。环境说明见 `docs/local-environment.md`。

## 加新夹具

玩家在游戏里按 F6，文件落在 `%LOCALAPPDATA%\STS1CombatSolver\`。挑有 `fault` 的复制进来，文件名保持原样（`sts1-state_divergence-<seed>-F<n>-v<ver>-<date>-<time>.json`），在上面表格里加一行说明它抓的是什么问题。
