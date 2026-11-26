# 00 CONTEXT MANIFEST — GD-YYYY-NNNN

> 不要手工拼接源码。复制任务目录后运行：
> `python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN --files <paths>`

- Workflow Version: v3.1
- Task ID: GD-YYYY-NNNN
- Base Commit: <commit 或可恢复副本时间>
- Baseline Generated At: <YYYY-MM-DDTHH:MM:SS+08:00>
- Baseline Generation Mode: baseline
- Chat Safe: ON
- Budget Limit: 150000
- Need Files Rounds: 0

## Token Budget

| 层级 | 估算 Token | 预算/状态 |
| --- | ---: | --- |
| L1 | <n> | <是否位于 4,096–8,000 缓存甜点区> |
| L2 | <n> | 建议 ≤ 30,000 |
| L3 | <n> | 建议 ≤ 100,000 |
| Total | <n> | <是否超过预算> |

## File Mapping

| 暂存名 | 层级 | 原路径 | 估算 Token | SHA-256 |
| --- | --- | --- | ---: | --- |
| `L1__PROJECT_OVERVIEW.md` | L1 | `AI_Context/PROJECT_OVERVIEW.md` | <n> | <sha256> |

## Project Tree Summary

```text
<由脚本生成>
```

## Explicit Exclusions

- `.git/`、`.venv/`、缓存、Library、Temp、Logs
- 所有 `FEED_DROP/` 与 `NEED_FILES/`
- 未选择业务文件与敏感文件

## NEED_FILES Round Index
