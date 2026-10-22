# STS1 Combat Solver 项目长期笔记

## 项目本质
《杀戮尖塔 1》战斗求解器 Mod。四层架构：游戏 → Java 模组（overlay/src/sts1solver，24 文件）→ Python 后端（backend.py，JSON lines，可杀死子进程）→ C++ 搜索引擎 combat4r（candidates/sts-ironclad-agent，pybind11）。发布版 v0.4.2（Steam 工坊）。

## 版本进展
- 0.6.0（2026-10-16 用户更新）：四职业协作开发 M0 地基（PR #8）+ 真值校准体系。关键资产：
  - docs/product.md（四职业 spec）、docs/architecture.md、docs/multi-character.md（缺口盘点+里程碑+分工）、docs/truth-calibration.md（校准协议）
  - CONTRIBUTING.md（协作者 9 条代码要求：以原版 Java 为准、仓库禁游戏代码、没实现就保持未实现、每个实现要有夹具、不放宽比较、职业开关归维护者）
  - fixtures/calibration/：24 个校准用例（四职业 × A0/A20 × 3，5894 动作 4890 检查点）
  - tools/truth_calibration/：run.py + headless_adapter.py（stdin/stdout JSON 行协议 new/act/quit）
  - overlay/coverage_manifest.json（覆盖清单，CI 查过期）；快照新增可选字段 character/stance/mantra/orbs/retain
  - RngMods.java：扫描其他 mod 是否碰游戏 Random 防 RNG 失步
- 里程碑：M0 done → M1 静默猎手（M1a 起始牌 Survivor/Neutralize 起步）→ M2 观者 / M3 机器人（宝珠子系统最大）

## 协作方法论：三次误判换来的硬规矩（2026-10-19 用户复盘确认）
作者的战士实现**写过的部分基本是对的**；出问题的是"战士用不到所以没写到的盲区"。因此：
1. **不许先怀疑作者**。判定"作者 bug"前必须读完**整条调用链**（不能只 grep 函数名的显式调用）。反例：`Player::buff` 里没搜到 `updatePowerOrder` 就断言"登记不上"——实际 buff 调的 `setHasStatus` 第 313 行自己会登记；四个标量字段（STRENGTH/DEXTERITY/FOCUS/ARTIFACT）则由 buff 自己显式登记（`setHasStatus` 对它们提前 return）。两条路都通，我加的第三行是冗余
2. **规格书只有字节码，攻略/wiki 只是线索**。反例：凭印象认为毒雾回合末结算 → 反汇编 `NoxiousFumesPower` 只有 `atStartOfTurnPostDraw()`，作者放的位置分毫不差
3. **改共享判定必须配"行为测试"**（数伤害/数次数），只断言状态值等于没测。反例：回响形态被我改坏，2 层实测 24（正确 30）才暴露
4. 反编译 jar 搜常量要搜**类名/字段名**，不要搜显示名字符串（曾因搜 "Curl Up" 漏掉引用它的 LouseNormal/LouseDefensive，误判"原版没有蜷身"）

## 模拟器缺口（覆盖清单 2026-10-15 快照）
- 铁甲 72/72 全实现；静默 2/71（Wraith Form、Piercing Wail）；机器人 0/71；观者 1/71（Vault）
- 卡牌行为在 BattleContext.cpp 三个 switch（useAttackCard/useSkillCard/usePowerCard，行号 ~972/1226/1538）
- 玩家状态位掩码 96 位上限，已用 87，扩容是 M0 交付的一部分

## 用户在协作中的角色
QQ 群协作者（昵称"有事问春风"），维护者是"明"（Yongzhaooo，邮箱 yongzhao.derek@gmail.com）。用户负责给三职业实现战斗模拟，通过 PR 提交。
**用户决定（2026-10-16）：先做故障机器人（M3）模拟**，不走文档建议的静默先行路线。文档允许（M2/M3 顺序由协作者兴趣定）；机器人不依赖静默的基础件，独立性强，但规模最大（宝珠子系统）。关键前置：认领（issue/邮件）→ 本地编译原生引擎 → 用正版游戏搭真值并过 24 用例校准（零容差，绕不开，没校准最多做到单元测试层，PR 会被卡）。游戏版本锚点：desktop-1.0.jar sha256 cfad868a…081673，[V2.3.4] (12-18-2022)。

