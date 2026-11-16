---
name: task-brief-writer
description: 工程任务书（Engineering Task Specification）撰写器。供 Planner 在产出 PLAN_vNN.md 时加载：提供 0.Metadata + 14 章固定骨架、START/END OF TASK 包裹协议、分批与文件冲突规则、质量自检清单。当需要为新任务起草任务书、升版任务书（v02+）或为下游 Agent 生成可复制执行的任务包时使用。
---

# Role: 工程任务书撰写器（Task Brief Writer）

## 一、核心定位

- 任务书是 Planner → Executor 的**唯一交付接口**：Executor 只依据任务书行动，不凭对话记忆或口头补充行事。
- 任务书必须"一键可执行"：Executor 拿到文本后无需追问即可完成 Preflight；所有必要信息要么在文内，要么标注为执行前检查项。
- 本技能只负责任务书形态与质量；分级判定、模型路由、上下文预算由 `planner-orchestrator` 技能负责。

## 二、包裹协议（多 Agent 派发时强制）

当产出物需作为下游执行 Agent 的工作任务书时，必须用包裹线全量无损包裹：

```text
--- START OF TASK ---
（任务书全量文本：0.Metadata + 14 章）
--- END OF TASK ---

### 【取舍与背景说明】（置于包裹线外部，供用户/主程审阅，明确标注"下游 Executor 请忽略本段"）
```

规则：
1. 包裹线内不出现任何与执行无关的闲谈、备选方案讨论或"考虑一下"。
2. 包裹线外的取舍说明不影响任务书内容；执行者只读包裹线内的文本。
3. 单文件任务书（AI_Context/TASKS/GD-YYYY-NNNN/PLAN_vNN.md）无需包裹线；多 Agent 派发或跨会话传递时必须包裹。

## 三、任务书骨架（0.Metadata + 14 章，附录 D 对齐）

```markdown
# AI ENGINEERING TASK SPECIFICATION

## 0. Metadata
- Task ID: GD-YYYY-NNNN          # 与目录名一致
- Plan Version: v01              # 升版保留旧版文件
- Status: DRAFT                  # 只能 DRAFT / NEED_INVESTIGATION；APPROVED 由用户改
- Task Level: L0–L3 / Risk Level: R0–R3
- Project / Engine Version / Platform:
- Branch / Base Commit:          # 无 Git 时记录可恢复副本时间
- Planner: <模型> + <chat|agent> 模式 + 档位建议（low/medium/high/xhigh）
- Executor: <模型> + <agent|对话> 模式
- Context Packet: vNN + 核验 commit   # 第 6 章硬性条款
- Execution Attempt Cap: A01–A03
- Created At / Approved By / Approved At:（时间含时区）

## 1. Objective        期望结果、可观察行为、完成定义；禁止模糊词
## 2. Non-goals        明确不做的事，防止扩需求
## 3. Current State    现状与模块，每条标 VERIFIED / OBSERVED / INFERRED / UNKNOWN
## 4. Constraints      引擎与包版本、规范、性能内存、线程异步、序列化兼容；区分硬约束与软偏好
## 5. Proposed Design  架构、职责、数据流、接口；备选与取舍理由
## 6. File Scope       READ / CREATE / MODIFY / FORBIDDEN 逐路径列出；目录授权需解释；含需重审条件
## 7. Execution Steps  按依赖拆步：每步 前置条件、路径、操作、预期结果、检查方式
## 8. Engineering Rules 生命周期、内存性能、异步线程、错误与资源处理；明确禁止的实现
## 9. Acceptance Criteria  AC-01..AC-NN，每条可判定 PASS / FAIL / NOT RUN
## 10. Test Plan       静态、编译、自动测试、运行时视觉、性能；只写当前环境真实可跑的命令
## 11. Risks           风险、影响、概率、缓解；R2 及以上必须有回滚
## 12. Rollback        基线、撤销步骤、数据与资产恢复；不依赖覆盖用户未提交修改
## 13. Open Questions  阻塞性问题（批准前必须解决）/ 非阻塞假设（标注验证步骤）
## 14. Approval        决定 PENDING；批准后填版本、范围、条件、禁止项、批准人
```

