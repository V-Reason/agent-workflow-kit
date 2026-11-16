# AI ENGINEERING TASK SPECIFICATION — 工程任务书模板 v3.0

> 使用：复制到任务目录改名 PLAN_v01.md；Planner 填写；状态只能是 DRAFT / NEED_INVESTIGATION，
> APPROVED 由用户审阅后亲自修改并写 APPROVAL_RECORD.md。撰写纪律见 skills/task-brief-writer。

## 0. Metadata
Task ID: GD-YYYY-NNNN / Plan Version: v01 / Status: DRAFT
Task Level: L1 / Risk Level: R1
Project: <项目名> / Engine Version: Python 3.12 / Platform: <目标平台>
Branch / Base Commit: <分支 / commit；无 Git 写可恢复副本时间>
Planner: <模型> + chat 模式 + high 档位建议（L2 改 xhigh）
Worker: <模型> + agent 模式
Watchdog: <独立会话/实例 + 模型 + 档位>
Context Manifest: 00_CONTEXT_MANIFEST.md + Base Commit <哈希或恢复时间>
Execution Attempt Cap: A01-A03
Created At: <YYYY-MM-DD HH:MM 时区> / Approved By: <留空> / Approved At: <留空>

## 1. Objective
<可观察行为描述的目标与完成定义；禁止模糊词>

## 2. Non-goals
- <明确不做的事>

## 3. Current State
- VERIFIED：<已确认事实 + 证据位置>
- OBSERVED：<来自描述或现象>
- INFERRED：<推导 + 验证方式>
- UNKNOWN：<信息不足项 + 索取计划>

## 4. Constraints
- 硬约束：<引擎与包版本、规范、性能内存、线程异步、序列化兼容>
- 软偏好：<可协商项>

## 5. Proposed Design
<架构、职责、数据流、接口；备选方案与取舍理由；公共接口变更必须在此披露>

## 6. File Scope
- READ: <路径>
- CREATE: <路径>
- MODIFY: <路径>
- FORBIDDEN: <相邻高危路径（配置、公共接口、序列化定义、AI_Context 之外文档）>
- 需重审条件：<出现哪些情况必须升版>

## 7. Execution Steps
| # | 前置条件 | 路径/位置 | 操作 | 预期结果 | 检查方式 |
| --- | --- | --- | --- | --- | --- |
| 1 | <前置> | <路径> | <操作> | <可检查结果> | <命令/观察点> |

## 8. Engineering Rules
- 生命周期 / 内存性能 / 异步线程 / 错误与资源处理规则；明确禁止的实现方式

## 9. Acceptance Criteria
- AC-01: <可判定 PASS / FAIL / NOT RUN 的条目>
- AC-02: <...>

## 10. Test Plan
- 静态：`uv run ruff check .` / `uv run mypy`
- 编译：`uv sync && uv run python -c "import app"`
- 自动测试：`uv run pytest`
- 运行时：<真实可跑的命令>

## 11. Risks
| 风险 | 影响 | 概率 | 缓解 |
| --- | --- | --- | --- |
| <风险> | <影响> | <高/中/低> | <缓解措施> |

## 12. Rollback
- 基线：<Base Commit / 副本时间>
- 撤销步骤：<每文件一句话命令>
- 不依赖覆盖用户未提交修改

## 13. Open Questions
- 阻塞：<必须在批准前解决>
- 非阻塞假设：<标注验证步骤>

## 14. Approval
- Decision: PENDING
- 批准后填写：Plan Version: v01 / Approved Scope: <逐条路径与操作> / Conditions: <附加约束> / Explicitly Forbidden: <明确禁止项> / Approved By: <批准人> / Approved At: <时间含时区>
