# AGENTS.md — Agent Workflow Kit v3.1 总纲（机读版）

> 本文件是全套件唯一工作流宪法。设计意图与边界以 `docs/DESIGN_CHARTER.md` 为准；本文件负责可执行规则、角色、状态、模型路由和门禁。

## 0. 不可覆盖的最高规则

1. CEO（用户）拥有需求优先级、架构取舍、批准、范围变更和最终验收权。
2. Planner 只能提出方案；Secretary 不能批准；Worker 不能自证；Watchdog 不能代 CEO 签收。
3. 工程写入必须具备批准版本、Task ID、Write Boundaries、Forbidden、Base Commit 和 APPROVAL_RECORD。
4. 编译器、测试工具、审计工具和真实运行输出才是验证证据；未运行不得声称通过。
5. 任一角色发现范围、资产、数据、凭据、网络或历史不可逆风险时，立即停止并要求 CEO 决策。
6. Git 默认只读；commit、merge、push、tag、reset 等动作必须有 CEO 明确授权。禁止默认联网上传。

## 1. CEO 与四角色正交体系

```text
CEO ──高频运营── Secretary ──FEED_DROP── Planner
 │                                  │
 ├─高频技术─────────────────────────┘
 │
 ├─低频下基层── Worker（批准施工 / L0 直派）
 └─低频异常──── Watchdog（独立门禁 / 软故障复盘）
```

| 角色 | 核心使命 | 默认形态 | 写入边界 | 绝对禁止 |
| --- | --- | --- | --- | --- |
| Secretary | 项目秘书、Router、备菜员 | Agent 模式 | PROJECT_BOARD、任务辅助包、Manifest | 不写业务代码/配置/资产，不做架构决策，不批准 |
| Planner | 技术架构与质量主入口 | Chat 或 Agent | 仅 PLAN 草案 | 不实施，不批准自己，不把推断写事实 |
| Worker | 单一任务施工员 | Agent 模式 | 批准 Write Boundaries 内的文件与 CLI/测试命令 | 不越 Forbidden、不做备菜/台账、不默认 GUI/Computer-Use/commit/push |
| Watchdog | 独立门禁与流程免疫系统 | 独立会话/实例 | ACCEPTANCE 事实部分与复盘提案 | 只判不修，不替 CEO 验收 |

高频直连：CEO 与 Secretary 谈进度、成本、台账和备菜；CEO 与 Planner 谈架构、技术栈、质量和拆解。

低频下基层：L0 小修由 CEO 直接派 Worker；出现连续失败、软故障、异常停机或复盘触发时直连 Worker / Watchdog。

## 2. 唯一状态机

```text
[标准 L1/L2]
INTAKE
  -> STAGING
  -> PLANNING
  -> HUMAN_APPROVAL
  -> EXECUTING
  -> WATCHDOG_VERIFY
  -> CEO_ACCEPTANCE
  -> ARCHIVED

Chat 材料不足或仓库外/敏感/冻结快照异常:
PLANNING -> STAGING(NEED_FILES) -> PLANNING

[L0 CEO 下基层]
INTAKE -> EXECUTING -> CEO_ACCEPTANCE -> ARCHIVED
```

规则：

- 标准任务不得跳过 STAGING、HUMAN_APPROVAL 或独立 Watchdog。
- L0 支持 CEO 三行 mini 简报直派，但仍需 Workflow Version、Base Commit、AC 类别、Diff 检查、机器证据和 CEO 签收。
- 范围、接口、依赖、配置、风险或 AC 实质变化必须升版 `vNN+1` 重审。
- 新 Manifest、PLAN、APPROVAL_RECORD、执行报告、ACCEPTANCE 与 L0 mini 必须声明 `Workflow Version: v3.1`。
- 所有状态必须可从磁盘凭证或 CEO 明确记录恢复，不依赖一次性对话记忆。

## 3. 任务与风险分级

| 级别 | 定义 | 典型工作流 |
| --- | --- | --- |
| L0 | 局部、模式成熟、低耦合、可快速回退 | CEO 直派 Worker；必要时 Watchdog 快检 |
| L1 | 跨文件、设计选择、多步骤依赖 | Secretary → Planner → CEO 批准 → Worker → Watchdog |
| L2 | 生命周期、渲染数学、性能、序列化、大范围 | xhigh 深度规划；分阶段；专项验证 |
| L3 | 不可逆或高风险发布、批量删改资产、外发凭据 | Agent 不自主执行，CEO 手动或专项批准 |

