# AGENTS.md — <项目名> 项目级 Agent 规范（Unity 2D）

> 本文件只写 Unity 项目特有约束；通用规则以 `AGENTS.md` 的 v4.0 托管块、`AI_Context/WORKFLOW_LOCK.toml` 与 `.agents/skills/` 为准。

## 0. 授权门

- 写入必须有 CEO 批准的 PLAN 版本与 `APPROVAL_RECORD.md`。
- 写入必须落在批准 Write Boundaries；Forbidden、边界外、未批准删除/重命名立即停止。
- Worker 可非敏感全仓只读检索，并在 Preflight 自动列出 Discovered Inputs 与 Planned Writes。
- 未批准时只允许读仓、Preflight 和只读取材。
- L0 可由 CEO 用紧凑 mini 简报直派 Worker，仍须 Profile 身份、Diff 和 ACCEPTANCE；碰资产、asmdef 或配置即升级。

## 1. 资产红线

1. Agent 永不直接写 `.prefab / .unity / .asset / .unitypackage / .xlsx`；此类操作交给 CEO 手工清单。
2. `.meta` 必须与资产同进同出；GUID 断裂、资产两端存在性不明时停止。
3. `ProjectSettings/`、`Packages/manifest.json`、渲染管线、asmdef references 默认禁止，需专项批准。
4. 不删除看似无用的资产、元文件或目录。
5. 手工清单每条必须含路径、操作、期望值与判据。
6. Unity Editor、游戏启动、Inspector 和最终视觉观察默认由 CEO 执行；Worker 只有获得 Computer-Use 专项授权时才可使用原生 UI。

## 2. 正式入口

- 项目看板：`AI_Context/PROJECT_BOARD.md`
- 上下文：`00_CONTEXT_MANIFEST.md` + `FEED_DROP/`
- 项目装配与自检：`scripts/workflow.py`
- 施工员：`worker-engine`
- 独立监察：`watchdog-inspector`

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 --files Assets/Scripts/Core/GameClock.cs
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --append --reason "<未解决未知项>" --files Assets/Scripts/Core/Extra.cs
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
```

## 3. 门禁

| 门禁 | 命令 / 操作 | 期望 |
| --- | --- | --- |
| 程序集编译 | Unity 打开工程（默认 CEO） | Console 0 error |
| EditMode | Test Runner > EditMode > Run All | `UNITY_GUI_REQUIRED`，由 CEO 或专项授权 Worker 执行 |
| 工作流审计 | `python scripts/workflow.py doctor .` + Unity `Tools > Agent Workflow > Workflow Audit` | 离线 doctor 通过；Unity 菜单 FAIL = 0 |
| 交接包 | `validate_handover.py --for watchdog` | exit 0 |

Unity Editor 菜单审计属于 GUI 门禁；没有登记的 headless 入口时不得臆造批处理命令。

## 4. 分层红线

1. `GAMEDEV.EditorTools` 仅依赖 `GAMEDEV.Core`，Editor 平台限定。
2. Runtime 与 Editor 代码物理隔离。
3. 测试只放 `GAMEDEV.Tests.Editor` 或批准的测试程序集。
4. Gameplay → Core；UI → Gameplay → Core；禁止循环。
5. 新增 asmdef 或改 references 必须先登记 DECISION_LOG 并重新审批。

## 5. 工程纪律

- 不虚构 Unity API；先核当前引擎版本。
- 物理使用 FixedUpdate；高频检测避免无界分配。
- 顿帧/慢动作走 `GameClock` 独立时间通道，不篡改全局 `Time.timeScale`。
- Hot Path 0 GC 目标必须用 Profiler 证据，不用口头顶替。
- 编译通过不代表行为正确；生命周期、序列化、资产引用和运行时必须分别验证。

## 6. 技能装载

| 阶段 | 加载 |
| --- | --- |
| 运营、登记、备菜、回写 | `secretary-router`（Agent） |
| 规划与任务书 | `planner-orchestrator` + `task-brief-writer`；按需只读叠加 `unity2d-architect` / `game-systems-designer` |
| 施工 | `worker-engine` 单装；不加载顾问 |
| L1/L2 验证 | `watchdog-inspector` 独立会话/实例 |
| 软故障复盘 | `watchdog-inspector`，只出提案 |

## 7. 归档

- 证据：`AI_Context/EVIDENCE/GD-YYYY-NNNN/`；优先审计日志、退出码、测试结果、Diff 和 Profiler 数据
- CEO 验收：`ACCEPTANCE.md`
- 验收后 24 小时内由 Secretary 依据 diff 起草上下文回写提案，CEO 审阅合入。
