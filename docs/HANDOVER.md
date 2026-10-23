# 交接（2026-10-23）

给下一个在这个工作区接手的人（或下一个对话）。先读这份，再读 `docs/notes/2026-10-23.md`（今天做了什么）
和 `docs/local-environment.md`（怎么跑、日志在哪、坑在哪）。

## 一句话状态

机器人（Defect）线的牌、数值、专属遗物与分发测试已按字节码逐项核对并补齐测试，**只差真机验证**。代码在
`defect/m3a-orb-skeleton`，工作区干净。CTest 16/16、运行时三项检查全 PASS、
`tools/check_defect_truth.py` PASS。
**本地领先 origin 2 个提交（`07699bd`、`ffbedbc`）未推**——推的时候网络不稳，要临时挂代理
`HTTPS_PROXY=http://127.0.0.1:7890`。**还没对上游发 PR。**

## 仓库结构

代码分两层：**Java 层（Mod 本体）** 和 **C++/Python 层（求解器）**。两层通过 stdin/stdout 的 JSON 协议
通信，`overlay/backend.py` 是 Python 侧入口。

### 顶层

| 目录 | 跟踪文件 | 作用 |
| --- | --- | --- |
| `overlay/` | 121 | **Java 层 Mod 本体**：面板、按键、事件规则、后端启动 |
| `candidates/sts-ironclad-agent/` | 132 | **求解器**：C++ 战斗引擎 + Python MCTS/导入层 |
| `tools/` | 79 | 构建脚本、各种 `check_*.py`、诊断脚本 |
| `fixtures/` | 32 | 夹具：`bug-reports/`（真机分歧现场）、`calibration/`、`combat-exams/` |
| `references/` | 40 | `CommunicationMod/`（原作者仓库本来就有，**别动**） |
| `docs/` | 21 | 文档。`architecture.md` 是总设计，`multi-character.md` 是四职业分工 |
| `assets/` | 1 | 一张图 |
| `.github/` | 3 | CI（3 系统 × 2 Python 版本） |

### `overlay/`（Java 层，149M 但只有 121 个文件进 git）

| 子目录 | 作用 |
| --- | --- |
| `src/sts1solver/` | 39 个 `.java`：`PanelCanvas`（面板）、`BackendClient`/`BackendRuntime`（启动 Python）、`EventRules`、`Foresight`、`MapExport`、`Distill2` 等 |
| `test/` | 45 项 Java 自检 + JSON 夹具。`test/recorded/` 是**我们加的**导入夹具（见下） |
| `resources/` | 7 个：本地化 tsv、`search_contract.json`、`distill2-weights.bin`（17M，上游自带的权重，不是我加的） |
| `nn/` | `scorer-v2.bin` |
| `build/` | **不进 git**。javac 产物、`STS1CombatSolver.jar`、`native/overlay_search.pyd` |
| `runtime/` | **不进 git**。`backend.log` 和 `runs/` 落在这 |

顶层散放的 `.py` 里，`backend.py` 是 Python 后端入口，`build_native.py` 生成并编译原生扩展，
`runtime_files.py` 定义哪些文件要打进 jar。

### `candidates/sts-ironclad-agent/`（求解器）

| 子目录 | 跟踪文件 | 作用 |
| --- | --- | --- |
| `combat_engine/` | 115 | C++ 引擎 + CTest。**改牌/改机制都在这** |
| `steam/` | 11 | `steam_mcts.py`（MCTS）、`live_search.py`、`state_export_mod/`（游戏内导出 mod）、`native/` |
| `sim_patch/` | 5 | `alignment/`（ID 映射）、`parity/`（一致性校验） |
| `build/` | 0 | **不进 git**。cmake 产物，真库在 `build/engine/Release/` |
| `runtime/` | 0 | **不进 git**。编好的 pyd + `live-manifest.json`（哈希清单） |

### 引擎内部分层（`combat_engine/combat4r/engine-source/`）