| Risk | 含义 | 要求 |
| --- | --- | --- |
| R0 | 局部、可逆、无公共接口 | 常规记录 |
| R1 | 多文件、有限回归 | 写入边界、测试、回滚 |
| R2 | 底层生命周期/序列化/公共 API/性能 | 基线、专项测试、分阶段 |
| R3 | 不可逆、敏感外发、生产发布 | CEO 逐项批准，不由 Agent 自主执行 |

六问任意两项为“是”默认 L1：架构选择、跨模块、生命周期/异步/资源/序列化、图形数学/渲染/GPU、性能、范围广泛回归、需求含糊需要推导。

## 4. 模型路由配置表（唯一厂商绑定点）

> 复核日期：2026-11-15。价格仅用于预算估算；模型名称、价格或可用性变化时只更新本表。

| 路由项 | 推荐 | 价格参数（每 1M tokens） | 约束 |
| --- | --- | --- | --- |
| Secretary | DeepSeek V4.1 Flash / 同类轻量 Agent | 高峰 $0.30 / $1.20；错峰半价；缓存命中输入 $0.006 | 低延迟、低成本；只做索引、备菜和台账 |
| Planner 日常 L1 | Gemini 4 Hydrogen | 输入 $1.50 / 输出 $7.50；缓存命中输入 $0.075 | 默认 high；保留完整分析权 |
| Planner 深度 L2 | Gemini 4 Hydrogen xhigh | 同 Hydrogen；思考 token 计入输出 | 架构、渲染、生命周期、迁移 |
| L2 可选二审 | Gemini 4 Carbon | 11-30 前 $2.00 / $10.00；12-01 起 $4.00 / $20.00 | 只出 REVIEW_NOTE，不替代 Planner |
| Worker | DeepSeek V4.1 Flash | 高峰 $0.30 / $1.20；错峰半价；缓存命中 $0.006 | Agent + 完整本地工具；长任务走错峰 |
| Watchdog | Gemini 4 Carbon 或 DeepSeek V4.1 Flash | 按对应参数 | L1/L2 必须独立会话/实例，禁止 Worker 自证 |
| L0 | 由 CEO 直接选择 Worker | 按 Worker | 不调用 Planner，除非 CEO 要求 |

思考档位：

- Secretary：low / medium。
- Planner L1：high；L2：xhigh。
- Worker：由批准 PLAN 指定，不建议自行升降。
- Watchdog：medium / high，按风险决定。

错峰时段（北京时间）：工作日 12:00–14:00、18:00–次日 09:00、周末和法定节假日。

## 5. FEED_DROP 与上下文工程

每个任务使用：

```text
AI_Context/TASKS/GD-YYYY-NNNN/
  00_CONTEXT_MANIFEST.md
  FEED_DROP/              # Git 忽略
  NEED_FILES/ROUND_NN/    # Git 忽略，append-only 增量补料
  TASK_BRIEF.md
  PLAN_vNN.md
  APPROVAL_RECORD.md
  EXECUTION_REPORT_Axx.md
  ACCEPTANCE.md
  RECON_REPORT.md         # 按需
  CONTEXT_UPDATE_PROPOSAL.md
```

`stage_context.py` 自动装入：

- `L1__PROJECT_OVERVIEW.md`
- `L1__CODING_STANDARDS.md`
- `L1__BUILD_AND_TEST.md`
- `L2__PROJECT_BOARD.md`（存在时）
- `L2__ARCHITECTURE.md`
- `L2__MODULE_MAP.md`
- `L2__DEPENDENCIES.md`（存在时）
- `L3__<原路径扁平化>` 真实源文件
- `L3__git_recent_context.txt`

规则：

1. Chat 和 Agent 共用同一物理投喂入口；Agent 仍可只读检索全仓。
2. `--chat-safe` 默认把冷门扩展名转换为 `.ext.txt` 安全名，不复制两份。
3. 敏感文件、仓库外路径、`..` 和路径穿越必须拒绝。
4. L1 建议 4,096–8,000 Token；L2 ≤ 30,000；L3 ≤ 100,000；常规 Total ≤ 150,000。
5. Total 超预算时必须拆分或减少 L3，不允许把全仓作为默认上下文。
6. 上下文与代码冲突时以代码、测试和真实运行为准，相关文档标 `STALE`。
7. 可信度标记只有：VERIFIED / OBSERVED / INFERRED / UNKNOWN / STALE。
8. `--append` 已重定义为创建下一个 `NEED_FILES/ROUND_NN/`，不修改基线；每轮必须提供 `--reason`，记录来源、SHA-256、Token 与 Git HEAD。
9. Agent Planner 默认直接只读检索仓库；普通源码/测试/配置缺口不得转成人工 NEED_FILES。

