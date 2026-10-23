# 交接（2026-10-23）

给下一个在这个工作区接手的人（或下一个对话）。先读这份，再读 `docs/notes/2026-10-23.md`（今天做了什么）
和 `docs/local-environment.md`（怎么跑、日志在哪、坑在哪）。

## 一句话状态

机器人（Defect）线的牌、数值与专属遗物已按字节码逐项核对并补齐测试，**只差真机验证**。代码在
`defect/m3a-orb-skeleton`，HEAD `7dc3eff`，工作区干净，已推 origin。**还没对上游发 PR**。

## 按 PR 标准，接下来做什么

依据是 `CONTRIBUTING.md`（分支和 PR / 代码要求 / CI 要求三节）和 `docs/multi-character.md` §4 的 M3
检查表。每条都标了依据条款，能查到原文。

### 阻断项（不解决 PR 一定被打回）

1. **另开一个干净分支。** CONTRIBUTING「分支和 PR」：*一个 PR 只做一个职业的一个小步，不顺手重构共享
   代码，也不夹带无关修复*；分支名写职业和小步，例如 `silent/m1a-starter-cards`。
   现状：`defect/m3a-orb-skeleton` 比 `upstream/main` 多 **88 个文件、24032 行**，里面混了诊断脚本、
   中文 wiki 数据表、文档、构建脚本。要做的是从 `upstream/main` 拉一条 `defect/m3a-1-cards`，只挑这些：
   - `candidates/.../src/combat/characters/DefectCards.cpp`、`src/combat/{Actions,BattleContext,CardInstance,CardManager,Player,Monster}.cpp`
     及对应头文件里**机器人相关**的改动
   - `tests/` 下 7 个 defect/orb 测试 + `CMakeLists.txt` 的注册
   - `tests/character_dispatch_test.cpp`（我们要改的地方见下一条）
   - `overlay/test/recorded/DEFECT/` 三个夹具 + `tools/check_snapshot_import.py`
   - `overlay/build_native.py`（`sts_core.lib` 路径修复，见「顺手发现」）
   - `overlay/coverage_manifest.json`
   **挑的时候注意拆分**：`f91059f` 一个提交里混了牌、遗物、X 费、洗牌四件事，回赠要拆成独立提交。

2. **`tests/character_dispatch_test.cpp` 的 DEFECT 用例不能一删了之，先问维护者。** CONTRIBUTING 代码要求
   第 5 条：*若你实现的牌正好是 `character_dispatch_test.cpp` 或 `tools/check_backend_protocol.py` 里当作
   "未实现"示例的牌，换成同职业同类型的另一张未实现牌，并在 PR 里说明*。

   实测结果（这条比预想的难）：
   - 上游那两条是 `{DEFECT, CardId::ZAP}` 和 `{DEFECT, CardId::BALL_LIGHTNING}`，本意是攻击和技能各一条。
     但字节码里 `Zap` 的 `CardType` 是 **SKILL**、`BallLightning` 是 **ATTACK**——上游注释把两行的类型
     写反了。我们两条都实现了，所以两条都得换。
   - **机器人奖励池 71 张 + 起始牌 4 张现在全部实现**，jar 的 `cards/blue/` 76 个类里没有一张未实现的牌
     （唯一的 `Impulse` 是未使用类，不在 `cardStringIds`）。也就是说**不存在"同职业同类型的另一张未实现
     牌"可换**。
   - `tools/check_backend_protocol.py:69` 的未实现示例用的是 `Neutralize`（静默）和 `Tingsha`（遗物），
     没有机器人牌，不用改。

   所以现在分支里是把那两行注释掉删了。PR 里要把这段写清楚：*要求换牌，但机器人牌已全部实现，无牌可换；
   保留的共享 switch 检查仍然覆盖"已实现的牌被正确处理"*。要么维护者给个处理办法（例如允许删、或允许
   用 `SILENT` 的一条补攻击/技能覆盖），要么这条得等维护者回话。**建议动手前先发个 issue 问。**

