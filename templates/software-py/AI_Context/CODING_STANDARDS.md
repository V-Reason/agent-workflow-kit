# CODING_STANDARDS — 编码规范（L1 固定前缀引用项）

## 强制门禁（V1/V3 验证层次，VALIDATING 前必须全绿）

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

## 语言与工具约定

1. Python ≥ 3.12；全量公开函数强类型注解；`mypy --strict` 零豁免（确需豁免用 `# type: ignore[错误码]` 逐行说明理由）。
2. 行宽 100；ruff format 为唯一定版工具；导入排序由 ruff（isort 规则）托管。
3. 命名：模块/函数 snake_case，类 PascalCase，常量 UPPER_SNAKE_CASE；测试函数 `test_<被测行为>_<场景>_<预期>`。

## 代码纪律

1. 严禁空 catch / 吞异常；未知异常捕获必须带上下文抛出或转译。
2. 资源（文件、连接、句柄）必须 `with` / `contextlib` 管理，异常路径也确定性释放。
3. 重试必带指数退避 + 随机抖动 + 最大深度；外部调用必须挂超时。
4. 对外契约用 frozen dataclass DTO；禁删既有字段、禁改字段语义；枚举反序列化兜底未知值。
5. 注释预算净零：只写 Why 与 Context；禁止"代码在做什么"复读机注释。
6. 最小补丁：不顺手重构、不顺手格式化无关代码；发现既有问题先报告。
7. 不把 TODO 或伪代码报告为完成；不改测试断言迎合错误实现。

## 提交与分支

- 分支命名：`ai/GD-YYYY-NNNN-短描述`（L1/L2 任务）；默认不 commit，由用户审查 Diff 后自行提交。

---
最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
