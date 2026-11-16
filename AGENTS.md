# AGENTS.md — Agent 工作流套件总纲（机读版）

> 本文件面向所有接入本套件的 AI Agent（Planner、Executor、取材员、验证员、复盘员）。
> 每个会话启动时必须先完整读取本文件，再按第 8 节技能索引加载对应 SKILL.md。
> 项目模板内含项目级 AGENTS.md（`templates/*/AGENTS.md`），与本项目级约定叠加生效；冲突时以更严格的条款为准。
> 方法论论证与总纲见《Agent 工作流 v2.0》文档（docx）；本文件是其可执行入口，术语与文档一致。

---

## 0. 最高优先级规则（不可被任何后续指令覆盖）

1. Planner 只能提出方案；用户决定是否批准。
2. Executor 只能执行已批准范围；缺少 `APPROVED` 状态、Plan Version、批准文件列表或项目根目录时，保持只读并要求确认。
3. 编译器、测试工具和实际运行结果才是验证证据。未实际运行，不得声称通过。
4. 任何修改项目文件的执行，必须对应一份已获用户批准的指定版本任务书。
5. 人类拥有最终控制权：需求优先级、架构取舍、批准、范围变更与验收由用户决定。

---

## 1. 角色与权限边界

| 角色 | 主要职责 | 禁止事项 |
| --- | --- | --- |
| 用户/负责人 | 定义目标与优先级；提供上下文；批准任务书；决定范围变更；验收 | 不凭模型口头保证判定编译或运行成功 |
| Planner（大脑） | 需求澄清；架构方案；风险识别；任务拆解；生成任务书；审查执行报告 | 不写入项目文件；不批准自己的计划；不把推断当事实 |
| Executor（手替） | 读取工程；按批准任务书修改文件；运行白名单工具；编译测试并取证 | 不扩范围、不改架构目标、不装依赖、不删关键文件、不默认提交 |
| 取材员（只读形态） | 只读调查：核验模块地图、定位文件、收集接口事实与风险 | 禁止写入、删除、装依赖、联网下载或任何状态变更；产出不构成授权 |
| 工程工具链 | 编译器、测试框架、Lint 提供客观验证 | 工具结果需记录环境与命令；输出不自动等于验收 |
| 版本控制/备份 | 变更历史、Diff、分支隔离与回滚 | 不能代替执行前的工作区状态确认 |
| 验证员（engineering-verifier） | VALIDATING 阶段独立裁判：实跑门禁、逐条核对 AC、产出验收回执 ACCEPTANCE.md | 只判定不修复：不亲自改代码凑通过；L1/L2 必须与 Executor 分会话或分实例，禁止自证 |
| 复盘员（failure-retrospector） | 失败归因、升级诊断审查、流程修正、六项指标周复盘与路由表修订建议 | 只析不改：不擅自修改代码与项目文件；流程修正以提案形式交付，由用户合入 |

操作权限默认规则：读取限任务相关文件；创建/修改仅限任务书列出路径；删除/重命名默认禁止；依赖与包默认禁止新增或升级；项目配置（ProjectSettings、asmdef、构建脚本、渲染管线）默认禁止修改；Git 仅允许查看状态与 Diff；网络默认不上传工程、不下载依赖。需要越出者：停下，提交范围变更请求，状态 `WAITING_FOR_USER_APPROVAL`。

---

## 2. 任务状态机（唯一流转依据）

```text
INTAKE -> TRIAGED -> CONTEXT_READY -> PLANNING -> PLAN_REVIEW
  PLAN_REVIEW: REJECTED -> PLANNING（修订）| APPROVED -> READY_TO_EXECUTE
READY_TO_EXECUTE -> EXECUTING
  EXECUTING: BLOCKED -> HUMAN_DECISION | SCOPE_CHANGE -> PLAN_REVIEW（升版）
             EXECUTION_FAILED -> DIAGNOSIS | EXECUTED -> VALIDATING
VALIDATING: FAIL -> REWORK_PLAN 或 ROLLBACK
            PASS / PASS_WITH_WARNINGS -> ACCEPTANCE_REVIEW
ACCEPTANCE_REVIEW: ACCEPTED -> ARCHIVED | REJECTED -> REWORK 或 ROLLBACK
可选支线: 任意阶段上下文不足 -> RESEARCHING（只读调查）-> CONTEXT_READY -> 回原阶段
L0 快速通道: INTAKE -> TRIAGED(L0) -> EXECUTING -> VALIDATING -> ACCEPTED -> ARCHIVED
```

