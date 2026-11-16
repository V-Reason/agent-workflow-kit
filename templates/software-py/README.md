# software-py — Python 通用软件项目模板

Agent 工作流 v2.0 配套模板：**src 四层架构 + uv + ruff + mypy + pytest + AI_Context 上下文体系**。复制本目录即可开始一个新项目；骨架自带最小可运行示例（任务看板 CLI）与 9 个测试用例，开箱全绿。

## 快速开始

```bash
uv sync                                        # 创建 .venv、安装依赖（editable）
uv run pytest                                  # 9 个用例全绿
uv run ruff check . && uv run mypy             # 门禁零违规
uv run app add GD-2026-0001 "首个任务" --level 1
uv run app list
uv run app advance GD-2026-0001
```

未安装 uv 时先 `pip install uv`。Python 版本要求 ≥ 3.12（`.python-version`）。

## 结构导览

| 路径 | 职责 |
| --- | --- |
| `src/app/domain/` | 实体、值对象、领域错误；零 I/O 零依赖 |
| `src/app/application/` | 用例编排 + 端口（Protocol） |
| `src/app/infra/` | 仓库/适配器实现（内存仓库为默认实现） |
| `src/app/interfaces/` | CLI 组合根；替换存储只改 `build_service()` |
| `tests/unit/` | 领域与应用层快测 |
| `tests/integration/` | CLI 端到端慢测 |
| `AI_Context/` | v2.0 第 6 章上下文体系（9 文件 + 任务归档 + 证据） |
| `AI_Context/TASKS/_templates/` | 交接包七件套模板（与校验器一一对应） |
| `scripts/validate_handover.py` | 交接包校验器（项目内副本） |
| `AGENTS.md` | 项目级 Agent 规范（叠加套件总纲） |

## 依赖规则

`domain` 零 I/O 零外部依赖 → `application` 只依赖 domain 与 Protocol → `infra` 实现端口 → `interfaces` 组合根装配。单向依赖，禁止循环；出现第 3 处相似变动才允许新分层（三法则）。

## 实例化（复制后必做）

1. 改包名：全局替换 `src/app`、`app.`、`packages = ["src/app"]`、`[project.scripts]` 中的 `app` 为你的项目名（若直接沿用 `app` 可跳过）。
2. 填 `AI_Context/PROJECT_OVERVIEW.md`、`MODULE_MAP.md`（按实际模块增删行）。
3. `pyproject.toml` 的 name / description 更新；应用类项目建议删除 `.gitignore` 中的 `uv.lock` 忽略项以锁定依赖。
4. 删除示例模块时同步更新 `MODULE_MAP.md` 与测试。
5. `git init && git add -A && git commit`（由你自己执行，不交 Agent）。

## 常用门禁命令

| 目的 | 命令 |
| --- | --- |
| 全部测试 | `uv run pytest` |
| 静态检查 | `uv run ruff check .` |
| 格式检查 | `uv run ruff format --check .` |
| 类型检查 | `uv run mypy` |
| 交接包校验 | `python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor` |

## 与方法论的对应

- 分层与门禁 ↔ v2.0 第 6 章（上下文）、第 12 章（验证层次 V1/V3）
- `AGENTS.md` ↔ 第 3、4、10、11 章的可执行摘要
- `AI_Context/TASKS/_templates/` ↔ 附录 C–H
- `METRICS.md` ↔ 第 15 章六项必记指标
