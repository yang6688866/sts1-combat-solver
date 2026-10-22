# 已知缺口与未完成事项

这份清单记的是**"我们知道但还没做"**的事。写在这里的东西都有具体出处或复现方式，不是愿望清单。

每条的格式：**现象** → **为什么还没做** → **怎么验证修好了**。

上游维护者不需要看这份文件；它是给这个仓库的长期维护者（和以后接手的人）看的。

---

## 一、求解器质量（不是缺陷，是设计上的取舍）

### 1.1 铺垫牌（Focus／姿态／宝珠）在未结束节点不计价值

**现象。** 搜索的估值函数在没打到赢的节点上只看怪物血量比例：

```cpp
if (PLAYER_VICTORY) return 100 * (35 + bc.player.curHp + potionScore - bc.turn * 0.01);
```

Focus、姿态、宝珠层数都不进这个式子。结果是"铺垫牌"（Defragment、Biased Cognition、碎片整理）在搜索视野内不改变胜负时，贡献恰好为 0，随后 `overlay/plan_reduction.py` 的 `_same_victory` 判据会把它当成零价值动作删掉。

**表现。** Lagavulin 111 血的长战里，求解器第一手就打碎片整理；floor 10 打酸液（55 血）的短战里，则留着 1 点能量结束回合。同一张牌，两种行为，都"正确"。

**为什么还没做。** 维护者文档 `docs/multi-character.md` §2.3 已经明确写了这是已知取舍：「未结束的节点只看怪物血量比例，所以姿态、宝珠、Focus 等铺垫价值不会被计入，**影响搜索质量，不影响正确性**」。要改就得动搜索估值，属于大改。

**怎么验证。** 改造后重跑 `tools/diagnostics/_card_usage.py`，看 `Defragment`（未升级，当前 3/39 = 0.08）这类牌的 `rate` 是否升上来，同时确认胜率不下降。注意 `Defragment+` 是 41/77 = 0.53，说明"升级后打得出来、没升级的打不出来"，这本身就是铺垫价值被低估的旁证。

### 1.2 满血时偏向格挡和抽牌

**现象。** 玩家满血时，格挡的边际价值应该接近 0（反正不掉血），但求解器仍然会把 1 点能量花在 Defend 上，而不是同一张手上的攻击牌。这跟 1.1 同源：赢不赢只看怪物血量，不看"我现在血满不满、能不能安全多打一张"。

**为什么还没做。** 同上，属于估值函数的结构问题。

**怎么验证。** `_card_usage.py` 里 Defend 类牌的 `rate` 明显低于攻击牌（当前 Defend_B+ 29/370 = 0.08 vs Strike_B 93/264 = 0.35），修好后应该拉近。

---

## 二、测试覆盖的缺口

### 2.1 fixtures/bug-reports/ 只有两个旧夹具

**现象。** 目录里只有 v0.7.0 时期的两个夹具（10-17 / 10-18）。这之后修的几个真机 bug **都只有单元测试，没有真机夹具**：

| bug | 修复提交 | 现有覆盖 |
| --- | --- | --- |
| Reboot 洗牌堆方向 | `f91059f` | 单元测试 `defect_cards_test.cpp` |
| Cables 第二次被动延后入队 | `f91059f` | 单元测试 `defect_relics_test.cpp` |
| floor 39 分歧（Cables 同源） | 同上 | 同上 |
| X 费（Tempest/Recycle/MultiCast） | `f91059f` | 单元测试 `defect_cards_test.cpp` |
| 导入与伤害类型缺口 | `1914ef2` | 见该提交说明 |

单元测试够用，但**真机夹具能防住"单元测试写错了假设"这种情况**——Reboot 的第一次修复就是这么翻车的：测试断言了"手牌按顺序进抽牌堆"，而游戏实际是随机的，测试全绿但行为是错的。

**为什么还没做。** 真机夹具需要 F6 导出文件，目前都在 `E:\sts-devkit\test-logs\`，还没挑进仓库。

**怎么验证。** 每个夹具配一个 `tools/diagnostics/` 里的重放脚本，`ctest` 之外手动跑一遍能复现原始 diff。

### 2.2 没有覆盖清单工具

**现象。** 哪些牌实现了、哪些没实现、哪些职业的遗物钩子有遗漏，只能靠读代码数。`docs/multi-character.md:136` 列了这个需求。

**为什么还没做。** 优先级低于修 bug。

---

## 三、构建与发布

### 3.1 手工重链后必须重算 manifest

**现象。** `live-manifest.json` 记录 pyd 的哈希，游戏启动时校验，不一致就抛 `ValueError: frozen live engine changed`。只跑 `cmake --build` 不跑 `tools/build_solver_runtime.py` 的话，哈希对不上。

**为什么还没做。** 这条不是要修，是**要记住**。已经写进 `docs/local-environment.md` 和 `AGENTS.md`。

**怎么验证。** 改完跑 `.venv/Scripts/python.exe tools/check_solver_runtime.py`，三项全 PASS 才算完。

### 3.2 游戏运行时 pyd 被锁

**现象。** java.exe 持有 pyd，链接报 `LNK1104`。

**为什么还没做。** 无解，必须让玩家退游戏。已记进 `docs/local-environment.md`。

---

## 四、仓库卫生

### 4.1 分支比上游多 96 个文件、2.3 万行

**现象。** `defect/m3a-orb-skeleton` 相对 `upstream/main` 的增量里，有约 24 个一次性诊断脚本和 8 个游戏数据表（468KB，来源是中文 wiki 导出 `sts.huijiwiki.com`）。

按 `AGENTS.md` 的规矩（一个 PR 一个功能），真要给上游回赠时得先精简。**现在不用动**，但回赠前必须处理。

**怎么验证。** 回赠 PR 之前，`git diff --stat upstream/main -- <每个文件>` 逐个确认。

### 4.2 反编译的游戏源码不能进仓库

**现象。** `CONTRIBUTING.md` 明令 never commit game JARs, decompiled code, game assets or build output。

**为什么还没做。** 已处理：`references/game-src/` 已删除，`.gitignore` 加了 `references/game-src/` 和 `*.decompiled/`。反编译产物在仓库外 `E:\sts-devkit\decompiled\`。

**怎么验证。** `git log --all --diff-filter=A -- references/game-src` 应为空。

---

## 五、其他职业线

### 5.1 猎人线未跟进

`feat/m1a-silent-poison` 比 `main` 多 32 个提交，未推远端。小刀精准（Accuracy）刷新逻辑待做。

### 5.2 机器人线改动是否回赠上游

`defect/m3a-orb-skeleton` 已推 `origin`，但没对上游发 PR。回赠前先处理 4.1。