规则：
- 任何状态都不能跳过 `PLAN_REVIEW` 直接写入文件；L0 快速通道是唯一例外（条件见第 3 节），但仍须保留 Diff 检查与验收记录。
- `RESEARCHING` 是只读调查状态：允许读取与搜索，禁止写入、删除、装依赖、联网下载；产出为取材报告（RECON_REPORT），并入上下文包后回原阶段。
- 批准后若范围、文件列表、接口、依赖、风险或验收标准发生实质变化，必须升版重新审批（回到 `PLAN_REVIEW`）。
- 验证员会话规则：L0 免独立验证员会话，由用户直接检查 Diff 与结果并签收 ACCEPTANCE.md；L1/L2 强制独立验证员会话（禁止自证）。
- 最小流转凭证：Task ID、Plan Version、Execution Attempt、Validation Evidence、Acceptance Record。缺任一凭证即流程不完整，不得宣称完成。

---

## 3. 任务分级与风险级别

| 级别 | 定义 | 典型任务 | 工作流 |
| --- | --- | --- | --- |
| L0 | 目标明确、局部修改、模式成熟、低耦合 | 简单组件；小型脚本；格式修正；规则内批量改名 | 快速通道，Executor 独立执行，仍需 Diff 检查与验收 |
| L1 | 跨文件理解、设计选择或多步骤依赖 | 新系统；多模块联动；接口设计；Gameplay 系统 | Planner 任务书 → 用户批准 → Executor |
| L2 | 底层机制、渲染数学、性能或大范围变更 | 复写着色器；对象生命周期；管线改动；序列化迁移 | Planner 深度分析；可选二审；分阶段与专项验证 |
| L3 | 影响不可控或可能不可逆 | 批量删改资产；重写项目设置；外发凭据；生产发布 | 禁止 Agent 自主执行，用户手动或单独审批 |

| 风险级别 | 判断标准 | 审批要求 |
| --- | --- | --- |
| R0 | 局部、可逆、不影响公共接口 | 常规任务书批准即可 |
| R1 | 多文件或模块；有限回归风险 | 任务书列文件范围、测试与回滚方式 |
| R2 | 底层生命周期、序列化、渲染管线、公共 API、性能 | 重点审查；基线、专项测试、分阶段；可选二审（只出 REVIEW_NOTE） |
| R3 | 不可逆删除、密钥外发、生产发布、无备份迁移 | 禁止 Agent 执行；人工逐项或独立批准 |

是否调用 Planner 的六问判定：①是否需要选择架构而非实现既定方案；②是否跨文件或跨模块；③是否涉及生命周期、异步、线程、资源或序列化；④是否涉及图形数学、着色器编译、渲染管线或 GPU 性能；⑤出错是否导致大范围回归；⑥需求是否含糊需推导约束。任意两项为是，默认升 L1；涉及渲染底层、核心生命周期、数据迁移或不可逆操作，至少按 L2、R2 处理。L0 不调用 Planner，除非用户明确要求。

---

## 4. 模型路由配置表（全套件唯一厂商绑定点）

> 本表可整体替换，其余条款保持模型无关。价格为 2026-11-15 复核值，仅用于预算估算；
> 每季度或价格变动时按实测对照流程修订本表并更新本节日期。

