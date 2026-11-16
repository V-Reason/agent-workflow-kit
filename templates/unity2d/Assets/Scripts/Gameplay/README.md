# Gameplay 层（GAMEDEV.Gameplay）

玩法逻辑层：角色控制、战斗、关卡规则、状态机。

## 铁律

1. 仅依赖 `GAMEDEV.Core`（asmdef 已锁定）；禁止反向依赖 UI，禁止引用 Editor 程序集。
2. 表现节奏读 `GameBootstrap.Instance.Clock.ScaledDeltaTime`，不读 `Time.deltaTime`（顿帧/慢动作统一走独立时间通道）。
3. 物理移动在 `FixedUpdate`；刚体开 `interpolation = Interpolate`；高频射线/碰撞用 NonAlloc 预分配 API。
4. Hot-Path（Update/FixedUpdate）0 GC：禁 `GetComponent`、闭包、LINQ、字符串拼接。
5. 高频生成物（弹幕、跳字、特效）强制对象池，池设 `maxSize` 与溢出策略。
6. 注释预算净零；新文件类名 = 文件名（PascalCase）。

本目录当前为空骨架（仅 asmdef 与本说明）；新增代码前先在 `AI_Context/MODULE_MAP.md` 登记行。
