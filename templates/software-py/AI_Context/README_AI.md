# README_AI — v4.0 项目上下文入口

Secretary 准备基线，Planner 从 `FEED_DROP/` 与 `00_CONTEXT_MANIFEST.md` 开始分析，Worker 在批准 Write Boundaries 内自主发现和施工，Watchdog 独立验证。`AI_Context/` 是所有角色的持久化事实源。

## 标准流程

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 --files src/app/example.py
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

## 加载规则

1. L1 固定层长期稳定，建议 4,096–8,000 Token。
2. L2 模块层只选相关架构、看板、模块地图与依赖。
3. L3 代码层由 Secretary 用脚本复制真实文件，不在 Markdown 中手工粘贴。
4. Chat 拖拽与 Agent 直读共用同一 `FEED_DROP`；Agent 仍可只读检索全仓。
5. `FEED_DROP/` 与 `NEED_FILES/` 被 Git 忽略；`00_CONTEXT_MANIFEST.md` 的轮次索引与 SHA-256 入库。
6. 关键事实标 VERIFIED / OBSERVED / INFERRED / UNKNOWN / STALE。
7. Agent Planner 默认不产生普通 `NEED_FILES`；Chat Planner 缺仓库时用 `--append --reason` 分轮补料。

## 项目文件

| 文件 | 内容 |
| --- | --- |
| `PROJECT_BOARD.md` | Secretary 的 Attention Queue 与 Ticket Index |
| `PROJECT_OVERVIEW.md` | 目标、边界与技术基线 |
| `ARCHITECTURE.md` | 分层与依赖规则 |
| `MODULE_MAP.md` | 模块、路径与职责索引 |
| `DEPENDENCIES.md` | 外部依赖与审批规则 |
| `BUILD_AND_TEST.md` | 真实门禁与证据位置 |
| `CODING_STANDARDS.md` | 编码和评审纪律 |
| `KNOWN_ISSUES.md` | 已知风险 |
| `DECISION_LOG.md` | 架构决策 |
| `METRICS.md` | 六项运营指标 |
| `TASKS/GD-YYYY-NNNN/` | Task ID、Manifest、Plan、批准、报告和验收 |

## 写回

验收后由 Secretary 根据已接受 diff 起草 `CONTEXT_UPDATE_PROPOSAL.md`，CEO 审阅后合入。长期文档与代码冲突时以代码和真实运行结果为准，相关条目标 STALE。