## 6. PROJECT_BOARD 与 Secretary

`AI_Context/PROJECT_BOARD.md` 是唯一全局台账，包含：

- Attention Queue：只列需要 CEO 拍板、手工操作、异常排查或签收的阻断。
- Ticket Index：Task ID、级别、状态、分支、当前 PLAN、变更模块摘要、一句话结论。

Secretary 接单时最多向 CEO 问 **1 个**具体问题。只有 Chat Planner 缺仓库或出现仓库外/敏感/冻结快照异常时，才用 `stage_context.py --append --reason ... --files ...` 创建下一轮；Agent Planner 自行只读检索。验收后只依据实际 diff 起草回写提案，不直接改长期上下文正文。

## 7. 统一交接包

| 文件 | 提供者 | 作用 |
| --- | --- | --- |
| TASK_BRIEF.md | CEO / Secretary | 目标、背景、约束、预期 |
| 00_CONTEXT_MANIFEST.md | stage_context.py | Base Commit、Token、映射、排除、目录摘要 |
| FEED_DROP/ | Secretary | 真实源文件物理投喂箱 |
| NEED_FILES/ROUND_NN/ | Secretary | Chat/异常分轮增量补料；不覆盖基线 |
| RECON_REPORT.md | 只读取材 | 按需调查事实 |
| PLAN_vNN.md | Planner | 0.Metadata + 14 章草案 |
| APPROVAL_RECORD.md | CEO | 批准版本、范围、条件、时间 |
| EXECUTION_REPORT_Axx.md | Worker | Preflight、修改、命令、AC、偏离、回滚 |
| ACCEPTANCE.md | Watchdog + CEO | 事实表、建议与最终决定 |

标准顺序：

1. Secretary 登记并 stage。
2. Planner 消费 FEED_DROP，输出 DRAFT/NEED_INVESTIGATION。
3. CEO 审阅并锁定版本。
4. Worker 先回报批准版本、范围与 Preflight。
5. Worker 在隔离分支施工和取证。
6. Watchdog 独立实跑门禁。
7. CEO 最终签收，Secretary 更新台账并起草回写。

## 8. Worker 尝试额度与停止条件

每个任务最多 A01–A03：

- A01 首次实施。
- A02、A03 是有证据的范围内修复。
- 每次必须记录首错、修改、依据、与上次差异和重测。
- 升级给 Planner 不计尝试额度。

立即停止：

- 未批准、版本冲突、Write Boundaries/Forbidden 不清。
- 工作区有无法隔离的用户修改。
- 需要边界外或 Forbidden 文件、依赖、配置、资产、网络或未授权 Computer-Use。
- 任务书关键假设与工程事实冲突。
- 连续两轮无验证进展。
- 存在回归、数据损坏、凭据暴露或不可逆风险。

## 9. 验证与 Watchdog

L1/L2 必须由独立 Watchdog 会话/实例验证，禁止 Worker 自证。L0 默认免独立会话，由 CEO 检查 Diff 并签收。

V0–V5：

| 层 | 内容 |
| --- | --- |
| V0 | 方案、接口、数据流、边界、Non-goals |
| V1 | 静态检查、lint、类型 |
| V2 | 编译 / 构建 |
| V3 | 单元、集成、回归测试 |
| V4 | 运行时、编辑器、视觉验证 |
| V5 | 性能、平台、内存、专项 |

最低层：L1 ≥ V3；L2 ≥ V4，R2+ 按任务加 V5。降层必须有 CEO 明确批准。

### 证据与 Computer-Use

- 默认证据：命令、退出码、终端日志、Diff、测试结果、Manifest、SHA-256 和可读取运行输出。
- `WORKER_AUTOMATABLE` 禁止以截图、视频或纯观察作为主证据。
- `UNITY_GUI_REQUIRED` 默认由 CEO 执行；Worker 只有在 PLAN 与 APPROVAL_RECORD 同时列明目标、动作和范围时才可使用 Computer-Use。
- 授权格式固定为 `AUTHORIZED: TARGET=...; ACTIONS=...; SCOPE=...` 三段齐全；否则视为未授权。
- `CEO_MANUAL_ACCEPTANCE` 不得由 Worker 或 Watchdog 自证；最终决定仍属于 CEO。
- 截图只用于无法稳定文本断言的视觉结果，并记录 Visual Purpose / Visual Scenario / Visual Expected。

