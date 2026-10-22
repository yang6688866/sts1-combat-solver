# 给上游回赠时的文件清单

这份文件**不是**给上游看的，是给自己回赠前核对用的。

背景：`defect/m3a-orb-skeleton` 相对 `upstream/main` 有 **96 个文件、23608 行**增量。其中 `tools/diagnostics/` 一个目录就占了 **34 个文件、11200 行**（将近一半），而这部分是本地排查工具，不该回赠。

上游的 `CONTRIBUTING.md` 要求 **一个 PR 一个功能**，所以不可能整分支一次推过去。

按下面的分组拆，每组独立成一个 PR，或者干脆只推第一组。

---

## 第一组：引擎行为修复（该进，核心价值）

这些是这次开发的实际成果，每个都有反编译依据和单元测试。

### 提交 `f91059f` 覆盖的部分

| 文件 | 改了什么 |
| --- | --- |
| `.../src/combat/characters/DefectCards.cpp` | Reboot 双重随机、Tempest/MultiCast 去重复扣费、Recycle 的 X 费分支 |
| `.../src/combat/BattleContext.cpp` | X 费哨兵（`costForTurn = -2`）的清零、`Actions::EmptyEnergy` |
| `.../src/combat/CardInstance.cpp` | `recycleEnergy` 与费用回收 |
| `.../src/combat/CardManager.cpp` | 洗牌/洗回时 X 卡重置哨兵 |
| `.../include/combat/CardInstance.h` | 新字段与方法声明 |
| `.../src/combat/Actions.cpp`、`include/combat/Actions.h` | `ShuffleAll`、`PutOnDeck`、`EmptyEnergy` |
| `.../src/combat/Player.cpp` | Cables 第二次被动延后入队 |
| `.../src/combat/Monster.cpp`、`include/combat/Monster.h` | 导入与伤害类型缺口（`1914ef2`） |

### 配套的绑定与语言层

| 文件 | 说明 |
| --- | --- |
| `.../bindings/slaythespire.cpp` | 新方法的 pybind 导出 |
| `candidates/sts-ironclad-agent/steam/steam_mcts.py` | 快照导入（focus/orbs/relics） |
| `candidates/sts-ironclad-agent/steam/native/live_combat_search.cpp` | 原生搜索入口 |
| `candidates/sts-ironclad-agent/sim_patch/parity/adapter.py` | 比较器的字段对齐 |
| `candidates/sts-ironclad-agent/sim_patch/alignment/tests/compare_powers.py` | 能力比较 |

### 测试（必带）

```
candidates/sts-ironclad-agent/combat_engine/tests/
  defect_cards_test.cpp          A   Defect 基础卡行为
  defect_relics_test.cpp         A   Cables / EmotionChip
  defect_card_select_test.cpp    A   选牌
  defect_potions_test.cpp        A   药水
  orb_damage_type_test.cpp       A   宝珠伤害类型
  orb_skeleton_test.cpp          A   宝珠骨架
  character_dispatch_test.cpp    M   职业分派
candidates/sts-ironclad-agent/combat_engine/CMakeLists.txt   M   注册新测试
```

### Java 层

| 文件 | 说明 |
| --- | --- |
| `overlay/src/sts1solver/SolverMod.java` | 职业门控加入 DEFECT（`SUPPORTED` 枚举） |
| `overlay/src/sts1solver/TestRecorder.java` | 记录器加 Defect 字段 |
| `overlay/src/sts1solver/RunExports.java` | F6 导出加 Defect 数据 |
| `overlay/coverage_manifest.json` | 覆盖清单更新 |

---

## 第二组：职业门控与测试后端（该进，但要看上游接不接）

| 文件 | 说明 |
| --- | --- |
| `overlay/backend_defect_test.py` | Defect 专用后端副本 |
| `overlay/test/recorded/DEFECT/*.json`（3 个） | 三个真机回放夹具 |
| `overlay/test/recorded/README.md` | 夹具说明 |
| `overlay/test/BackendRuntimeCheck.java` | 测试入口 |
| `overlay/build.py`、`build.ps1`、`build_native.py` | `--defect-test` 构建开关、javac 警告不再中断构建 |
| `tools/make_test_backend.py` | 生成测试后端 |
| `tools/check_defect_parity.py`、`check_defect_truth.py` | Defect 一致性/真值检查 |
| `tools/check_snapshot_import.py` | 修改 |

