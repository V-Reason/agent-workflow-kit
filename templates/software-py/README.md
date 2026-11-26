# software-py — Python 通用软件 v4.0 模板

面向 CEO + Secretary / Planner / Worker / Watchdog 工作流的 Python 项目骨架：四层架构、`FEED_DROP` 真实源文件投喂、项目看板、uv/ruff/mypy/pytest 门禁和任务凭证。

## 通过 v4.0 装配器使用

```bash
python scripts/workflow.py create <project> \
  --layers core,generic,python,python-starter --yes
```

装配器会从 canonical 源安装工作流脚本、技能、任务模板和项目锁；本目录只提供 Python starter 资产。Python 要求 ≥ 3.12。首次装配后填写 `AI_Context/PROJECT_OVERVIEW.md`、`MODULE_MAP.md` 与 `PROJECT_BOARD.md`。

## 结构

| 路径 | 职责 |
| --- | --- |
| `src/app/domain/` | 实体、值对象、领域错误；零 I/O |
| `src/app/application/` | 用例与 Protocol 端口 |
| `src/app/infra/` | 端口实现与外部适配 |
| `src/app/interfaces/` | CLI 与组合根 |
| `tests/unit/`、`tests/integration/` | 自动回归 |
| `AI_Context/PROJECT_BOARD.md` | Secretary 维护的 Attention Queue + Ticket Index |
| `AI_Context/TASKS/_templates/` | v4.0 任务凭证 |
| `AGENTS.md` | 项目级授权、分层和技能装载 |

## 首个任务

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --files src/app/interfaces/cli.py
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

`FEED_DROP/` 与 `NEED_FILES/ROUND_NN/` 只存在于本地并被 Git 忽略；`00_CONTEXT_MANIFEST.md` 入库保存来源、Token、SHA-256 与 append-only 轮次索引。

## 质量隔离

`pyproject.toml` 显式让 Ruff、mypy、pytest 排除 `AI_Context/`，避免暂存副本干扰源代码质量门禁。

## 手工检查 starter

装配后可运行项目门禁：

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

1. 按需改包名 `app`、入口和项目元数据。
2. 填写 AI_Context 架构、模块、依赖和看板。
3. 如需把 `uv.lock` 纳入版本控制，删除 `.gitignore` 对应忽略项并使用 `uv sync --locked`。
4. Git 初始化和首次提交由 CEO 明确执行；v4.0 装配器不会自动 commit。
