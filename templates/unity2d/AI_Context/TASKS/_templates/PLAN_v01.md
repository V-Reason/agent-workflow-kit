# AI ENGINEERING TASK SPECIFICATION — 工程任务书模板 v3.0（Unity 版）

> 使用：复制到任务目录改名 PLAN_v01.md；Planner 填写；状态只能是 DRAFT / NEED_INVESTIGATION，
> APPROVED 由用户审阅后亲自修改并写 APPROVAL_RECORD.md。撰写纪律见 skills/task-brief-writer。

## 0. Metadata
Task ID: GD-YYYY-NNNN / Plan Version: v01 / Status: DRAFT
Task Level: L1 / Risk Level: R1
Project: <项目名> / Engine Version: Unity 2022.3 LTS 或 Unity 6 / Platform: <目标平台>
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
- 硬约束：<Unity 版本、渲染管线（URP/Built-in）、PPU 约定、性能预算（GC/帧时间）、平台>
- 软偏好：<可协商项>

## 5. Proposed Design
<架构、职责、数据流、接口；备选方案与取舍理由；公共接口与 asmdef/序列化变更必须在此披露>

## 6. File Scope
- READ: <路径>
- CREATE: <路径（仅 .cs/.asmdef 等文本文件）>
- MODIFY: <路径>
- FORBIDDEN: <.prefab/.unity/.asset/.meta/.xlsx 资产、ProjectSettings、Packages/manifest.json、渲染管线配置>
- 用户手工清单：<Agent 不碰、由用户在编辑器完成的项（每条含路径、期望值、判据）>
- 需重审条件：<出现哪些情况必须升版>

## 7. Execution Steps
| # | 前置条件 | 路径/位置 | 操作 | 预期结果 | 检查方式 |
| --- | --- | --- | --- | --- | --- |
| 1 | <前置> | <路径> | <操作> | <可检查结果> | <编译/测试/审计> |

## 8. Engineering Rules
- 生命周期（Awake/OnEnable/OnDestroy 时序）、主线程约束、0 GC、对象池 maxSize、
  NonAlloc 检测、Editor 隔离、序列化兼容；明确禁止的实现方式

## 9. Acceptance Criteria
- AC-01: <可判定 PASS / FAIL / NOT RUN 的条目>
- AC-02: <...>

## 10. Test Plan
- 编译：Unity 打开工程后 Console 0 error（记录 Unity 版本）
- EditMode 测试：Window > General > Test Runner > EditMode > Run All（记录通过数）
- 结构审计：GAMEDEV > 审计 > 项目结构审计（FAIL = 0）
- 运行时视觉：<需要用户在编辑器实跑的场景与观察点，或 NOT RUN>
- 性能：<Profiler 采样点与预算，或 NOT APPLICABLE>

## 11. Risks
| 风险 | 影响 | 概率 | 缓解 |
| --- | --- | --- | --- |
| <风险> | <影响> | <高/中/低> | <缓解措施> |

## 12. Rollback
- 基线：<Base Commit / 副本时间>
- 撤销步骤：<每文件一句话命令；.meta 与资产一并考虑>
- 不依赖覆盖用户未提交修改

## 13. Open Questions
- 阻塞：<必须在批准前解决>
- 非阻塞假设：<标注验证步骤>

## 14. Approval
- Decision: PENDING
- 批准后填写：Plan Version: v01 / Approved Scope: <逐条路径与操作> / Conditions: <附加约束> / Explicitly Forbidden: <明确禁止项> / Approved By: <批准人> / Approved At: <时间含时区>
