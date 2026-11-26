## Unity 2D 项目约束

- Agent 不直接写 `.prefab / .unity / .asset / .unitypackage / .xlsx`；此类操作交 CEO 手工清单。
- `.meta` 必须与对应资产同进同出；GUID 不明确时停止。
- `ProjectSettings/`、`Packages/manifest.json`、渲染管线与 asmdef references 属于 Protected Changes。
- Unity Editor、游戏启动、Inspector 与 Test Runner 默认由 CEO 执行；Worker 仅凭专项 Computer-Use 授权操作。
- 静态审计入口：Unity 菜单 `Tools > Agent Workflow > Workflow Audit`。