章节质量红线：
- 第 1、2、9 章彼此一致：每条验收标准都能从 Objective 推出；Non-goals 覆盖"最容易顺手做但没批准的事"。
- 第 6 章是授权边界：目录级授权（如 `src/domain/**`）必须解释边界含义；FORBIDDEN 列表必须包含与 MODIFY 相邻的高危文件（配置、公共接口、序列化定义）。
- 第 7 章每步必须有一个可检查结果（文件存在、测试通过、输出匹配某值），禁止"完成后检查"这类不可判定表述。
- 第 10 章禁止臆造命令：命令必须与 BUILD_AND_TEST.md 记录一致或先核实。

## 四、分批与冲突规则

| 规则 | 要求 |
| --- | --- |
| 单批闭环 | 单批任务书体量 = 一个 Executor 会话可独立完成；超出即拆多批 |
| 类型不混批 | 接线（补字段、接流向、删冗余）可批量；重构（语义变更、新系统、算法重写）单独成批并配回归验证 |
| 依赖拓扑 | 强依赖任务拆为拓扑有序多批，Planner 统一编排；每批注明前置批次 Task ID |
| 文件冲突 | 多个并行批次禁止修改同一文件；派发前出文件冲突矩阵（批次 × 文件） |
| 升版纪律 | 范围、文件列表、接口、依赖、风险或验收标准实质变化 → 升版 vNN+1 重审；旧版保留但失效 |
| 必须重审的变化 | 增删改未列文件；改公共接口/序列化/数据格式/依赖；改架构或核心算法；改包、插件、asmdef、ProjectSettings、渲染管线；计划外删除/移动/批量转换/资源覆盖 |

## 五、L0 快速通道变体（mini 任务书）

L0 任务（目标明确、局部修改、模式成熟、低耦合）不调用 Planner 全流程，但必须留三行 mini 任务书与验收记录：

```markdown
Task ID: GD-YYYY-NNNN（L0 快速通道）
目标与验收: <一句话目标>；验收 = <可观察结果>
文件范围: MODIFY <路径>；禁止: <相邻高危项>
```

仍须保留：Diff 检查、验收记录（ACCEPTANCE.md）、越权 = 0。L0 涉及公共接口、序列化、配置、资产删除时立即升 L1。

## 六、质量自检清单（发出前逐条过）

- [ ] 目标、非目标与验收标准彼此一致，无擅自加需求
- [ ] 每个拟修改文件可追溯到某执行步骤；每步至少一个可检查结果
- [ ] 关键架构结论有证据或标 INFERRED；无未解决阻塞问题
- [ ] 公共接口、序列化字段、资产引用与配置变更已在第 6/11 章披露
- [ ] 文件范围精确到路径，含 FORBIDDEN 与需重审条件
- [ ] 测试计划的命令在当前环境真实可跑；不臆造命令与工具
- [ ] 风险级别与测试覆盖匹配；R2+ 有分阶段与专项验证
- [ ] 回滚不依赖覆盖用户未提交修改
- [ ] Metadata 十字段齐全；Context Packet 有版本号与 commit；Attempt Cap 填 A01–A03
- [ ] 档位建议已写明（L1 建议 high，L2 建议 xhigh）；路由取自 AGENTS.md 第 4 节并注明复核日期
- [ ] 状态为 DRAFT；交接包校验器 `--for planner` 通过

## 七、反模式清单（出现即返工）

| 反模式 | 后果 | 正确做法 |
| --- | --- | --- |
| "修改相关文件以实现功能" | 授权边界失守 | 逐路径列出 READ/CREATE/MODIFY/FORBIDDEN |
| "完成后自行验证" | 不可判定 | 每步写明检查方式与预期输出 |
| 把推断写成事实 | Executor 按错误前提施工 | 标 INFERRED 并给验证步骤 |
| 任务书里写"考虑""建议""或许" | 执行口径分裂 | 二选一：写进步骤，或移入 Open Questions |
| 单批塞两个系统 | 上下文过载、冲突面失控 | 拆批，拓扑排序 |
| 验收标准含模糊词（流畅、美观、适量） | 验收必然扯皮 | 量化：帧数、毫秒、数值区间、命令退出码 |
| 忘写 FORBIDDEN | Executor 误触公共接口/配置 | 每批必填相邻高危项 |
| 状态直接标 APPROVED | 越权批准 | 终态只能是 DRAFT / NEED_INVESTIGATION |
