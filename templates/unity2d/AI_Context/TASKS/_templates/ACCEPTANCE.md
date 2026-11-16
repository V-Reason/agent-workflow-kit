# ACCEPTANCE — 验收回执模板（第 12 章）

> 使用：Watchdog（独立于 Worker）生成事实部分；最终决定由 CEO 作出。

Task ID: GD-YYYY-NNNN / 验收人: <Watchdog> / 时间: <YYYY-MM-DD HH:MM 时区>
验证层次: V0–V5 实际执行项：<列出>

| 项 | 期望 | 实测 | 证据 |
| --- | --- | --- | --- |
| AC-01 | <任务书原文> | <实测结果> | <命令+退出码 / 日志 / 截图路径> |
| AC-02 | <...> | <...> | <...> |
| 范围遵守 | 修改 100% 在批准范围内 | <一致 / 范围外 N 处> | <Diff 摘要路径> |
| 非目标保护 | 非目标行为不变 | <一致 / 回归点> | <回归命令输出> |
| 用量披露 | Usage 与档位如实 | <一致 / 缺失> | <执行报告第 7 节> |

未解决问题与警告:
- <逐条列出；无则写 none>

Watchdog 结论建议: PASS / PASS WITH WARNINGS / FAIL
用户决定: ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT
后续动作: <FOLLOW-UP 转新任务；REJECT 按 v3.0 第 13 章处理；ACCEPTED 后 24h 内提交上下文回写提案>
