# ACCEPTANCE — 验收回执模板（第 12 章）

> 使用：Watchdog（独立于 Worker）生成事实部分；最终决定由 CEO 作出。

Task ID: GD-YYYY-NNNN / 验收人: <Watchdog> / 时间: <YYYY-MM-DD HH:MM 时区>
Workflow Version: v4.0
验证层次: V0–V5 实际执行项：<列出>

| AC | Class | Executor | Expected | Result | Primary Evidence |
| --- | --- | --- | --- | --- | --- |
| AC-01 | WORKER_AUTOMATABLE | WORKER | <任务书原文> | <PASS / FAIL / NOT RUN / BLOCKED / NOT APPLICABLE> | <TEST_RESULT+LOG / DIFF / HASH> |
| AC-02 | CEO_MANUAL_ACCEPTANCE | CEO | <人工验收项> | <结果> | <OBSERVATION / SCREENSHOT / VIDEO> |

视觉证据仅在无法稳定文本断言时使用，并记录：
- Visual Purpose: <观察目的>
- Visual Scenario: <执行场景>
- Visual Expected: <期望结果>

## Unplanned Change Review

| Path | Decision | Reason |
| --- | --- | --- |
| none | NOT APPLICABLE | 无边界内未计划改动 |

未解决问题与警告:
- <逐条列出；无则写 none>

Watchdog 结论建议: PASS / PASS WITH WARNINGS / FAIL
用户决定: ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT
后续动作: <FOLLOW-UP 转新任务；REJECT 按 v4.0 第 13 章处理；ACCEPTED 后 24h 内提交上下文回写提案>
