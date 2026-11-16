# BUILD_AND_TEST — 编译、测试与验证方法（L1 固定前缀引用项）

> 任务书第 10 章（Test Plan）只允许引用本文件登记过的方法；禁止臆造命令。

## 环境准备

1. Unity Hub 安装 **Unity 2022.3 LTS**（或 Unity 6000.x，与 PROJECT_OVERVIEW.md 一致）。
2. 打开工程后等待 Assembly 编译完成；首次打开 Unity 会补全 manifest 内置模块并生成 .meta。
3. Input System 首次启用时弹窗要求重启并切换 Active Input Handling —— 该项属 ProjectSettings 变更，由用户手工确认。

## 日常验证方法（V0–V5 映射，对照 v2.0 表 23）

| 层次 | 本项目对应 | 操作 | 期望 |
| --- | --- | --- | --- |
| V1 静态检查 | IDE 无红线 + 审计窗口 | GAMEDEV > 审计 > 项目结构审计 | FAIL = 0 |
| V2 编译构建 | Assembly 编译 | 打开工程 / Script Compilation | Console 0 error |
| V3 自动测试 | EditMode 测试 | Window > General > Test Runner > EditMode > Run All | 全绿（基线 6 用例） |
| V4 运行时视觉 | 编辑器实跑 | <按任务登记的场景与观察点> | <按任务> |
| V5 性能 | Profiler | Window > Analysis > Profiler | <按任务预算> |

## 命令行批处理（可选，CI 或批量验证）

```bash
# Windows 示例（路径按本机调整）；macOS/Linux 用对应 Unity 可执行路径
# 注意：不要追加 -quit；RunBatchAudit 会以 EditorApplication.Exit 显式控制退出码
"<UnityEditor>" -batchmode -nographics -projectPath "<工程根>" -executeMethod GAMEDEV.EditorTools.ProjectAuditWindow.RunBatchAudit -logFile audit.log
```

注意：
- 批处理执行前必须关闭编辑器实例；`-executeMethod` 需要静态公开方法。
- `RunBatchAudit()` 逐条输出审计日志（FAIL 行用 Error 级别），并以退出码报告结果：`FAIL > 0 → 1`，`FAIL = 0 → 0`。
- 退出码非 0 即门禁失败，可直接挂 CI 或脚本拦截；`audit.log` 末行的 `[ProjectAudit]` 汇总即为审计结果。

## 证据归档

验证证据（Console 截图、Test Runner 结果、审计输出、Profiler 采样）存入
`AI_Context/EVIDENCE/GD-YYYY-NNNN/`；执行报告第 4 节引用相对路径。

---
最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
