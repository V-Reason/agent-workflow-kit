# KNOWN_ISSUES — 已知问题与历史决策

> 发现即登记；与代码/资产冲突时以工程文件为准并把对应上下文条目标 STALE。

| # | 日期 | 问题/决策 | 影响 | 状态 | 关联任务 |
| --- | --- | --- | --- | --- | --- |
| 1 | 2026-11-15 | ProjectAuditWindow 的命名检查只覆盖 Assets/Scripts 下的 .cs | 其他目录命名漂移不会告警 | OPEN | — |
| 2 | 2026-11-15 | BootstrapSceneMenu 使用 FindObjectOfType（2022.3 LTS 兼容） | 迁移 Unity 6 后建议换 FindFirstObjectByType 消除弃用告警 | OPEN | — |
| <n> | <日期> | <问题描述> | <影响> | OPEN/CLOSED | GD-YYYY-NNNN |

## 登记规则

1. Worker 发现既有缺陷：只报告不修复（除非在批准范围内），登记本表。
2. CLOSED 条目必须附证据位置（EVIDENCE/ 路径或操作记录）。
3. 决策类条目同步登记 DECISION_LOG.md。
