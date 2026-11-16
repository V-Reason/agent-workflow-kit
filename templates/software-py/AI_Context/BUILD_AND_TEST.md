# BUILD_AND_TEST — 构建、测试与验证方法（L1）

> Worker 与 Watchdog 只能引用本文件登记的命令；未实际运行一律写 `NOT RUN`。

## 环境

- Python ≥ 3.12
- uv
- 依赖由 `pyproject.toml` 与 `uv.lock` 锁定

```bash
uv sync
```

## 门禁

| 目的 | 命令 | 期望 |
| --- | --- | --- |
| 依赖同步 | `uv sync` | exit 0 |
| 格式 | `uv run ruff format --check .` | exit 0 |
| Lint | `uv run ruff check .` | exit 0 |
| 类型 | `uv run mypy` | exit 0 |
| 自动测试 | `uv run pytest` | 全绿 |
| 导入冒烟 | `uv run python -c "import app"` | exit 0 |
| CLI 冒烟 | `uv run app list` | exit 0 |

`AI_Context/` 被 Ruff、mypy 与 pytest 排除，防止 `FEED_DROP` 副本影响门禁。

## 上下文与交接

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN --files src/app/example.py
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for archive
```

## V0–V5

| 层 | 内容 |
| --- | --- |
| V0 | 计划、接口、数据流、Non-goals 审阅 |
| V1 | ruff + mypy |
| V2 | 依赖同步、导入冒烟 |
| V3 | pytest 单元与集成 |
| V4 | CLI/运行时行为 |
| V5 | 有性能敏感模块后登记 benchmark |

## 证据

命令、版本、退出码、日志与截图存入 `AI_Context/EVIDENCE/GD-YYYY-NNNN/`，执行报告与 ACCEPTANCE 使用相对路径引用。

---

最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
