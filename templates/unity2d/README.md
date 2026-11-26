# unity2d — Unity 2D v4.0 模板

面向 CEO + Secretary / Planner / Worker / Watchdog 工作流的 Unity 2D 骨架：asmdef 分层、组合根、独立时间通道、Editor 结构审计、物理投喂箱与 v4.0 任务凭证。

## 通过 v4.0 装配器使用

1. 用 Unity 2022.3 LTS 或 Unity 6 新建 2D 工程。
2. 运行：

```bash
python scripts/workflow.py attach <unity-project> \
  --layers core,generic,unity2d,unity2d-starter --yes
```

3. Unity 打开并等待程序集编译，Console 期望 0 error。
4. Unity GUI/Test Runner 由已授权执行人运行；`Tools > Agent Workflow > Workflow Audit` 应无 FAIL。
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
| `AI_Context/TASKS/_templates/` | v4.0 任务凭证 |
| `Assets/AgentWorkflow/Editor/` | 装配器安装的独立工作流静态审计 |

## 静态审计

现有项目适配使用 `core,generic,unity2d`，不会注入本目录的示例 gameplay 代码。Unity Editor、Test Runner 与最终视觉验证仍由 CEO 或专项授权执行人运行。

## 关键设计

- `GameClock` 独立时间通道，不篡改全局 `Time.timeScale`。
- 服务装配只在 `GameBootstrap`。
- Gameplay → Core；UI → Gameplay → Core；EditorTools → Core。
- Agent 不写 Prefab、场景、Asset、meta 或电子表格。

## Git

`AI_Context/TASKS/**/FEED_DROP/` 与 `AI_Context/TASKS/**/NEED_FILES/` 已在 `.gitignore`。
Git 初始化、提交和远端配置由 CEO 明确控制。
