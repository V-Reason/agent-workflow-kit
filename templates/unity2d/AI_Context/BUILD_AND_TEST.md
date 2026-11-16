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
| V1 | Unity 编译后的 Console + 结构审计 | 0 error，审计 FAIL = 0 |
| V2 | Assembly 编译 | 0 error |
| V3 | Window > General > Test Runner > EditMode > Run All | 全绿 |
| V4 | 编辑器/运行时场景验证 | 观察点与截图/录屏证据 |
| V5 | Profiler / Memory / DrawCall | 符合任务预算 |

## 无头结构审计

```text
<UnityEditorPath> -batchmode -nographics -projectPath <ProjectRoot> -executeMethod GAMEDEV.EditorTools.ProjectAuditWindow.RunBatchAudit -logFile audit.log
```

- 不要追加 `-quit`；`RunBatchAudit()` 通过 `EditorApplication.Exit` 返回真实退出码。
- FAIL > 0 时退出码为 1，否则为 0。
- 审计检查分层目录、asmdef、`AI_Context/PROJECT_BOARD.md`、`scripts/stage_context.py`、`scripts/validate_handover.py` 和脚本 `.meta`。
- 运行前关闭同工程编辑器实例。

## 上下文与交接

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN --files Assets/Scripts/Core/GameClock.cs
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for archive
```

## 证据

Console、Test Runner、审计日志、截图与 Profiler 数据存入 `AI_Context/EVIDENCE/GD-YYYY-NNNN/`。验收表必须记录命令、版本、退出码或观察点。

---

最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
