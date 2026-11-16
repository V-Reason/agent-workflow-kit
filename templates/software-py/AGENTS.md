# AGENTS.md — <项目名> 项目级 Agent 规范

> 本文件与套件总纲（agent-workflow-kit/AGENTS.md）叠加生效；本文件缺失的条款一律以套件总纲为准。
> 每个会话启动必读；本项目类型为 **Python 通用软件**（uv + ruff + mypy + pytest）。

## 0. 授权门（最高优先级）

- 只有用户明确批准的任务书版本（Status: APPROVED + APPROVAL_RECORD.md）构成写入授权。
- 未批准：只读模式，可做 Preflight 检查与只读调查，禁止任何写入。
- 修改范围 = 任务书第 6 章 File Scope 逐路径白名单；越界即停。

## 1. 本项目门禁命令（VALIDATING 必须全绿）

```bash
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

- 全部命令在项目根目录执行；退出码非 0 即门禁失败。
- 门禁失败时：先判首错，按 A01–A03 额度修复；连续两轮无可验证进展即停。

## 2. 分层红线（对齐 AI_Context/ARCHITECTURE.md）

1. `src/app/domain/`：零 I/O、零外部依赖、零框架 import；只放实体、值对象、领域错误、纯规则。
2. `src/app/application/`：只 import domain 与 ports（Protocol）；禁止 import infra 与 interfaces。
3. `src/app/infra/`：只实现 application 的端口；禁止反向被 application import。
4. `src/app/interfaces/`：组合根与输入输出转换；替换存储实现只改 `build_service()`。
5. 依赖方向单向：interfaces → application → domain；出现循环依赖 = 架构违规，立即停止。

## 3. 文件操作边界

| 操作 | 默认 | 需要批准 |
| --- | --- | --- |
| 读 src/tests/AI_Context | 允许 | 个人目录、密钥、.env |
| 创建/修改 | 仅任务书白名单路径 | 任何白名单外路径 |
| 删除/重命名 | 禁止 | 逐路径列出并说明回滚 |
| pyproject.toml 依赖变更 | 禁止 | 任务书披露 + 用户批准 |
| .env / 密钥 / 凭据 | 禁止读写 | 永不 |
| Git commit/push | 禁止 | 用户明确说"提交" |

## 4. 执行纪律

1. Preflight 六项逐项完成并写入执行报告第 1 节，未通过不动手。
2. 最小补丁；不顺手重构、不顺手格式化；既有缺陷只报告并登记 KNOWN_ISSUES.md。
3. 不虚构 API 与测试结果；未实际运行不声称通过；测试断言不许删改迎合实现。
4. 尝试额度 A01–A03；升级与重新规划不消耗额度；停止条件见套件总纲第 7/10 节。
5. 长任务（批量验证、编译重试）安排在错峰时段：工作日 12:00–14:00、18:00–次日 09:00、周末节假日（北京时间）。

## 5. 交接与归档

- 任务目录：`AI_Context/TASKS/GD-YYYY-NNNN/`（七件套模板在 `TASKS/_templates/`）。
- 交接前校验：`python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for <模式>`。
- 证据归档：`AI_Context/EVIDENCE/GD-YYYY-NNNN/`。
- 验收通过 24 小时内提交上下文回写提案（`_templates/CONTEXT_UPDATE_PROPOSAL.md`），用户审阅合入。

## 6. 技能装载

| 场景 | 加载 |
| --- | --- |
| 规划/分级/任务书 | planner-orchestrator（+ software-architect 叠加） |
| 执行 | executor-engine |
| 验证 | engineering-verifier（独立会话/实例，禁止自证） |
| 失败/指标复盘 | failure-retrospector |
