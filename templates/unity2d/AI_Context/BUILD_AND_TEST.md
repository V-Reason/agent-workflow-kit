# BUILD_AND_TEST — Unity 2D 验证方法（L1）

> 任务书第 10 章只能引用这里登记的验证入口。实际未运行必须记 `NOT RUN`，环境缺失必须记 `BLOCKED` 或 `NOT RUN`。

## 环境

- Unity 2022.3 LTS 或 Unity 6000.x，版本必须与 `PROJECT_OVERVIEW.md` 一致。
- 首次打开 Unity 会生成 `.meta` 和缓存；资产与 meta 必须成对保留。
- `ProjectSettings/`、`Packages/manifest.json`、渲染管线与 asmdef references 变更需重新审批。

## 日常门禁

| 层 | 操作 | 期望 |
| --- | --- | --- |
| V0 | 审阅 PLAN、接口、生命周期与 Non-goals | 无未决阻塞 |
| V1 | `python scripts/workflow.py doctor .` + Unity Workflow Audit | 离线通过；Unity FAIL = 0 |
| V2 | Assembly 编译 | 0 error |
| V3 | Window > General > Test Runner > EditMode > Run All | 全绿；标 `UNITY_GUI_REQUIRED` |
| V4 | 编辑器/运行时场景验证 | 观察点；截图/录屏仅在无法文本断言时使用 |
| V5 | Profiler / Memory / DrawCall | 符合任务预算 |

## 工作流审计

```bash
python scripts/workflow.py doctor .
```

再在 Unity 选择 `Tools > Agent Workflow > Workflow Audit`，Console 期望 `FAIL=0`。该菜单属于 `UNITY_GUI_REQUIRED`，默认由 CEO 执行。除非项目另有已登记且真跑通过的 headless 入口，不得把菜单审计描述成 CLI 证据。

## 上下文与交接

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN --files Assets/Scripts/Core/GameClock.cs
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN \
  --append --reason "<chat planner 未解决的具体未知项>" \
  --files Assets/Scripts/Core/Extra.cs
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for archive
```

## 证据

Console、Test Runner、审计日志、退出码、Diff、Profiler 数据与必要截图存入
`AI_Context/EVIDENCE/GD-YYYY-NNNN/`。机器可验项以命令、退出码和日志为主证据；
视觉项必须记录 Visual Purpose、Visual Scenario 与 Visual Expected，截图数量最小化。
Unity Editor/游戏启动/Inspector 默认由 CEO 执行，Worker 仅在 Computer-Use 专项授权下操作。

---

最后核验日期：2026-11-26｜分支：main｜维护人：<项目 Owner>