3. **补真机夹具。** CONTRIBUTING 代码要求第 5 条：*每个新实现至少一个原生夹具覆盖它*；M3 每小步的检查
   表（`docs/multi-character.md` §4）还要 *至少一组原版夹具 + 快照往返测试 + ID 映射*。
   现状：`fixtures/bug-reports/` 还是 v0.7.0 的两个；`overlay/test/recorded/DEFECT/` 的三个是**导入中间层**
   夹具（`tools/check_snapshot_import.py` 用），不是「原版结果作为真值」的重放夹具。Reboot、Cables、
   X 费、Bullseye、Inserter 五个修复都只有单测。F6 导出在 `E:\sts-devkit\test-logs\`，挑进仓库时只留
   状态数字和 ID。

4. **不进 PR 的东西**：`tools/diagnostics/`（含 `data/` 那 468KB 中文 wiki 导出表）、`docs/notes/`、
   `docs/HANDOVER.md`、`docs/known-gaps.md`、`docs/upstream-handoff.md`、`overlay/backend_defect_test.py`
   及其构建开关、`tools/make_test_backend.py`、`tools/check_defect_*.py`。`CONTRIBUTING` 代码要求第 2 条
   只禁游戏代码；这些是「与本小步无关」，归第「不夹带无关修复」那条。

### 内容项

5. **PR 说明要写清四件事**（CONTRIBUTING「分支和 PR」）：实现了哪些牌/遗物/能力；每项依据的 **Java 类名
   和方法名**（只写名字，不贴代码）；覆盖清单的变化；新增了哪些夹具和测试。依据现在散在
   `docs/notes/` 里，要提炼成 PR 正文。已知要引用的类：`Reboot`、`LockOn`、`Inserter`、
   `ShuffleAllAction`、`PutOnDeckAction`、`DrawCardAction`、`ImpulseAction`、`Tempest`、`MultiCast`、
   `Recycle`、`AllForOneAction`、`ReinforcedBody`、`GoldPlatedCables`。
6. **如实写出没修的缺口**：`cardColors[]` 里 `BUFFER`/`COMPILE_DRIVER` 被标 `PURPLE`、
   `BRILLIANCE`/`COLLECT` 被标 `BLUE`（不影响战斗，只影响变化牌池；属共享表，按「不顺手重构共享代码」
   单独说明不修）；铺垫牌估值、满血偏格挡两条属维护者已承认的搜索取舍（`docs/multi-character.md` §2.3），
   PR 里说明「不在本步范围」。
7. **`tools/coverage_manifest.py` 的改动要不要随 PR 走，先问维护者。** 现在它只对 `IRONCLAD` 查缺口，
   输出 `IRONCLAD has no gaps`；`class_relic_tests` 段是本步新加的（遗物要有 CTest 才算出覆盖）。
   两者都算共享工具改动，按「不顺手重构共享代码」得单独确认。

### 交叉验证项

8. **CI 是 3 系统 × 2 Python 版本**（`.github/workflows/native-runtime.yml`：`ubuntu-24.04` / `macos-14` /
   `windows-2022` × 3.11 / 3.14）。本机只验证过 Windows；`overlay/build_native.py` 里 `/O2 /utf-8 /EHsc
   /bigobj`、`-A x64` 是 Windows 专用分支，Linux/macOS 分支没跑过。推 PR 前最好在别的系统上过一遍，
   或者先推 draft 看 CI 报什么。
9. **推 PR 前本地跑全套**（CONTRIBUTING「CI 要求」列的五行，`truth_calibration` 那行需要自己的适配器）。

---

## 硬要求（先看这个，别踩）

1. **一切以游戏字节码为准**。`sts_cards.json`、wiki、牌面描述都不算依据——它们有最终数字，没有决定
   数字何时生效的分支。`AGENTS.md` 末尾写着这条。反编译工具在仓库外
   `E:\sts-devkit\decompiled\decompile.sh <类路径>`。
2. **一个 PR 一个职业的一个小步**，不夹带无关修复、不重构共享代码、不改铁甲战士行为。
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

---

## 已知缺口与设计取舍

`docs/known-gaps.md` 是权威清单。里面两条最容易误判成 bug 的：

- 铺垫牌（Focus／姿态／宝珠）在未结束节点不计价值——**是搜索估值的取舍，不是缺陷**，维护者文档
  `docs/multi-character.md` §2.3 已承认。
- 满血时偏向格挡抽牌——同源。

## 顺手发现但没动的

- `include/constants/Cards.h` 的 `cardColors[]` 有两行错位（`BUFFER`/`COMPILE_DRIVER` 标 PURPLE，
  `BRILLIANCE`/`COLLECT` 标 BLUE）。`getCardColor()` 只被变化牌/随机生成牌池用，不进战斗结算。属共享
  表，按 CONTRIBUTING 不夹带。
- `overlay/build_native.py` 曾硬编码 `build/engine/sts_core.lib`，WIN32 布局下真文件在
  `build/engine/Release/`。已在 `060d058` 修成两处都找。这是「链接成功但行为不变」的经典陷阱，
  以后遇到先查这里。

## 用户怎么协作

扫一眼 `git log --oneline -10` 和 `docs/notes/` 就能看出节奏：用户报 bug（给 jsonl 和/或 F6 导出），
这边定位、按字节码改、补测试、重建运行时、报告；用户再真机复测。用户明确要求**一步一个脚印、
按 PR 标准来，不要偷懒跳过测试**。
