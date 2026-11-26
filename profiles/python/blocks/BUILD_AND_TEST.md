## Python 工作流门禁

根据项目现有工具链运行，建议：

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

`AI_Context/` 必须被静态检查与测试收集器排除。
