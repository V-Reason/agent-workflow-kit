# README_AI — {{project_name}}

本目录是 Agent Workflow Kit v4.0 的持久化事实源。

```bash
python scripts/workflow.py status .
python scripts/workflow.py doctor .
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for planner
```

`FEED_DROP/` 与 `NEED_FILES/` 是 Git 忽略的本地投喂副本；`WORKFLOW_PROFILE.toml` 与 `WORKFLOW_LOCK.toml` 入库保存装配事实。