**注意**：`backend_defect_test.py` 是"另一职业还没做完时"的临时方案。上游如果自己实现了职业开关（`docs/multi-character.md` 里说"职业开关归维护者"），这一组可能被拒或要求改造。**先问再发**。

---

## 第三组：不该进 PR 的（留在本地）

### 3.1 一次性诊断脚本（20 个，约 1250 行）

`tools/diagnostics/cases/` 下的全部 `_*.py`：

```
_barrage.py  _barrage_damage.py  _barrage_engine.py  _barrage_value.py  _barrage_vs.py
_cables_only.py  _cables_probe2.py  _cables_repro.py  _cmp_jars.py
_f39_drop.py  _f39_full.py  _f39_turn1end.py
_floor39_probe.py  _floor39_relics.py  _floor39_rolls.py  _floor39_trace.py
_probe_run.py  repro_floor39.py  repro_floor39_real.py  repro_reboot.py
```

理由：每个都是一次性复现脚本，硬编码了具体局面的参数。上游没有对应的日志文件，跑不起来。留在本地分支自己用。

**例外**：如果第一组或第二组里有 bug 需要"这个 bug 怎么复现"的证据，把对应的那一个脚本一起带上。

### 3.2 游戏数据表（8 个文件，464KB）

```
tools/diagnostics/data/sts_cards.{json,csv}   sts_potions.{json,csv}
                        sts_powers.{json,csv}   sts_relics.{json,csv}
```

理由：来源是中文 wiki 导出（`sts.huijiwiki.com`），不是从游戏内提取，版权上比反编译安全但**没必要**。上游 `CONTRIBUTING.md` 的规矩是"以原版 Java 为准"，带一个二手数据表反而容易误导（F55 Recycle bug 就是被它误导的）。

### 3.3 迁移期笔记（5 个）

```
docs/notes/MEMORY.md  docs/notes/README.md
docs/notes/2026-10-16.md  2026-10-18.md  2026-10-19.md
```

理由：这是从 WorkBuddy 迁过来时记的项目笔记，含大量"我和 AI 怎么协作"的内容，对上游没意义。

### 3.4 本地环境文档（1 个）

```
docs/local-environment.md
```

理由：写的是**这台机器**的路径（`E:\sts-devkit\`）、本地构建坑。对其他协作者不适用。

`AGENTS.md` 里指向它的那一行也要一起去掉（diff 里第一条 `+` 行）。

### 3.5 这一条建议保留

`AGENTS.md` 第二条 `+` 行：

> Card behaviour comes from the game's bytecode, never from exported tables like `sts_cards.json` … Decompile with `E:\sts-devkit\decompiled\decompile.sh`

前半句（**别信导出表**）是这几轮踩坑换来的通用教训，上游也该知道。但后半句写了我的本地路径，回赠时要改成中性说法，比如"decompile the relevant class from the game jar"。

---

## 第四组：本地分支自己的（不算回赠，但要留）

| 文件 | 说明 |
| --- | --- |
| `fixtures/bug-reports/` 下 5 个夹具 | 真机证据，体积 2.2MB。上游可能不收这么大的二进制 JSON |
| `docs/known-gaps.md` | 本地待办 |
| `.gitignore` 的 `references/game-src/` 等 | 上游可能已有自己的写法 |

---

## 回赠操作步骤

```bash
# 1. 从 upstream/main 开一个干净分支
git fetch upstream
git checkout -b defect/engine-fixes upstream/main

# 2. 只挑第一组（引擎 + 测试 + Java 门控）
git checkout defect/m3a-orb-skeleton -- \
  candidates/sts-ironclad-agent/combat_engine/ \
  candidates/sts-ironclad-agent/steam/ \
  candidates/sts-ironclad-agent/sim_patch/ \
  overlay/src/ \
  overlay/coverage_manifest.json
#   （overlay/src 里含 SolverMod.java，这是改动最大的单个文件，要单独 review）

# 3. 确认没有夹带
git status --short
git diff --stat upstream/main

# 4. 跑全套检查，写进 PR 说明
cmake --build candidates/sts-ironclad-agent/build/engine
ctest --test-dir candidates/sts-ironclad-agent/build/engine -C Release
.venv/Scripts/python.exe tools/check_solver_runtime.py
```

PR 说明里要写清：跑了哪些检查、哪些通过、在游戏里验证了什么（`CONTRIBUTING.md` 的要求）。

---

## 判断某文件该不该进，一句话

> **上游拿到这个文件，能在自己的机器上跑起来吗？**

跑不起来的（依赖我的日志路径、我的反编译目录、我的 devkit），就不进。
