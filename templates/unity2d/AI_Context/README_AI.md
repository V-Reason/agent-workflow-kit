# README_AI — 如何使用本项目的 AI 资料

本目录是 Agent 工作流 v2.0 第 6 章定义的项目上下文体系。Planner 裁剪上下文包、Executor 执行前核对、验证员取证都以本目录为单一来源。

## 使用规则

1. **分层加载，禁止全量投喂**：固定前缀引用 PROJECT_OVERVIEW + CODING_STANDARDS 摘要（4,000–8,000 tokens）；模块级只选 ARCHITECTURE / MODULE_MAP / DEPENDENCIES 的相关节（≤ 30,000 tokens）；代码级按任务裁剪（≤ 100,000 tokens）；单次总量 ≤ 150,000 tokens。
2. **可信度标记**：每条关键事实标 VERIFIED / OBSERVED / INFERRED / UNKNOWN / STALE；不得把推断写成事实。
3. **回写闭环**：验收通过后 24 小时内按 `TASKS/_templates/CONTEXT_UPDATE_PROPOSAL.md` 提交回写提案，用户审阅合入；每份文件末尾维护「最后核验日期 / 分支 / 维护人」。
4. **冲突裁决**：本目录与代码/资产冲突时，以工程文件为准，并把本目录对应条目标 STALE、登记 KNOWN_ISSUES.md。

## 目录清单

| 文件 | 内容 | 更新时机 |
| --- | --- | --- |
| PROJECT_OVERVIEW.md | 项目目标、引擎与平台 | 立项与方向变化时 |
| ARCHITECTURE.md | asmdef 分层与依赖规则 | 架构变化时 |
| MODULE_MAP.md | 程序集、目录、类与职责索引 | 每个任务验收后核对漂移 |
| CODING_STANDARDS.md | C# 编码规范与门禁 | 规范调整时 |
| DEPENDENCIES.md | Unity 包与外部插件台账 | 依赖变化时 |
| BUILD_AND_TEST.md | 编译、测试、验证方法 | 工具链变化时 |
| KNOWN_ISSUES.md | 已知问题与历史决策 | 发现即登记 |
| DECISION_LOG.md | 重要架构决策记录（ADR） | 决策发生时 |
| METRICS.md | 六项必记指标周台账 | 每周 |
| TASKS/GD-YYYY-NNNN/ | 交接包七件套按任务归档 | 每个任务 |
| EVIDENCE/ | 编译日志、测试摘要、Diff、截图 | 验证取证时 |

任务模板：`TASKS/_templates/`（与套件 `scripts/validate_handover.py` 校验规则一一对应）。

---
最后核验日期：2026-11-15｜分支：main｜维护人：<项目 Owner>
