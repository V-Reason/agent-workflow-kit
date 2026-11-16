# UI 层（GAMEDEV.UI）

表现与界面层：HUD、菜单、飘字、红点。

## 铁律

1. 依赖 `GAMEDEV.Core` + `GAMEDEV.Gameplay`（asmdef 已锁定）；Gameplay 禁止引用 UI（单向）。
2. 只读 Gameplay 的事件与状态做呈现，不反向写玩法状态；需要交互时通过事件/回调回传。
3. UI 动画（缩放、飘字）用 unscaled 时间（`Time.unscaledDeltaTime` / Tween unscaled 模式），顿帧不冻结 UI。
4. 文本更新避免每帧字符串拼接（Hot-Path 0 GC）；数字滚动用增量缓存。

本目录当前为空骨架（仅 asmdef 与本说明）；新增代码前先在 `AI_Context/MODULE_MAP.md` 登记行。
