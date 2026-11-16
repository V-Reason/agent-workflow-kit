# DECISION_LOG — 重要架构决策记录（ADR）

> 每个决策一条记录；决策推翻时新增条目并标记旧条目 SUPERSEDED，不删除历史。

## ADR-0001 记录架构决策（Record Architecture Decisions）

- **状态**：ACCEPTED（2026-11-15）
- **背景**：AI 双 Agent 协作中，架构决策若只存在于对话里，后续任务无法追溯依据。
- **决定**：所有影响公共接口、依赖、分层、序列化或渲染管线的决策必须登记本文件。
- **后果**：Planner 引用决策时必须给出 ADR 编号；推翻决策需新增条目而非改写历史。

## ADR-0002 asmdef 物理分层 + 空层骨架

- **状态**：ACCEPTED（2026-11-15）
- **背景**：无程序集边界的 Scripts 目录在规模增长后依赖失控；先填肉后立约定会导致结构性返工。
- **决定**：Core/Gameplay/UI/Editor 四程序集单向依赖；空层先立 asmdef 与 README 约定；
  新增程序集必须先登记本文件。
- **备选与理由**：单 Assembly-CSharp（小项目可行，但失去编译隔离与依赖检查，弃）。
- **后果**：跨层引用必须改 asmdef references 并触发重审；依赖方向由编译器强制。

## ADR-0003 独立时间通道（GameClock）

- **状态**：ACCEPTED（2026-11-15）
- **背景**：顿帧（Hit-stop）若改全局 Time.timeScale 会连带暂停 UI、音频与补间。
- **决定**：所有游戏节奏读 `GameClock.ScaledDeltaTime`；全局暂停才用 Time.timeScale；
  两层语义分离；测试通过 `Tick(unscaledDeltaTime)` 直接驱动保证确定性。
- **备选与理由**：timeScale 篡改（牵连面大，弃）；每系统自建计时（重复实现，弃）。
- **后果**：新表现系统接入时必须使用 Clock；遗忘接入的检测列入代码审查项。

## ADR-0004 <决策标题>

- **状态**：PROPOSED / ACCEPTED / SUPERSEDED（<日期>）
- **背景**：<为什么需要决策>
- **决定**：<选定的方案>
- **备选与理由**：<方案 B 为何不选>
- **后果**：<对其他模块、依赖、规范的影响>

---
最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
