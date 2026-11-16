# AGENTS.md — <项目名> 项目级 Agent 规范（Python）

> 本文件只写本项目特有约束；角色、状态机、模型路由与通用红线以 `agent-workflow-kit/AGENTS.md` v3.0 为准。

## 0. 授权门

- 动手写入必须有 CEO 批准的 PLAN 版本与 `APPROVAL_RECORD.md`。
- 修改范围严格等于批准 File Scope；越界立即停止。
- 未批准时只允许读仓、Preflight 和只读取材。
- L0 可由 CEO 用三行 mini 简报直派 Worker，仍须 Diff 与验收记录。

## 1. 唯一正式入口

- 任务目录：`AI_Context/TASKS/GD-YYYY-NNNN/`
- 看板：`AI_Context/PROJECT_BOARD.md`
- 上下文：`00_CONTEXT_MANIFEST.md` + `FEED_DROP/`
- 施工员：`worker-engine`
- 独立监察：`watchdog-inspector`

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 --files src/app/example.py
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

## 2. 门禁命令

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

全部在项目根执行，退出码非 0 即失败。`AI_Context/` 被 Ruff、mypy、pytest 显式排除，暂存副本不参与质量门禁。

## 3. 分层红线

1. `src/app/domain/`：零 I/O、零框架、零外部依赖。
2. `src/app/application/`：只依赖 domain 与 Protocol 端口。
3. `src/app/infra/`：实现 application 端口，不被 application import。
4. `src/app/interfaces/`：组合根与输入输出转换。
5. 依赖方向：interfaces → application → domain；禁止循环。

## 4. 写入边界

| 操作 | 默认 | 必须 |
| --- | --- | --- |
| 读取源码 / 测试 / AI_Context | 允许 | 只读任务范围 |
| 修改业务文件 | 禁止 | 批准 File Scope |
| 新增依赖 / 改 pyproject | 禁止 | 专项批准与重审 |
| 删除 / 重命名 | 禁止 | 逐路径批准与回滚 |
| `.env` / 密钥 / 凭据 | 永不读取或提交 | 使用 `.env.example` 占位 |
| Git commit / merge / push | 禁止 | CEO 明确授权；禁止默认 push |

## 5. 技能装载

| 阶段 | 加载 |
| --- | --- |
| 运营、登记、备菜、回写 | `secretary-router`（Agent） |
| 规划与任务书 | `planner-orchestrator` + `task-brief-writer`；按需只读叠加 `software-architect` |
| 施工 | `worker-engine` 单装；不加载顾问 |
| L1/L2 验证 | `watchdog-inspector` 独立会话/实例 |

## 6. 归档

- 证据：`AI_Context/EVIDENCE/GD-YYYY-NNNN/`
- CEO 验收：`ACCEPTANCE.md`
- 验收后 24 小时内由 Secretary 依据 diff 起草 `CONTEXT_UPDATE_PROPOSAL.md`，CEO 审阅后合入。