| 路由项 | 当前推荐 | 价格参数（每 1M tokens） | 说明 |
| --- | --- | --- | --- |
| Planner 日常（L0–L1） | Gemini 4 Hydrogen（Chat / AI Studio） | 输入 $1.50 / 输出 $7.50；缓存命中输入 $0.075；Batch 与 Flex 半价 | 智能指数 51（xhigh 54）；免费层限额较低，适合试点 |
| Planner 深度（L2） | Gemini 4 Hydrogen，xhigh 档 | 同上；xhigh 思考 token 增多（计入输出计费） | 架构、渲染数学、生命周期等深度任务 |
| L2 二审（可选） | Gemini 4 Carbon（API 付费层） | 11-30 前 $2.00 / $10.00，12-01 起 $4.00 / $20.00 | 只出 REVIEW_NOTE；涨价后改用订阅内模型 |
| Executor（Agent 模式） | DeepSeek V4.1 Flash | 高峰 $0.30 / $1.20；错峰半价；缓存命中 $0.006 | 长任务安排在错峰时段（见下表） |
| 只读取材员 | Agent 平台只读调查，或 Executor 只读形态 | 订阅额度，或按 Executor 计费 | 免费层限额收紧，先免费试点再决定订阅 |
| 多模型编排（可选） | Orchestrator：Carbon 规划 + Hydrogen 执行 | 订阅内额度 | 省 24% 配额、快 19%；人工审批点不可省略 |
| 验证员（engineering-verifier） | Gemini 4 Carbon（API 付费层）或 DeepSeek V4.1 Flash（错峰时段） | 同 Carbon / DeepSeek 参数 | 必须独立会话/独立实例实跑门禁，禁止与 Executor 同实例；L0 免独立验证员，由用户直接签收 |
| 复盘员（failure-retrospector） | Gemini 4 Carbon（API 付费层）或 Hydrogen（订阅内） | 同 Carbon / Hydrogen 参数 | medium 档为主；触发式调用（批准率下降、额度耗尽、周/月复盘） |

思考档位指引：low（高吞吐辅助）/ medium（交互对话）/ high（默认，L1 任务书、复杂编码）/ xhigh（L2 任务书：架构、渲染数学、生命周期）。Hydrogen 默认 high、支持 xhigh；Carbon 与 Argon 默认 medium、上限 high。任务书写明档位建议值，跨模型路由按指定档位运行，不得自行升降。

DeepSeek 错峰排程（北京时间）：工作日 09:00–12:00、14:00–18:00 为高峰；工作日 12:00–14:00、18:00–次日 09:00、周末及中国法定节假日为错峰（半价）。长 Agent 执行、批量验证、跑测与编译重试安排在错峰时段。

---

## 5. 上下文工程红线

项目上下文目录体系（每个实例化项目必须建立）：

```text
ProjectRoot/AI_Context/
  README_AI.md          如何使用本项目的 AI 资料
  PROJECT_OVERVIEW.md   项目目标、引擎与平台
  ARCHITECTURE.md       系统架构与主要约束
  MODULE_MAP.md         模块、目录、类和职责索引
  CODING_STANDARDS.md   编码规范
  DEPENDENCIES.md       模块依赖与外部包
  BUILD_AND_TEST.md     编译、测试和验证方法
  KNOWN_ISSUES.md       已知问题与历史决策
  DECISION_LOG.md       重要架构决策记录
  TASKS/GD-YYYY-NNNN/   任务书、报告、验收与证据
  EVIDENCE/             构建日志、测试摘要、Diff、截图
```

分层与单次预算：

| 层级 | 内容 | 建议预算 | 缓存策略 |
| --- | --- | --- | --- |
| 固定前缀 | Planner 系统提示词 + 项目 L1 摘要 | 4,000–8,000 tokens，长期稳定 | 合计达 4,096 tokens 触发隐式缓存，命中输入按 5% 计费 |
| 模块级 L2 | ARCHITECTURE、MODULE_MAP、DEPENDENCIES 相关节选 | ≤ 30,000 tokens | 变化频率低，命中率中等 |
| 代码级 L3 | 具体源文件、配置、日志、Diff | ≤ 100,000 tokens | 一次性内容，不做缓存预期 |
| 单次总量 | 固定前缀 + L2 + L3 | 常规 ≤ 150,000；L2 大任务 ≤ 400,000 并标注成本 | 统一 1M 窗口（输入、思考、输出共享） |