```
include/ 和 src/ 一一对应，改实现要同时看头文件
├── combat/      战斗核心：BattleContext（总调度）、CardManager（牌堆）、Player、Monster、
│                 Actions（动作队列）、CardInstance；characters/ 下按职业分文件
│                 → DefectCards.cpp 就是机器人 74 张牌的实现
├── constants/   静态表：Cards.h（371 张牌的枚举/费用/类型）、CardPools.h（牌池）、
│                 Relics.h、MonsterEncounters.h …  ← 改表要小心，属共享代码
├── game/        GameContext（局外状态）、Random（Java 同款 LCG）、Deck、Map、Shop
├── sim/search/  搜索算法：ScumSearchAgent2、Action（动作编解码）
└── bindings/    slaythespire.cpp — pybind11 导出，Python 能调什么看这里

tests/           16 个 CTest，每个 .cpp 一个可执行文件，模板 pen_nib_test.cpp
third_party/     nlohmann（唯一第三方依赖）
CMakeLists.txt   加新测试在这注册（三行）
```

### 找东西的路线

| 想改什么 | 去哪 |
| --- | --- |
| 某张机器人牌的效果/数值 | `src/combat/characters/DefectCards.cpp` |
| 起始牌（打击/防御） | `src/combat/BattleContext.cpp` 的共享 switch（四个职业共用） |
| 牌的费用/类型 | `include/constants/Cards.h` 的 `getEnergyCost` / `cardTypes[]` |
| 球（Lightning/Frost/Dark/Plasma）机制 | `src/combat/Actions.cpp`、`src/combat/Player.cpp` |
| 遗物 | `src/combat/BattleContext.cpp` 的 `initRelics` 和各钩子 |
| 搜索/估值策略 | `src/sim/search/` **（CONTRIBUTING 禁止顺手改）** |
| 面板显示 | `overlay/src/sts1solver/PanelCanvas.java` |
| Python 侧 MCTS | `candidates/sts-ironclad-agent/steam/steam_mcts.py` |

### 文档索引（`docs/` 21 个文件 = 20 份 md + 1 张图，别乱翻）

上游写的（别改，先读再动手）：

| 文件 | 回答什么问题 |
| --- | --- |
| `architecture.md` | 总设计：四层结构、模块边界 |
| `multi-character.md` | 四职业范围与分工，§4 是 M3 检查表（PR 标准的来源之一） |
| `truth-calibration.md` | 真值校准的格式、运行器、24 个校准用例 |
| `ui-development.md` | 改面板/模式/按键前必读 |
| `product.md` | 产品 spec，「Play modes and player control」 |
| `event-rules.md` | 战士全自动爬塔的事件规则单 |
| `outside-rules.md` | 局外规则校对单（683 行，最大的一份） |
| `mod-pair-ci.md` | 双 mod 构建 CI 怎么跑 |
| `releases/0.8.0-beta.1.md` | 上游发版说明 |

我们写的：

| 文件 | 回答什么问题 |
| --- | --- |
| `HANDOVER.md` | **本文件**，接手先读 |
| `local-environment.md` | 仓库外的路径、日志三来源、构建坑 |
| `known-gaps.md` | 「我们知道但还没做」的权威清单，带出处 |
| `upstream-handoff.md` | 回赠上游前的文件核对清单（**不是给上游看的**） |
| `notes/2026-10-16/18/19.md`、`notes/MEMORY.md` | WorkBuddy 时期的项目笔记，历史参考 |
| `notes/2026-10-22.md`、`notes/2026-10-23.md` | 这两天做了什么 |

### 两套夹具别搞混

| 位置 | 谁写的 | 是什么 |
| --- | --- | --- |
| `overlay/test/recorded/DEFECT/` | **我们** | 三条 `game_state` 原样导出，供 `tools/check_snapshot_import.py` 验证导入层。不是「原版结果作真值」的重放夹具 |
| `fixtures/bug-reports/` | 混：2 个上游 v0.7.0 + 3 个我们加的 | F6 导出的 `sts1-run-v1`，含 `request`/`reply`（**带真实 RNG**）和 `fault` 原文。`README.md` 有逐文件说明 |
| `fixtures/calibration/`、`fixtures/combat-exams/` | 上游 | 维护者的，别改 |

