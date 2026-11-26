# Agent Workflow Kit v4.0 托管规则

> 本段由 `scripts/workflow.py` 托管。可在标记外添加项目规则，不要手工编辑标记内内容。

- 工作流版本：`v4.0`。
- 标准 L1/L2 必须经过 STAGING、HUMAN_APPROVAL、EXECUTING、独立 WATCHDOG_VERIFY 和 CEO_ACCEPTANCE。
- Worker 写入必须命中批准的 Write Boundaries，且不得命中 Forbidden。
- 任务事实源：`AI_Context/TASKS/<Task ID>/`、`AI_Context/PROJECT_BOARD.md` 与 `AI_Context/WORKFLOW_LOCK.toml`。
- Git commit、merge、push、tag、reset 只有 CEO 明确授权后才能执行。
- 未实际运行的编译、测试或审计不得写成 PASS。
- 项目技能位于 `.agents/skills/`；按阶段加载，施工期只加载 `worker-engine`。