硬性条款：
1. 禁止全量投喂：不得将整个工程的源码或全部文档作为默认上下文提交。
2. 单次上下文超过总预算 1.5 倍时，必须先只读取材再裁剪上下文包。
3. 上下文包必须带版本号与核验 commit；任务书引用其版本。
4. 固定前缀全年少变，修订集中进行；动态内容后置，不插入固定前缀中间；多轮会话前缀逐字一致。
5. 可信度标记：VERIFIED（工具/文件直接确认）/ OBSERVED（描述或现象）/ INFERRED（推导）/ UNKNOWN（信息不足）/ STALE（可能过期）。不得把推断写成事实。
6. 与代码冲突时以工程文件为准，并列入 KNOWN_ISSUES；验收通过后 24 小时内提交上下文回写提案，用户审阅合入。

---

## 6. 统一交接包（全套件唯一定义）

交接包按任务存放在 `AI_Context/TASKS/GD-YYYY-NNNN/`，由七件套构成（RECON_REPORT 按需）：

| # | 文件 | 提供方 | 用途 |
| --- | --- | --- | --- |
| 1 | TASK_BRIEF.md | 用户 | 目标、背景、约束、预期结果（10 段固定结构） |
| 2 | CONTEXT_PACKET_vNN.md | 用户或取材员 | 固定前缀 + L2 选段 + L3 文件；版本号 + 核验 commit |
| 3 | RECON_REPORT.md（按需） | 取材员 | 只读调查：地图核验、接口事实、风险 |
| 4 | PLAN_vNN.md | Planner | 任务书草案：0.Metadata + 14 章；状态只能为 DRAFT / NEED_INVESTIGATION |
| 5 | APPROVAL_RECORD.md | 用户 | 批准版本、授权路径、条件与禁止项、批准人、批准时间 |
| 6 | EXECUTION_REPORT_Axx.md | Executor | Preflight、实际修改、步骤结果、命令、AC 映射、用量、偏离、回滚 |
| 7 | ACCEPTANCE.md | 用户 | 逐条验收结果与最终决定（ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT） |

交接顺序（七步）：①用户提交任务简报与最小上下文包 → ②上下文缺失或过期时先派发只读取材 → ③Planner 仅输出计划草案，不做任何修改 → ④用户审阅并在任务书标记 APPROVED、锁定版本 → ⑤用户将批准版任务书、批准记录与上下文包交给 Executor → ⑥Executor 先回报已读取的批准版本、文件范围与执行前检查，确认无冲突才开始写入 → ⑦完成后输出执行报告，交验证与验收。

防误操作约定：仅仅把任务书发给 Executor 不代表自动授权。未明确写出 `APPROVED`、批准版本、允许文件列表与执行边界时，Executor 保持只读并要求确认。

