# unity2d — Unity 2D v3.1 模板

面向 CEO + Secretary / Planner / Worker / Watchdog 工作流的 Unity 2D 骨架：asmdef 分层、组合根、独立时间通道、Editor 结构审计、物理投喂箱与 v3.1 任务凭证。

## 实例化

1. 用 Unity 2022.3 LTS 或 Unity 6 新建 2D 工程。
2. 把本目录的 `Assets/`、`Packages/manifest.json`、`AI_Context/`、`scripts/`、`AGENTS.md`、`README.md`、`.gitignore`、`.gitattributes` 合并进新工程。
3. Unity 打开并等待程序集编译，Console 期望 0 error。
4. Unity GUI/Test Runner 由已授权执行人运行，结构审计 `RunBatchAudit` FAIL = 0。
5. 填写 `PROJECT_OVERVIEW.md`、`PROJECT_BOARD.md` 和 `MODULE_MAP.md`。

## 结构

| 路径 | 内容 |
| --- | --- |
| `Assets/Scripts/Core/` | `GAMEDEV.Core`：组合根与时间通道 |
| `Assets/Scripts/Gameplay/` | `GAMEDEV.Gameplay` |
| `Assets/Scripts/UI/` | `GAMEDEV.UI` |
| `Assets/Scripts/Editor/` | `GAMEDEV.EditorTools`，只依赖 Core |
| `Assets/Tests/Editor/` | EditMode 测试 |
| `AI_Context/PROJECT_BOARD.md` | Attention Queue + Ticket Index |
| `AI_Context/TASKS/_templates/` | v3.1 任务凭证 |
| `scripts/stage_context.py` | L1/L2/L3 真文件投喂 |
| `scripts/validate_handover.py` | v3.1 四模式、证据与 Diff 边界门禁 |

## 无头审计

`GAMEDEV.EditorTools.ProjectAuditWindow.RunBatchAudit` 会检查分层目录、程序集、看板、两个脚本、关键上下文和脚本 `.meta`，FAIL > 0 时返回 1。命令模板见 `AI_Context/BUILD_AND_TEST.md`；不要再追加 `-quit`。

## 关键设计

- `GameClock` 独立时间通道，不篡改全局 `Time.timeScale`。
- 服务装配只在 `GameBootstrap`。
- Gameplay → Core；UI → Gameplay → Core；EditorTools → Core。
- Agent 不写 Prefab、场景、Asset、meta 或电子表格。

## Git

`AI_Context/TASKS/**/FEED_DROP/` 与 `AI_Context/TASKS/**/NEED_FILES/` 已在 `.gitignore`。
Git 初始化、提交和远端配置由 CEO 明确控制。
