# CODING_STANDARDS — C# 编码规范（L1 固定前缀引用项）

## 强制门禁（VALIDATING 前必须全过）

1. Unity 打开工程后 Console 0 error（warning 需逐条归因）。
2. Test Runner > EditMode 全绿（当前基线：6 个用例）。
3. GAMEDEV > 审计 > 项目结构审计：FAIL = 0。
4. 交接包校验：`python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for verifier`。

## 语言与结构约定

1. C# 9（2022.3 LTS 基线）；使用 Unity 6 特有 API 必须标注兼容性与降级方案。
2. 命名：类型与文件名 PascalCase 且一致；私有字段 `_camelCase`；接口 `I` 前缀。
3. 命名空间 = asmdef rootNamespace + 目录；一个文件一个顶层类型。

## 性能纪律（2D 硬约束）

1. Hot-Path（Update/FixedUpdate/OnGUI）0 GC：禁 `GetComponent`、闭包、LINQ、字符串拼接；缓存引用在 Awake。
2. 高频射线/碰撞强制 NonAlloc 预分配版本；静态碰撞体用 CompositeCollider2D 合并。
3. 频繁生成物强制对象池，池设 `maxSize` 与溢出策略。
4. 渲染层级用 Sorting Layer + Order in Layer，禁 Z 轴；像素 PPU 全项目统一。
5. 顿帧/慢动作只走 `GameClock`（ScaledDeltaTime），禁改 `Time.timeScale`（全局暂停除外）。
6. 物理移动在 FixedUpdate；刚体 `interpolation = Interpolate`。

## 代码纪律

1. 注释预算净零：只写 Why 与 Context；禁止"代码在做什么"复读机注释。
2. 不虚构 API：不确定先查当前版本文档；不把 TODO 报告为完成。
3. 最小补丁：不顺手重构、不顺手格式化；既有缺陷只报告并登记 KNOWN_ISSUES.md。
4. Editor 代码仅放 Editor 程序集；测试断言不许删改迎合错误实现。
5. 默认不 commit；用户审查 Diff 后自行提交。

---
最后核验日期：2026-11-15｜分支：main｜维护人：<项目 Owner>