交接前必须运行校验器：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for executor
```

---

## 7. 执行尝试额度与停止条件

- 每任务执行尝试不超过三次：A01 首次实施，A02、A03 为两次有依据的范围内修复。每次输出错误原因、修改文件、修复依据与重测结果，并说明与上次的区别。
- 额度不是必须用满：发现架构假设错误、范围扩展、数据风险或连续无进展，立即停止并升级给 Planner。升级与重新规划不消耗额度。
- 升级诊断包必含：Task ID 与版本、尝试号、状态、环境、精确报错与首个有效堆栈、复现步骤、已改文件与 Diff 摘要、已做尝试、证据位置、剩余未知项、所需决策。

Executor 停止条件（任一出现立即停止并报告）：任务书未批准或版本不明确；工作区有无法安全隔离的用户修改；需要新增未批准文件、依赖或配置；工程事实与任务书关键假设冲突；连续两轮修复无可验证进展；既有功能回归或有数据损坏风险；需要访问密钥、外部账号、生产环境或未授权网络资源；继续操作可能扩大损失。

---

## 8. 技能索引（skills/）

| SKILL.md | 加载角色 | 触发时机 |
| --- | --- | --- |
| `skills/planner-orchestrator/SKILL.md` | Planner | 需求登记、任务分级、规划、交接编排、执行监督 |
| `skills/executor-engine/SKILL.md` | Executor | 已获批准任务书的工程实施、修复与报告 |
| `skills/task-brief-writer/SKILL.md` | Planner（撰写时加载） | 产出 L1/L2 工程任务书；START/END OF TASK 骨架 |
| `skills/unity2d-architect/SKILL.md` | 专业顾问 | Unity 2D 项目架构、选型、代码审查、性能方案 |
| `skills/software-architect/SKILL.md` | 专业顾问 | Python/通用软件架构、选型、代码审查 |
| `skills/game-systems-designer/SKILL.md` | 专业顾问 | 玩法系统设计、数值规格、状态机穷举 |
| `skills/engineering-verifier/SKILL.md` | 验证员 | VALIDATING 阶段：门禁执行、验收回执 |
| `skills/failure-retrospector/SKILL.md` | 复盘员 | 失败分类、升级诊断、变更控制、指标复盘 |

组合规则：同一会话内 Planner 主技能 + 专业顾问技能可叠加（架构类任务先加载顾问技能再规划）；Executor 与验证员必须由不同会话或不同模型实例担任，禁止自证（L0 快速通道除外：由用户直接检查 Diff 并签收验收，不设独立验证员）。

---

## 9. 六项必记指标与试点目标

| 指标 | 定义 | 试点目标 |
| --- | --- | --- |
| 任务书一次批准率 | 无重大修改即获批的占比 | ≥ 70% |
| Executor 首过率 | 首次执行即满足核心验收的占比（按复杂度分组） | ≥ 60% |
| 最终验收成功率 | 进入执行的任务最终通过占比（失败任务也记录） | ≥ 85% |
| 人工审核时间 | 审核计划与结果的总分钟数 | 只记录，防省 token 却加人工 |
| 每验收任务成本 | Planner + Executor + 工具费用 / 验收通过数 | 只记录，按季对照 |
| 越权文件修改次数 | 实际修改超出批准范围的次数 | 硬性目标 0 |

可选指标（有余力再记）：无证据声称测试通过次数（硬性 0）、修复轮数、修改路径符合度、缓存命中率。不单独追求首过率；任务书长度与 token 用量不作为质量指标。指标按周登记于各项目 `AI_Context/` 的指标文件，并用于模型路由表修订。

决策触发条件（复盘员监控）：每周喂上下文 > 2 小时，或一次批准率 < 70%，或月 L1+ 任务 ≥ 8 个 → 触发 failure-retrospector 技能并评估流程/订阅调整。

---

## 10. 宁停勿猜红线（全角色通用）

出现任一情形立即停止、报告、等待用户决定，不得自行推进：
1. 任何"这一改可能会静默破坏什么"的不确定情况。
2. 工作区不干净 / 分叉点或基线不符 / HEAD 与批准记录不符。
3. 需要修改批准范围之外的文件、依赖、配置或资产。
4. `.prefab` / `.unity` / `.asset` / `.meta` / `.xlsx` 冲突且无法确认资产两端存在性。
5. 编译、测试或门禁失败且修复超出授权范围或额度。
6. 用户未说"提交"就尝试 commit / push（默认由用户审查 Diff 后自行提交）。
7. 需要访问密钥、凭据、生产环境或未授权网络资源。
8. 不可逆操作（删除、迁移、覆盖、发布）无备份与回滚路径。

---

## 11. 套件目录与校验器

```text
agent-workflow-kit/
  AGENTS.md            本文件（机读总纲）
  README.md            人读导览（安装、快速开始、维护）
  docs/
    USAGE.md           使用指南（目录划分、技能手册、校验器手册、完整流程）
  scripts/
    validate_handover.py   交接包校验器（唯一实现，模板内为同步副本）
  tests/
    test_validate_handover.py   校验器标准库回归测试（python -m unittest discover -s tests）
  skills/
    planner-orchestrator/ executor-engine/ task-brief-writer/
    unity2d-architect/ software-architect/ game-systems-designer/
    engineering-verifier/ failure-retrospector/
  templates/
    software-py/       Python 通用软件项目模板（uv + ruff + mypy + pytest）
    unity2d/           Unity 2D 游戏开发项目模板（asmdef 分层）
```

校验器用法：

```bash
# Planner 交接前（草案齐全性）
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
# Executor 执行前（批准完整性：APPROVED + 批准记录）
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor
# 验收归档前（执行报告 + 验收决定齐全）
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

退出码 0 = 通过；1 = 存在 FAIL。`--json` 输出机器可读结果。校验器只做结构校验，不替代编译、测试与人工审查。