## 仓库之外：`E:\sts-devkit\`

排查和取证用的东西都在这里，**不进 git**（版权 + 体积）。`E:\sts-devkit\README.md` 是索引，
`docs/local-environment.md` 只讲了会影响排查的那几项，下面这份是全的。

| 目录 | 体积 | 是什么 |
| --- | --- | --- |
| `decompiled\` | 2.2M | **原版游戏字节码**，行为的唯一权威。`classes\` 下已解 111 个 `.txt`，`README.md` 有已解类索引和 4 条用真 bug 换来的坑 |
| `test-logs\` | 80M | 玩家真机导出的 10 个 `sts1-test-*.jsonl`、3 个 F6 分歧快照、5 个历史 jar、安装/测试说明、`待办-已知缺口.md`（旧的，已并入 `docs/known-gaps.md`） |
| `tools\` | 80K | **写测试时的取证工具**，见下表。`card-numbers.txt` 是权威数值表 |
| `bin\` | 18K | `cmake.bat`（剥掉 `-A x64` 转发给 venv 的 cmake）、`msvc-env.sh`、`build_values_test.bat`、`rebuild_runtime.bat` |
| `cache-reports\` | 48K | prompt 缓存账本存档，含 2026-10-22 的基线 |
| `jar-scratch\` | 848M | jar 解包与抓取残留，**只读存档，可以整目录删**，删了不影响任何流程 |

### `E:\sts-devkit\tools\`

全部从字节码取数，`.venv/Scripts/python.exe -X utf8` 跑。

| 脚本 | 干什么 |
| --- | --- |
| `cardbytecode.py` | 共享解析库：`methods()`、`body(text, signature, cls=None)`、`instructions()`、`card_game_id(ctor)` |
| `card-numbers.txt` | **权威数值表**，78 行 = 2 行表头 + 76 个类，格式 `card cost dmg block magic`，`->` 是升级后值。写数值测试直接照抄，别重新生成 |
| `extract_card_numbers.py` | 生成上表。循环或派生出来的值打 `?`，**绝不猜** |
| `card_numbers2.py` | 同上但给绝对值（`cost base->up`），替代旧表只有增量的版本 |
| `card_table_cpp.py` | 用 `cardStringIds[]`↔`cardEnumStrings[]` 逐位对齐把游戏 ID 映射到引擎枚举名 |
| `verify_card_numbers.py` | 拿表去校验 `DefectCards.cpp`：攻击必须排队伤害动作、每个 `up ? A : B` 必须是字节码产出的 (base,up) 对（能抓出把 9/12 写成 `up ? 7 : 9`）、变化的对必须可见、base≥2 必须出现 |
| `compare_card_numbers.py` | 表 vs 源码的差异清单 |
| `card_effects.py` | dump `use()` 的调用顺序与常量，供人工核对 |

两个坑写在 `cardbytecode.py` 的 docstring 里，踩过一次别再踩：javap 的方法**没有闭合大括号**（必须按声明行切分）；
`upgradeBaseCost` 的参数是**绝对新费用**，而 `upgradeDamage/Block/MagicNumber` 是**增量**。

### 反编译怎么用

```
E:/sts-devkit/decompiled/decompile.sh com/megacrit/cardcrawl/cards/blue/Recycle
E:/sts-devkit/decompiled/decompile.sh com/megacrit/cardcrawl/actions/defect/      # 整个包，尾斜杠
```

输出到 `classes/<包路径>.txt`；已解的跳过，`--force` 重解。`javap -p -c`（**没有 `-constants`**），
因为反编译成 Java 源码会重新排版、丢掉 `addToBot`/`addToTop` 的先后和字段读写时机，而卡牌 bug
几乎全是这两样引起的。`STS_GAME_DIR` / `STS_JDK` 可覆盖默认路径。

## 按 PR 标准，接下来做什么

依据是 `CONTRIBUTING.md`（分支和 PR / 代码要求 / CI 要求三节）和 `docs/multi-character.md` §4 的 M3
检查表。每条都标了依据条款，能查到原文。

### 阻断项（不解决 PR 一定被打回）

1. **另开一个干净分支。** CONTRIBUTING「分支和 PR」：*一个 PR 只做一个职业的一个小步，不顺手重构共享
   代码，也不夹带无关修复*；分支名写职业和小步，例如 `silent/m1a-starter-cards`。
   现状：`defect/m3a-orb-skeleton` 比 `upstream/main` 多 **88 个文件、24247 行**，里面混了诊断脚本、
   中文 wiki 数据表、文档、构建脚本。要做的是从 `upstream/main` 拉一条 `defect/m3a-1-cards`，只挑这些：
   - `candidates/.../src/combat/characters/DefectCards.cpp`、`src/combat/{Actions,BattleContext,CardInstance,CardManager,Player,Monster}.cpp`
     及对应头文件里**机器人相关**的改动
   - `tests/` 下新增的 7 个 defect/orb 测试 + `CMakeLists.txt` 的注册
   - `tests/character_dispatch_test.cpp`（见下面「已改完、PR 里必须解释的一项」）
   - `overlay/test/recorded/DEFECT/` 三个夹具 + `tools/check_snapshot_import.py`
   - `overlay/build_native.py`（`sts_core.lib` 路径修复，见「顺手发现」）
   - `overlay/coverage_manifest.json`
   **挑的时候注意拆分**：`f91059f` 一个提交里混了牌、遗物、X 费、洗牌四件事，回赠要拆成独立提交。

2. **补真机夹具。** CONTRIBUTING 代码要求第 5 条：*每个新实现至少一个原生夹具覆盖它*；M3 每小步的检查
   表（`docs/multi-character.md` §4）还要 *至少一组原版夹具 + 快照往返测试 + ID 映射*。
   现状：`fixtures/bug-reports/` 有 5 个——2 个上游 v0.7.0 的，加 3 个我们补的 v0.9.1 现场（F39 Cables 两次、
   F55 X 费/Recycle）。但那 3 个都是**修复前**抓的「错成什么样」，没有修复后重抓的；而且 Reboot、Bullseye、
   Inserter 三个修复一个夹具都没有。`overlay/test/recorded/DEFECT/` 的三个是**导入中间层**夹具
   （`tools/check_snapshot_import.py` 用），不是「原版结果作为真值」的重放夹具。F6 导出在
   `E:\sts-devkit\test-logs\`，挑进仓库时只留状态数字和 ID。

3. **不进 PR 的东西**：`tools/diagnostics/`（含 `data/` 那 468KB 中文 wiki 导出表）、`docs/notes/`、
   `docs/HANDOVER.md`、`docs/known-gaps.md`、`docs/upstream-handoff.md`、`overlay/backend_defect_test.py`
   及其构建开关、`tools/make_test_backend.py`、`tools/check_defect_*.py`。`CONTRIBUTING` 代码要求第 2 条
   只禁游戏代码；这些是「与本小步无关」，归第「不夹带无关修复」那条。

### 已改完、PR 里必须解释的一项

**`tests/character_dispatch_test.cpp`（`b6c0587`）。** CONTRIBUTING 代码要求第 5 条：*若你实现的牌正好是
`character_dispatch_test.cpp` 或 `tools/check_backend_protocol.py` 里当作"未实现"示例的牌，换成同职业同
类型的另一张未实现牌，并在 PR 里说明*。

规则的前提在我们这一步不成立，实测依据：
- 上游那两条是 `{DEFECT, CardId::ZAP}` 和 `{DEFECT, CardId::BALL_LIGHTNING}`，注释标成 attack 和 skill。
  字节码里实际相反：`Zap` 是 **SKILL**、`BallLightning` 是 **ATTACK**——上游把两行的类型写反了。
- **机器人 71 张奖励牌 + 4 张起始牌全部实现**；jar 的 `cards/blue/` 76 个类里唯一没有引擎 case 的是
  `Impulse`，而它是未使用类、不在 `cardStringIds`。所以**没有"同职业同类型的另一张未实现牌"可换**。
- `tools/check_backend_protocol.py:69` 的未实现示例是 `Neutralize`（静默）和 `Tingsha`（遗物），
  没有机器人牌，那处不用改。

改法：把用例拆成两组。`unimplemented[]` 保留静默三张 + 观者三张（攻击/技能/能力各一），断言打出去报
`unimplemented card`；`implemented[]` 放机器人三张（Ball Lightning 攻击 / Zap 技能 / Defragment 能力），
断言**不**报该错、正常执行。两组都保持三种类型覆盖，机器人这三张既补上原两行的类型覆盖，也把
"已实现的牌不该被误报"变成断言。

PR 正文里必须写清这段：*要求换牌 → 机器人无牌可换 → 改成断言已实现的牌正常运行*。这不是绕过要求，
是把原本由那两行承担的两个职责（类型覆盖、拒绝未实现）分开承担。**如果维护者更想保留"三种类型都被
拒绝"的机器人样本，需要他给出处理办法。**

### 内容项

1. **PR 说明要写清四件事**（CONTRIBUTING「分支和 PR」）：实现了哪些牌/遗物/能力；每项依据的 **Java 类名
   和方法名**（只写名字，不贴代码）；覆盖清单的变化；新增了哪些夹具和测试。依据现在散在
   `docs/notes/` 里，要提炼成 PR 正文。已知要引用的类：`Reboot`、`LockOn`、`Inserter`、
   `ShuffleAllAction`、`PutOnDeckAction`、`DrawCardAction`、`ImpulseAction`、`Tempest`、`MultiCast`、
   `Recycle`、`AllForOneAction`、`ReinforcedBody`、`GoldPlatedCables`。
2. **如实写出没修的缺口**：`cardColors[]` 里 `BUFFER`/`COMPILE_DRIVER` 被标 `PURPLE`、
   `BRILLIANCE`/`COLLECT` 被标 `BLUE`（不影响战斗，只影响变化牌池；属共享表，按「不顺手重构共享代码」
   单独说明不修）；铺垫牌估值、满血偏格挡两条属维护者已承认的搜索取舍（`docs/multi-character.md` §2.3），
   PR 里说明「不在本步范围」。
3. **`tools/coverage_manifest.py` 的改动要不要随 PR 走，先问维护者。** 现在它只对 `IRONCLAD` 查缺口，
   输出 `IRONCLAD has no gaps`；`class_relic_tests` 段是本步新加的（遗物要有 CTest 才算出覆盖）。
   两者都算共享工具改动，按「不顺手重构共享代码」得单独确认。
   **副作用要主动说明**：新判据一上线，`--check` 会多打一段 `NOTE: implemented but untested:`，列出
   战士的 7 个遗物（`BRIMSTONE`、`CHAMPION_BELT`、`CHARONS_ASHES`、`MARK_OF_PAIN`、`PAPER_PHROG`、
   `RED_SKULL`、`SELF_FORMING_CLAY`）——**这些是上游原有的缺口，不是我们弄坏的**，而且只是 NOTE、
   不影响 `PASS`。PR 里要写清楚，免得被当成回归。

### 交叉验证项

1. **CI 是 3 系统 × 2 Python 版本**（`.github/workflows/native-runtime.yml`：`ubuntu-24.04` / `macos-14` /
   `windows-2022` × 3.11 / 3.14）。本机只验证过 Windows；`overlay/build_native.py` 里 `/O2 /utf-8 /EHsc
   /bigobj`、`-A x64` 是 Windows 专用分支，Linux/macOS 分支没跑过。推 PR 前最好在别的系统上过一遍，
   或者先推 draft 看 CI 报什么。
2. **推 PR 前本地跑全套**（CONTRIBUTING「CI 要求」列的五行，`truth_calibration` 那行需要自己的适配器）。
   适配器我们没有（`tools/truth_calibration/headless_adapter.py` 要 `--cli` 指向一份带存档的 CLI，这里没有），
   但**机器人这条线有一条不需要游戏也不需要适配器的替代路**：
   `.venv/Scripts/python.exe tools/check_defect_truth.py`。它拿 `fixtures/calibration/DEFECT/` 里维护者的 6 个
   真值用例回放，实测 `cases 6, plays 623: costs 620, channels 58, block 297, damage 75` / `PASS`。
   PR 里就把这条当作真值校准的证据，并说明为什么 `truth_calibration/run.py` 跑不了。

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

   `cmake`/`ctest` 都不在 PATH 上（`shutil.which('cmake')` 返回 None），只在
   `.venv/Lib/site-packages/cmake/data/bin/` 里；`cmake --build` 还要先 `vcvars64.bat` 才有编译器。
   所以最省事的是照抄现成的 `build/_build_engine.bat` 和 `build/_ctest.bat`（这两个在 `.gitignore`
   里，不进 git，只在本机）。`build/_rebuild.bat` 用 `python -m cmake` 走另一条路，也行。

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

## 怎么在游戏里验证（真机测试的完整步骤）

机器人线**唯一还没做的一步**就是这里。流程只在 `docs/notes/2026-10-18.md:220` 记过一次，抄过来：

1. **确认后端能起**：`.venv/Scripts/python.exe tools/build_solver_runtime.py` 跑完三项 PASS。
   工坊那份是 `runtime=bundled` 且用 cp314 pyd，**不能直接换它的 runtime**；我们走 `runtime=native`，
   由 jar 的 `solver.properties` 直接指向仓库 `.venv` + `overlay/backend.py`，所以**只换 jar 就够**。
2. **打测试 jar**：`.venv/Scripts/python.exe tools/make_test_backend.py` 先生成
   `overlay/backend_defect_test.py`（把 `SUPPORTED_CLASSES` 从只有战士扩成战士+机器人），再
   `.venv/Scripts/python.exe overlay/build.py --game E:\SteamLibrary\steamapps\common\SlayTheSpire --defect-test`。
   产物在 `overlay/build/STS1CombatSolver.jar`。
3. **装**：把工坊的 `STS1CombatSolver.jar` 改名成 `.disable`（在
   `E:\SteamLibrary\steamapps\workshop\content\646570\3814773843\`），把新 jar 拷进
   `E:\SteamLibrary\steamapps\common\SlayTheSpire\mods\`。`mods\` 里现在只有一个
   `STS1CombatSolver-defect-1021.jar.disable`（已禁用），**启用前先确认没有两份同时生效**。
4. **测什么**（这次专门要盯的五个修复）：Bullseye（伤害 8/11 + Lock-On 2/3）、Reboot（洗牌后抽 4/6、
   手牌随机回填）、Cables（回合结束第二个被动延后）、X 费（Tempest/Multi-Cast/Recycle 扣能量与
   Confusion 变 0 费）、Inserter（第 2 回合才 +1 球位，不是第 1 回合）。
5. **报错看哪**：`C:\Users\yang\AppData\Local\STS1CombatSolver\backend.log`（全文，含
   `state_divergence` 的 diff）。行为记录会落在桌面 `sts1-dev-defect\sts1-test-<seed>.jsonl`。
6. **还原**：工坊 jar 改回 `.jar`、删掉 `mods\` 里那份，两步反向。

`overlay/build.py` 会自己跑二十多个 Java 自检（`LanguageCheck`、`PanelSizeCheck`、`ModeCheck`、
`Distill2Check`、`OutsidePacketParityCheck` 等），所以它能通过就说明 Java 层没坏。

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
