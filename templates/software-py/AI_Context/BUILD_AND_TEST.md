# BUILD_AND_TEST — 构建、测试与验证方法（L1 固定前缀引用项）

> 任务书第 10 章（Test Plan）只允许引用本文件登记过的真实命令；禁止臆造命令。

## 环境准备

```bash
# 安装 uv（一次性）
pip install uv          # 或 curl -LsSf https://astral.sh/uv/install.sh | sh
uv sync                 # 创建 .venv 并安装项目与 dev 组依赖（editable 安装）
```

## 日常命令

| 目的 | 命令 | 期望结果 |
| --- | --- | --- |
| 安装/同步依赖 | `uv sync` | 退出码 0，生成 .venv |
| 运行 CLI | `uv run app list` | 输出任务列表（可为空） |
| 全部测试 | `uv run pytest` | 全绿；骨架预置 9 个用例 |
| 仅单元测试 | `uv run pytest tests/unit` | 全绿 |
| 仅集成测试 | `uv run pytest tests/integration` | 全绿 |
| Lint | `uv run ruff check .` | 0 违规 |
| 格式检查 | `uv run ruff format --check .` | 0 重排 |
| 类型检查 | `uv run mypy` | 0 错误 |
| 交接包校验 | `python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for executor` | exit 0 |

## V0–V5 验证层次映射（对照 v2.0 表 23）

| 层次 | 本项目对应 | 命令 |
| --- | --- | --- |
| V1 静态检查 | ruff + mypy | 见上表 |
| V2 编译构建 | Python 无编译；等价物为安装与导入检查 | `uv sync && uv run python -c "import app"` |
| V3 自动测试 | pytest 单元 + 集成 | 见上表 |
| V4 运行时验证 | CLI 真实运行 | `uv run app add GD-2026-0001 示例 && uv run app list` |
| V5 性能验证 | 暂不适用（出现性能敏感模块后补充基准命令） | — |

## 证据归档

验证证据（命令输出、日志、截图）存入 `AI_Context/EVIDENCE/GD-YYYY-NNNN/`；执行报告第 4 节引用相对路径。

---
最后核验日期：2026-11-15｜分支：main｜维护人：<项目 Owner>
