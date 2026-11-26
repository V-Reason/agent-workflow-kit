# MODULE_MAP — 程序集、目录与职责索引（L2 模块级引用项）

> 每个任务验收后核对漂移；漂移项标 STALE 并回写修正。

| 路径 | 程序集 | 职责 | 公共接口 |
| --- | --- | --- | --- |
| `Assets/Scripts/Core/GameBootstrap.cs` | GAMEDEV.Core | 组合根引导：唯一装配入口、防重复引导 | `Instance`、`Clock` |
| `Assets/Scripts/Core/GameClock.cs` | GAMEDEV.Core | 独立时间通道：顿帧/慢动作不改全局 timeScale | `ScaledDeltaTime`、`Freeze`、`SetChannelScale`、`Tick` |
| `Assets/Scripts/Gameplay/` | GAMEDEV.Gameplay | 玩法逻辑（空骨架） | 待登记 |
| `Assets/Scripts/UI/` | GAMEDEV.UI | 表现与界面（空骨架） | 待登记 |
| `Assets/AgentWorkflow/Editor/WorkflowAuditWindow.cs` | AgentWorkflow.Editor | v4.0 装配文件、技能和 Unity 标记审计 | 菜单 Tools > Agent Workflow > Workflow Audit |
| `Assets/Scripts/Editor/Tools/BootstrapSceneMenu.cs` | GAMEDEV.EditorTools | 场景装配菜单：插入/移除 GameBootstrap | 菜单 GAMEDEV > 搭建 |
| `Assets/Tests/Editor/GameClockTests.cs` | GAMEDEV.Tests.Editor | GameClock EditMode 测试（6 用例） | Test Runner |
| `scripts/workflow.py` | — | 项目装配、status、doctor 与 sync | CLI |
| `scripts/validate_handover.py` | — | v4.0 交接包校验器 | CLI |

## 漂移记录

| 日期 | 漂移内容 | 处理 |
| --- | --- | --- |
| <日期> | <漂移描述> | <已修正/待修正> |

---
最后核验日期：2026-11-26｜分支：main｜维护人：<项目 Owner>