## 机器人模拟分支 defect/m3a-orb-skeleton（2026-10-18）
- 奖励牌 71/71 + 起始 4/4 + 职业遗物 9/9 全实现，分支 20 commits，CTest 12/12；四系宝珠 + 集中（可负）+ Loop/电动力学闭环
- 遗物两个坑：Gold-Plated Cables 的行为写在三个 orb 触发动作里（TriggerEndOfTurnOrbs / Impulse / DarkImpulse），都作用 `orbs.get(0)`（=evokeOrb 取的那颗=引擎 index0，卡面叫"最右侧"）；Emotion Chip = 任意掉血置 pulse，下回合开始 ImpulseAction
- 药水：Essence of Darkness 原本是空动作（药水无效果），已按字节码实现为 每栏 1 颗 Dark（圣树皮 2）；Focus=2/4、Capacity=2/4 已核对
- **Echo Form 判定**：作者原式 `cardsPlayedThisTurn - echoFormCardsDoubled <= amount` 是对的——引擎把复制出的队列项也计入 cardsPlayedThisTurn，必须减去复制数才能还原原版 `size() <= amount`。曾误改成 `<= amount`，2 层以上会只复制第一张（实测 24 vs 正确 30），已回退并加回归测试
- 其他共享改动：Player::attacked 内挂静电释放（只认攻击伤害，poison/自伤走 loseHp 不触发）；**格挡全挡住的攻击也不触发**（字节码：damage() 先 decrementBlock 再遍历 powers.onAttacked，而 StaticDischargePower.onAttacked 在参数 ≤0 时直接返回）；onAfterUseCard 内做卡牌自改写（精简改良/蒸汽护壁/遗传算法，等价原版 onMoveToDiscard）；cardOnExit 启用作者注释掉的 GENETIC_ALGORITHM 写回
- 费用表：Cards.h cardCost() 默认 1，机器人 0/2/3/4/5/X 费与升级降费必须显式列（0 费 12 张、2 费 5 张、3 费 3 张、力场 4、陨石 5、暴风雨 X）
- **快照链路**：CommunicationMod 已导出 `combat_state.player.orbs`（id/evoke_amount/passive_amount，空栏 id=null）；`steam_mcts.build_snapshot` 透传，`battleFromSnapshot` 反推（evoke−基础−focus=卡牌加成；Dark 的 evoke 就是累计伤害；Plasma→FUSION）
- **改 Player 结构体后必须同时重建 runtime/engine 三个 pyd 与 overlay/build/native/overlay_search.pyd**，否则跨模块传 BattleContext 报 "vector too long"；overlay 重建需 `-Dpybind11_DIR=<venv>/Lib/site-packages/pybind11/share/cmake/pybind11`，并手工更新 runtime/live-manifest.json 的 sha256

## 本机构建环境（2026-10-19 已验证配方）
- 游戏：`E:/SteamLibrary/steamapps/common/SlayTheSpire`；desktop-1.0.jar sha256 = cfad868a…（与校准锚点一致，可直接用于校准）
- MTS/BaseMod 工坊 jar 在 `E:/SteamLibrary/steamapps/workshop/content/646570/{1605060445,1605833019}/`，build.py 自动探测
- JDK 25（java/javac/jar 均有，javac --release 8）；仓库根 `.venv`（Python 3.13.14，pybind11 + cmake 4.4.4 + ninja）；MSVC 14.44.35207 + SDK 10.0.26100.0（VS2022 BuildTools）
- **Windows 构建必须绕开脚本里的 `-A x64`**：`tools/build_solver_runtime.py` 和 `overlay/build_native.py` 都硬编码 VS generator，且 PowerShell 工具禁 cmd.exe（不能 call vcvars64.bat）。可行路径：纯 PowerShell 手工设环境再 Ninja——
  `PATH += .venv/Scripts + MSVC/bin/Hostx64/x64 + WindowsKits/10/bin/10.0.26100.0/x64`（**SDK bin 必须加，缺 rc.exe/mt.exe 会报 "CXX compiler is broken"**）
  `INCLUDE = MSVC/include + SDK Include/{ucrt,um,shared,winrt}`；`LIB = MSVC/lib/x64 + SDK Lib/{ucrt,um}/x64`
  引擎：`cmake --build candidates/sts-ironclad-agent/build/engine -j 4`（已有 Ninja 缓存）；overlay：删 `overlay/build/native/cmake` 后 `cmake -S overlay/build/native -B ... -G Ninja -DCMAKE_BUILD_TYPE=Release -Dpybind11_DIR=...`
- 故障排查：工坊版=0.7.0（含 8000→128000 加深逻辑，238 请求卡死根因）；本地=0.8.0-beta.1（发布说明已修"搜索轨迹失控"），计划本地构建 0.8.0-beta.1 替代工坊版

## 分支状态（2026-10-19 重组后）
- `defect/m3a-orb-skeleton` = 纯机器人线（28 commits，HEAD 8ce8499，基线 v0.8.0-beta.1 合并点 b653576）：71/71 奖励牌 + 起始 4/4 + 职业遗物 9/9 + 宝珠系统 + 共享引擎修复（Echo Form 回退、静电释放、宝珠 THORNS、爆炸药水、搜索器选牌枚举）
- `feat/m1a-silent-poison` = 猎人线（2 commits：f6bcac0 毒系八张、a15cd17 千刀万剐，覆盖 10/71），等机器人上线后再继续
- `overlay/backend_defect_test.py` = 测试包专用副本（backend.py 的 CRLF 版 + SUPPORTED_CLASSES 加 DEFECT），不进 git；测试包做法：复制标准 jar，改 jar 内 solver.properties 的 `backend=` 指向它
- 用户指令（2026-10-19）：先不 PR，机器人真机测试通过后再让推 GitHub