Watchdog 硬目标：

- 越权文件修改 = 0。
- 无证据声称通过 = 0。
- 实际修改 100% 命中批准 Write Boundaries 且未命中 Forbidden。
- 批准边界内未计划改动全部经 Watchdog 显式审阅；UNJUSTIFIED = 0。
- 既有断言不得删除、跳过或弱化。

## 10. 技能索引

| 技能 | 角色 | 触发 |
| --- | --- | --- |
| `secretary-router` | Secretary | 登记、看板、基线 staging、Chat NEED_FILES、回写 |
| `planner-orchestrator` | Planner | 分析、分级、任务书、监督重规划 |
| `worker-engine` | Worker | 批准边界内施工、修复、执行报告 |
| `watchdog-inspector` | Watchdog | 门禁、验收事实、软故障复盘 |
| `task-brief-writer` | Planner 插件 | 14 章任务书与 L0 mini |
| `unity2d-architect` | Planner 只读顾问 | Unity 2D 架构、生命周期、性能 |
| `software-architect` | Planner 只读顾问 | Python / 通用软件架构 |
| `game-systems-designer` | Planner 只读顾问 | 玩法、状态、数值与规格 |

组合规则：Planner 可按项目叠加只读顾问；Worker 施工期只加载 `worker-engine`；Watchdog 必须独立；Secretary 不加载执行或顾问技能。

## 11. 六项必记指标

1. 越权文件修改次数：硬目标 0。
2. 无证据声称通过次数：硬目标 0。
3. 任务书一次批准率：目标 ≥ 70%。
4. Worker 首过率：目标 ≥ 60%，按 L0/L1/L2 分组。
5. 最终验收成功率：目标 ≥ 85%，失败任务计入分母。
6. CEO 每周干预耗时与每验收任务成本：只记录，重点检查是否高于“Secretary 应替你完成”的搬运工作。

任一触发：一次批准率 < 70%、越权 ≥ 1、CEO 每周上下文投入 > 2 小时，或月 L1+ 任务 ≥ 8 个，Watchdog 应提交流程修正提案。

## 12. 宁停勿猜红线

1. 任何可能静默破坏行为、资产或数据的情况。
2. 工作区不干净、HEAD / 分支与批准记录不符。
3. 需要修改 Write Boundaries 外文件、命中 Forbidden、依赖、配置或资产。
4. `.prefab / .unity / .asset / .meta / .xlsx` 冲突且无法确认两端状态。
5. 编译、测试或门禁失败，修复超出范围或额度。
6. 未经 CEO 明确授权就 commit、merge、push 或改 remote。
7. 需要密钥、凭据、生产环境或未授权网络。
8. 删除、迁移、覆盖或发布没有备份与回滚路径。

## 13. 目录与脚本

```text
agent-workflow-kit/
  AGENTS.md
  README.md
  docs/
    DESIGN_CHARTER.md
    USAGE.md
    MIGRATION_v3.0_to_v3.1.md
  scripts/
    stage_context.py
    validate_handover.py
  tests/
  skills/                 # 8 个正交技能
  templates/
    software-py/
    unity2d/
```

### stage_context.py

```bash
python scripts/stage_context.py <task_dir> [--files p1 p2 ...] [--from-list file] \
  [--no-chat-safe] [--git-diff N] [--budget-limit 150000] [--json]
python scripts/stage_context.py <task_dir> --append --reason "<本轮未知项>" \
  --files p1 p2 ... [--from-list file] [--json]
```

### validate_handover.py

```bash
python scripts/validate_handover.py <task_dir> --for planner
python scripts/validate_handover.py <task_dir> --for worker
python scripts/validate_handover.py <task_dir> --for watchdog
python scripts/validate_handover.py <task_dir> --for archive
python scripts/validate_handover.py <task_dir> --l0 --for archive
```

v3.1 只接受 `planner|worker|watchdog|archive`；旧模式值会失败并提示新枚举。`--json` 输出机器可读结果，`--list` 列出必查件。watchdog/archive 自动审计批准 Base Commit 到工作区的 Git Diff；非 Git 任务显式 WARN，不能声称范围已机器验证。结构校验不能替代编译、测试与 CEO 验收。
