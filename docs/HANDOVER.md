# 交接（2026-10-23）

给下一个在这个工作区接手的人（或下一个对话）。先读这份，再读 `docs/notes/2026-10-23.md`（今天做了什么）
和 `docs/local-environment.md`（怎么跑、日志在哪、坑在哪）。

## 一句话状态

机器人（Defect）线的牌与专属遗物已按字节码逐项核对并补齐测试，**只差真机验证**。代码在
`defect/m3a-orb-skeleton`，HEAD `8105e3c`，工作区干净，本地比 origin 多 1 个提交（网络不通没推）。

## 硬要求（先看这个，别踩）

1. **一切以游戏字节码为准**。`sts_cards.json`、wiki、牌面描述都不算依据——它们有最终数字，没有决定
   数字何时生效的分支。`AGENTS.md` 末尾写着这条。反编译工具在仓库外
   `E:\sts-devkit\decompiled\decompile.sh <类路径>`。
2. **一个 PR 一个职业的一个小步**，不夹带无关修复、不重构共享代码、不改铁甲战士行为。见
   `CONTRIBUTING.md`。
3. **仓库里不能有游戏代码**：不贴反编译片段、不提交 jar/资源，夹具只留状态数字和 ID。
4. **每项新实现都要有 CTest**，模板 `tests/pen_nib_test.cpp`。
5. **改完必须跑全套**（缺一样都可能被 CI 或游戏卡住）：

   ```
   cmake --build candidates/sts-ironclad-agent/build/engine --config Release   # 必须带 --config Release
   ctest --test-dir candidates/sts-ironclad-agent/build/engine -C Release
   .venv/Scripts/python.exe tools/build_solver_runtime.py
   .venv/Scripts/python.exe tools/check_solver_runtime.py
   .venv/Scripts/python.exe tools/check_backend_protocol.py
   .venv/Scripts/python.exe tools/coverage_manifest.py --check
   ```

   **不带 `--config Release` 会默认编 Debug，在 pybind11 的 `stl_bind.h` 报 `error C2001: 常量中有
   换行符`——看着像代码坏了，其实是配置选错。**

## 三个必须知道的环境事实

- **解释器**：`.venv/Scripts/python.exe`（3.13）。系统 `python` 是 3.11 Anaconda，`import slaythespire`
  会失败。
- **`overlay/build_native.py` 只编译打过补丁的那几个 .cpp**，其余引擎文件从 `sts_core.lib` 静态链接。
  改了引擎而行为没变，先查这里链接的是不是旧库（Windows 下真文件在 `build/engine/Release/`）。
- **手工重链后必须重算 `runtime/live-manifest.json` 的哈希**，否则游戏启动抛
  `ValueError: frozen live engine changed`。用 `tools/build_solver_runtime.py` 会自动处理。
- **游戏开着的时候 java.exe 锁 pyd**，链接报 `LNK1104`，只能让玩家退游戏。

## 日志在哪

| 要什么 | 路径 |
| --- | --- |
| 报错全文 | `C:\Users\yang\AppData\Local\STS1CombatSolver\backend.log` |
| 行为记录（有状态、无 RNG） | `E:\sts-devkit\test-logs\sts1-test-<seed>.jsonl`，用户新给的会丢在桌面 `sts1-dev-defect` |
| F6 导出的分歧快照（**有真实 RNG**） | 同上目录，`sts1-state_divergence-*.json` |
| 完整请求/回复 | `%LOCALAPPDATA%\STS1CombatSolver\runs\` |

排查用的诊断脚本在 `tools/diagnostics/`，路径由 `_paths.py` 统一（会读环境变量 `STS_TEST_LOGS`）。

## 接下来做什么（按优先级）

1. **实机验证**。这是唯一的空白。开 mod 打一局，重点出 Bullseye、Reboot、X 费牌（Tempest /
   Multi-Cast / Recycle），最好带上 Inserter 或 Cables。现在这堆改动**只有单测背书**。
2. **补真机夹具**。`fixtures/bug-reports/` 还是 v0.7.0 的两个。Reboot / Cables / floor 39 三个 bug
   都只有单测——而 Reboot 第一次修复正是「单测全绿但假设是错的」翻车的。
3. 网络恢复后推 `8105e3c`。
4. 回赠上游前精简分支（96 文件 2.3 万行里约 24 个一次性脚本 + 8 个 wiki 数据表要处理），见
   `docs/known-gaps.md` §4.1。

## 已知缺口与设计取舍

`docs/known-gaps.md` 是权威清单。里面两条最容易误判成 bug 的：

- 铺垫牌（Focus／姿态／宝珠）在未结束节点不计价值——**是搜索估值的取舍，不是缺陷**，维护者文档
  `docs/multi-character.md` §2.3 已承认。
- 满血时偏向格挡抽牌——同源。

## 用户怎么协作

扫一眼 `git log --oneline -10` 和 `docs/notes/` 就能看出节奏：用户报 bug（给 jsonl 和/或 F6 导出），
这边定位、按字节码改、补测试、重建运行时、报告；用户再真机复测。用户明确要求**一步一个脚印、
按 PR 标准来，不要偷懒跳过测试**。
