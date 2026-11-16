# `agent-workflow-kit` 设计总纲（v3.0）
> **副标题**：面向游戏与软件工程的“CEO + Super-Agent”四角色正交协作系统 · 需求分析与架构指导书  
> **定位**：`agent-workflow-kit` 迭代重构的最高产品需求文档（PRD）与架构宪法  
> **适用域**：Unity / Unreal / Shader / DCC 工具 / Python 通用工程  
> **基线基础**：继承 v2.0 工程安全红线、证据分级与成本护栏；引入 Super-Agent 调度、旁路监督与物理文件投喂体系  

---

## 1. 演进背景与核心问题定义（Why）

### 1.1 历史痛点复盘：为什么必须破坏重构
经过 v1.0（口号化规则）与 v2.0（分层文本 + 三路线并存）的演进，我们识别出阻碍日常持续运转的三个根本矛盾：
1. **人类成为了“肉身路由器”与“上下文搬运工”**：在原有的多窗口协作中，虽然保护了代码安全，但需要用户亲自跟踪多任务进度、手工把源码片段拼贴成 Markdown、在 Planner/Executor/Verifier 之间人肉传话、并在验收后手工更新文档。只要工程规模增长，**人工协调耗时**就会迅速突破每周 2 小时阈值，倒逼开发者退回“全量投喂”或直接放弃规范。
2. **大脑形态与路线被人为割裂（A/B/C 路线痛点）**：过去因“Chat 模式看不见仓库”而分化出“纯 Chat 手工路线”与“必须付费订阅 Agent IDE 的路线”。这种分裂导致工作流协议臃肿，无法做到**根据预算和任务自由切换大脑形态**。
3. **文本拼贴上下文脱离真实开发习惯**：把 `.cs`、`.py` 代码塞进巨型 `.md` 文档既不便于人工拖拽喂给网页端大脑，也容易丢失原始文件结构与语法直觉；而如果由执行代码的人去兼职搜集上下文，又会混淆“备菜”与“施工”的权责边界。

### 1.2 破旧立新：本总纲明确废除的设计
1. **彻底废除 A / B / C 多路线分叉**：全套件**只保留唯一一套通用工作流**。无论是免费的网页 Chat 大脑，还是高配的本地/云端 Agent 大脑，都接入同一个标准投喂接口，底层运行完全兼容。
2. **彻底废除“手工拼贴代码进 Markdown 上下文包”**：不再由人手抄代码段进 `CONTEXT_PACKET.md`，改由工具脚本直接提取并拷贝**真实源文件**到投喂箱。
3. **彻底废除“人肉跟踪进度与手写文档回写”**：进度台账、候选上下文打包、验收后的文档更新提案，全部下沉给新增的轻量常驻中间层（`Secretary`）自动完成。
4. **彻底废除技能之间的职责混杂**：清除专业顾问技能里的“全栈执行”残留指令，统一施工者命名为 `Worker`，合并监督与复盘职责为独立外环 `Watchdog`。

### 1.3 第一性设计目标（5 项核心原则）
1. **极致节省人类（CEO）注意力**：这是 DeepSeek Super-agent 的灵魂原则——系统平时保持安静，只在需要拍板（审批、手工装配、最终验收）时向你提交聚焦的决策请求；提问一次只问一个具体问题。
2. **大脑形态自由解耦**：免费 Chat 大脑（如 AI Studio 拖拽投喂）与 Agent 大脑（直读仓库）共用同一套物理投喂入口，随时无痛切换，不绑死付费订阅。
3. **权责绝对正交，防越权防自证**：管家只管进度与备菜、大脑只管技术架构、工人只在隔离分支按单施工、监察员只在旁路独立裁判，四者能力边界与工具权限物理隔离。
4. **进度存磁盘，不靠对话记忆**：所有项目状态、任务索引、历史链路（Chain of Recall）持久化在仓库台账中，任何一次性新开的 Chat 大脑都能 10 秒接上当前工程进度。
5. **游戏与复杂工程零妥协安全底线**：延续 v2.0 最硬核的工程保护——证据优先（`VERIFIED/INFERRED/UNKNOWN`）、资产边界（`User Manual Checklist`）、`A01–A03` 尝试熔断、不覆盖未提交修改。

---

## 2. 组织隐喻与四角色正交体系（Who）

本套件借鉴 DeepSeek Super-agent 的 **Router–Worker–Watchdog** 三元正交架构，结合研发流程中“先谋后动”的架构必要性，构建 **“1 位 CEO（用户） + 4 个正交 AI 职能”** 的协作模型。

### 2.1 CEO 交互拓扑（主入口 vs. 下基层）

```text
                        ┌──────────────────────┐
                        │     用户（CEO）       │
                        │ 最终需求 / 拍板 / 验收 │
                        └──┬────────────────┬──┘
           [高频直连·运营线] │                │ [高频直连·技术线]
       进度、排期、成本、上下文 │                │ 架构、技术栈、工程质量、拆解方案
                           ▼                ▼
               ┌───────────────┐        ┌───────────────┐
               │   Secretary   │───────▶│    Planner    │
               │ (Router/秘书) │FEED_DROP│  (Brain/大脑)  │
               │   Agent 模式  │        │ Chat/Agent皆可 │
               └───────┬───────┘        └───────┬───────┘
                       │     ▲                  │
       [L0/异常下基层]   │     │ 进度/状态汇总      │ 经 CEO 批准的 PLAN
          (低频直连)    │     │                  ▼
            ┌──────────┼─────┴──────────┬───────────────┐
            │          ▼                ▼               │
            │  ┌───────────────┐  ┌───────────────┐     │
            └─▶│    Worker     │◀─│   Watchdog    │◀────┘
               │ (原Executor)  │  │ (独立监察员)   │  [低频下基层：现场排障/复盘]
               │ 隔离分支施工员 │  │ 质检+软故障巡检 │
               └───────────────┘  └───────────────┘
```

**交互频次与职责分层说明：**
* **高频主对接人（日常工作 90% 交互对象）**：
  * **与 `Secretary（项目秘书）` 沟通非技术/运营管理**：提新想法、问“现在做到哪一步了”、看本周花了多少钱/多少时间、接收“待你拍板”清单、让它帮你把某任务的材料备好、验收后让它去刷新项目文档。
  * **与 `Planner（大脑/首席架构师）` 沟通技术/质量把控**：探讨系统怎么分层、Unity/Python 技术栈选型、RenderPipeline/GC/并发难点取舍、审核任务书里的设计合理性。
* **低频直连对象（“CEO 下基层”模式）**：
  * **与 `Worker（施工员）` 与 `Watchdog（监察员）`**：在标准的 L1/L2 开发流中，它们对 CEO 基本“静默运行”（Worker 在隔离分支施工，Watchdog 在旁路验证并把结果交给 Secretary 汇总）。**仅在以下两种情况，CEO 直接下基层对话**：
    1. **快速反应小任务（L0 Fast Track）**：改个小 Bug、调个局部参数，CEO 直接派 `Worker` 改完看 Diff，必要时让 `Watchdog` 快检一次，不惊动 `Planner`；
    2. **一线应急排障与复盘**：遇到连续报错阻塞或 Watchdog 报警时，CEO 直接介入一线现场核对诊断包与根因。

### 2.2 四角色权责与能力边界矩阵

| 角色                                  | 定位与核心使命                                          | 运行形态与模型策略                                           | 工具与写入权限                                               | 绝对禁止（红线）                                             |
| :------------------------------------ | :------------------------------------------------------ | :----------------------------------------------------------- | :----------------------------------------------------------- | :----------------------------------------------------------- |
| **Secretary**<br>（项目秘书）         | 全局调度台、工程进度管家、上下文“备菜员”                | **Agent 模式**（读仓+调打包脚本）<br>轻量快模型（低延迟、低成本） | 只读全仓 + 运行 `stage_context.py`；仅可写 `PROJECT_BOARD.md`、台账与 `TASKS/` 下的辅助包 | **严禁写业务代码/改配置资产**；<br>**严禁越权替代大脑做架构决策**（只提供“候选上下文”，完整分析权属于 Planner）；<br>每次最多向 CEO 提 1 个具体问题 |
| **Planner**<br>（架构大脑）           | 首席软件/游戏架构师，掌握**完整项目分析权**与方案拆解权 | **形态自由（Chat 拖拽 或 Agent 直读）**<br>强推理旗舰（L1 `high` / L2 `xhigh`），可叠加专业顾问技能 | Chat 模式：读投喂文件；Agent 模式：读 `FEED_DROP/` + 全仓只读检索。仅产出 `PLAN_vNN.md`（草案） | 不修改任何业务文件；不批准自己的计划；不把推断写成事实       |
| **Worker**<br>（施工员，原 Executor） | 专注单一任务的隔离工程实施者                            | **Agent 模式 + 完整本地工具链**<br>高性价比强编码模型（长任务走错峰半价） | 在独立 Git 分支（`ai/GD-YYYY-NNNN`）内读写 `APPROVED` 白名单文件、跑编译与测试命令 | **不再兼职备菜/摸底/维护全局台账**；不直接响应未批准的口头加需求；不触碰 `FORBIDDEN` 与用户未提交修改 |
| **Watchdog**<br>（独立监察员）        | 主链路之外的**客观裁判 + 软故障免疫系统**               | **独立会话 / 独立模型实例**<br>稳定中/强模型（L0 免开独立会话，L1/L2 必开） | 只读代码与 `git diff` + 实跑门禁命令 + 写 `ACCEPTANCE.md` 事实部分与复盘提案 | **只判不修，绝不亲自改代码凑通过**；禁止 Worker 自证；不替 CEO 签最终 `ACCEPT` |

---

## 3. 核心系统需求分析（What：Kit 必须提供的六大能力）

### 3.1 物理源文件投喂箱机制（`FEED_DROP/` + `stage_context.py`）
彻底用“真实源文件拷贝”取代“在 Markdown 里粘贴代码”，实现一份准备、通吃 Chat 与 Agent 两种大脑：

1. **目录结构与层级扁平化命名（已拍板方案 A）**：
   每个任务目录下生成独立的暂存区 `AI_Context/TASKS/GD-YYYY-NNNN/FEED_DROP/`，并由确定性脚本 `scripts/stage_context.py` 清空重建：
   * `L1__PROJECT_OVERVIEW.md`、`L1__CODING_STANDARDS.md`、`L1__BUILD_AND_TEST.md`（固定前缀，字典序最前，保障长稳内容持续命中 4,096 tokens 隐式缓存）；
   * `L2__ARCHITECTURE.md`、`L2__MODULE_MAP.md`（模块导航与依赖约束）；
   * `L3__<斜杠转下划线的原路径>`（例如 `L3__Assets_Scripts_Core_GameClock.cs` 或 `L3__src_app_domain_models.py`）；
   * `L3__git_recent_context.txt`（近期 `git log` / 关键 Diff 摘要，解决 Chat 对项目最新进展无感知问题）。
2. **双形态大脑无缝消费**：
   * **Chat 模式大脑**：CEO 打开 `FEED_DROP/`，`Ctrl+A` 一键全选拖入网页对话框即可；扁平命名解决了浏览器拒收多层嵌套文件夹的问题，文件名自带原路径层级解决了上下文坐标丢失问题。同时脚本提供 `--chat-safe` 选项，对 `.asmdef`/`.shader` 等冷门后缀自动附带 `.txt` 镜像，避免网页端上传拦截。
   * **Agent 模式大脑**：直接从 `FEED_DROP/` 与 `00_CONTEXT_MANIFEST.md` 起步（省去自己大海捞针的 Token 消耗），同时仍保留对全仓库的只读自查权。
3. **配套内联索引（`00_CONTEXT_MANIFEST.md`）**：
   借鉴 Super-agent 的 **Inline & Spill** 思想：记录当前仓库 `Base Commit`（或无 Git 恢复时间）、文件映射表（暂存名 ↔ 原路径）、选中理由、估算 Token 总量（超过 150K 触发拆分警告）、全仓目录树概览以及“明确未放入的大目录清单”。
4. **大脑的反向补料权（保障完整分析权）**：
   由于 Secretary 只做快速初筛，若 Planner 审阅后认为缺少某个依赖文件，Chat 模式下直接输出点名清单（`NEED_FILES`）交由 Secretary 用 `stage_context.py --append` 一键补齐；Agent 模式下大脑自行读仓补全。
5. **零污染工程隔离（硬性要求）**：
   * `.gitignore` 必须强制忽略 `AI_Context/TASKS/**/FEED_DROP/`，确保暂存文件绝不入库、不污染 `git status`；
   * `templates/software-py/pyproject.toml` 中的 `ruff`、`mypy`、`pytest` 必须显式配置排除 `AI_Context/`，防止工具链扫描暂存箱里的 `.py` 副本引发误报；
   * Unity 模板因 `AI_Context/` 位于 `Assets/` 外，天然不触发 Unity 编译。

### 3.2 全局进度与 CEO 注意力总台（`PROJECT_BOARD.md`）
由 Secretary 独家维护的仓库级唯一状态板，借鉴 Super-agent 的 **Web Panel（待人工处理面板）** 与 **Chain of Recall（链式召回）**：
* **【第一区：待 CEO 拍板队列（Attention Queue）】**：永远置顶，只展示当前阻断需要人介入的事项（如：`待批准计划 PLAN_v01`、`待在 Unity 手工挂载 Prefab`、`待签收验收`、`Watchdog 异常停机告警`），配合**一句话决策提示**，平时不制造噪音。
* **【第二区：全局任务台账与召回索引（Ticket Index）】**：记录每个任务的 `Task ID | 级别 | 状态 | 分支 | 当前 PLAN 版本 | 变更模块摘要 | 一句话结论`。当 CEO 提到“上周那个顿帧任务”时，Secretary 可沿索引直达对应任务目录召回，不必重翻海量聊天记录。

### 3.3 唯一通用状态机与 L0 快车道
全套件只维护一套主干状态机与一条合法快车道：

```text
[通用 L1/L2 主干]
INTAKE (Secretary 接单/最多问1题)
  -> STAGING (Secretary 快筛 + stage_context.py 生成 FEED_DROP)
  -> PLANNING (Planner 消费 FEED_DROP 输出 PLAN_vNN [DRAFT])
       └─ 材料缺口时: -> STAGING (点名补拷) -> PLANNING
  -> HUMAN_APPROVAL (CEO 审阅拍板 -> APPROVED + APPROVAL_RECORD)
  -> EXECUTING (Worker 独立分支施工, A01-A03 熔断)
  -> WATCHDOG_VERIFY (Watchdog 独立会话实跑门禁 + 软故障检查 -> ACCEPTANCE 事实)
  -> ARCHIVED (CEO 签收 ACCEPT -> Secretary 对照 diff 自动起草回写并刷新台账)

[L0 CEO 下基层快速通道]
INTAKE (L0/R0 局部小修) -> EXECUTING (CEO 直连 Worker + 3 行简报) -> ACCEPTED (CEO 看 Diff 签收) -> ARCHIVED
```

### 3.4 统一监督与自愈回路（`Watchdog` = Verifier + Retrospector）
合并后的 `watchdog-inspector` 承担两项相互呼应的独立职责，严格做到“不写业务代码、不让工人自证”：
1. **客观门禁裁判（任务级）**：在 L1/L2 任务进入验收前，由独立会话实跑 V0–V5 门禁命令，逐路径比对 `git diff` 与 `APPROVAL_RECORD` 范围（越权 = 0），严防“假通过（删断言/吞异常/未运行写 PASS）”。
2. **软故障巡检与流程自愈（系统级）**：
   * 识别 Worker 软故障：连续 2 轮无有效进展、偏离 `Non-goals`、反复试错修改同一边界外文件；
   * 识别文档漂移：检测 `MODULE_MAP` / `ARCHITECTURE` 是否与近期提交出现 `STALE` 冲突；
   * 识别成本与心力警报：监控六项指标触发线（一次批准率 `< 70%`、越权 `≥ 1`、每周 CEO 操心上下文 `> 2 小时`），及时拉响流程修正提案。

### 3.5 结构化交接与硬门禁校验（`validate_handover.py`）
校验器必须完全适配新体系并杜绝误判：
* 适配 `FEED_DROP/` + `00_CONTEXT_MANIFEST.md` 的存在性与非空校验；
* 默认匹配多版本文件（`PLAN_vNN` / `EXECUTION_REPORT_A0x`）中的**最新版本**，并校验 `APPROVAL_RECORD` 锁定版本号与最新任务书严格一致；
* 使用整行枚举精确匹配，彻底拦截未填写的模板占位符（如 `PASS / FAIL`、`ACCEPT / REJECT`、`<待填>`）；
* 兼容无 Git 项目时间戳格式与空格/下划线混合的 `APPROVED WITH CONDITIONS`；
* 原生支持 `--l0` 模式校验快速通道任务的归档完整性。

### 3.6 工程底座安全与双栈模版硬化
* **`templates/unity2d`**：继续坚守“AI 不碰 `.prefab / .unity / .asset / .meta`”，统一 `User Manual Checklist` 衔接；将 `ProjectAuditWindow` 改造为支持无头批处理返回真实退出码（`RunBatchAudit`）的真门禁；修正 `TASK_BRIEF` 模板残留。
* **`templates/software-py`**：保持 `domain -> application(Protocol) <- infra <- interfaces` 四层洁净架构，在 `pyproject.toml` 中锁死工具链门禁并隔离 `AI_Context/` 目录。

---

## 4. 套件目录与技能重组规范（Architecture of the Kit）

### 4.1 套件目标目录树

```text
agent-workflow-kit/
├── AGENTS.md                        # 全套件宪法（唯一模型路由表、四角色矩阵、状态机与红线）
├── README.md                        # 极速导览
├── docs/
│   ├── DESIGN_CHARTER.md            # 【本文件】v3.0 设计总纲与需求分析案
│   └── USAGE.md                     # 操作手册（Secretary/CEO/Brain/Worker/Watchdog 实操走读）
├── scripts/
│   ├── stage_context.py             # 【新增】物理源文件投喂箱打包脚本（L1__/L2__/L3__ + 清单 + 估算）
│   └── validate_handover.py         # 【升级】交接包门禁校验器（适配 FEED_DROP、最新版本、防假阳、--l0）
├── tests/
│   └── test_validate_and_stage.py   # 【新增】基于标准库 unittest 的双脚本回归测试集
├── skills/                          # 8 个权责零重叠的技能（4 核心 + 1 写作插件 + 3 只读顾问）
│   ├── secretary-router/SKILL.md    # 【新增】项目秘书（Router）
│   ├── planner-orchestrator/SKILL.md# 架构大脑（保留单贴自足性）
│   ├── worker-engine/SKILL.md       # 【重构改名】隔离施工员（原 executor-engine，剥离备菜与台账职责）
│   ├── watchdog-inspector/SKILL.md  # 【合并】独立监督员（合并原 verifier + retrospector）
│   ├── task-brief-writer/SKILL.md   # 任务书 14 章骨架撰写插件
│   ├── unity2d-architect/SKILL.md   # 纯规划期只读顾问（去执行化，对齐 GAMEDEV.EditorTools）
│   ├── software-architect/SKILL.md  # 纯规划期只读顾问（去执行化）
│   └── game-systems-designer/SKILL.md# 纯规划期只读顾问（去执行化）
└── templates/
    ├── software-py/                 # 内置 PROJECT_BOARD.md、FEED_DROP 屏蔽规则、双脚本同步副本
    └── unity2d/                     # 内置 PROJECT_BOARD.md、RunBatchAudit 门禁、双脚本同步副本
```

### 4.2 技能“去冲突与去重”设计准则
1. **核心技能保自足，顾问技能去执行**：
   * `secretary-router`、`planner-orchestrator`、`worker-engine`、`watchdog-inspector` 保留各自完整的关键纪律与自检清单，确保用户在任何网页 Chat 窗口单贴一份正文也能闭环工作；
   * 三个专业顾问技能（`unity2d-architect` / `software-architect` / `game-systems-designer`）**全部剥离“全栈闭环 / 工程执行 / 自写回滚”条款**，明确标定为叠加于 Planner 的“只读技术智囊”，且统一规定**进入 Worker 施工期不再挂载任何顾问技能**（避免消耗上下文并诱发扩范围）。
2. **唯一事实源分工**：全局路由表、预算上限、标准目录树仅在 `AGENTS.md` 维护一份权威定义，各模板内项目级 `AGENTS.md` 只写项目特有红线与门禁命令，不做全文复读。

---

## 5. 经济账本与运营护栏（Cost & Attention Governance）

### 5.1 模型与算力精准匹配（路由表唯一绑定原则）
所有厂商型号与价格参数继续**唯一收敛在 `AGENTS.md` 第 4 节**，四角色对应差异化选型逻辑：
* **Secretary（高频轻量）**：选用极低单价/免费层快速的 Agent 模型（例如 DeepSeek Flash 或免费平台层），因为仅做索引检索与文件清单筛选，单次花费近乎为零。
* **Planner（低频高智商）**：选用推理幻觉最低的旗舰模型（如 Gemini 4 Hydrogen `high/xhigh`；L2 可选 Carbon 二审），配合 `FEED_DROP/` 中 `L1__` 前缀逐字不变触发 **5% 隐式缓存计费**。
* **Worker（重工具长跑）**：选用高并发低价强编码模型（如 DeepSeek V4.1 Flash），大批量编译修复优先安排在北京时间错峰半价时段（午间、18:00 后、周末节假日）。
* **Watchdog（低频冷静旁路）**：仅对 L1/L2 启动独立实例校验，或由 CEO 在触发复盘阈值时唤醒；L0 任务免开独立 Watchdog 会话，严防监督成本高于任务本身。

### 5.2 核心运营指标（保留 6 项必记，重点监控注意力回报）
延续并微调 v2.0 指标体系（写入 `METRICS.md`）：
1. **越权文件修改次数**（硬目标：0）
2. **无证据声称通过次数**（Watchdog 重点拦截，硬目标：0）
3. **任务书一次批准率**（目标：≥ 70%，反映 Secretary 备菜质量 + Planner 规划水准）
4. **Worker 首过率**（目标：≥ 60%，按 L0/L1/L2 分组统计）
5. **最终验收成功率**（目标：≥ 85%）
6. **CEO 每周干预耗时 & 每验收任务成本**：重点盯防“是不是又让人肉干了本该由 Secretary 干的搬运活”。

---

## 6. 套件 v3.0 迭代开发路线（Implementation Roadmap）

为确保重构过程本身严守“小步、可验证、可回滚”原则，建议将本《设计总纲》拆分为 **两批顺序推进的工程任务**（由我后续为你生成具体可执行任务书）：

* **Iteration 1（底层基础设施与剧本升级——Script & Template Hardening）**：
  * 编写并单测 `scripts/stage_context.py`（实现 `FEED_DROP/` 扁平化拷贝、`--chat-safe`、Token 估算与 `00_CONTEXT_MANIFEST.md` 生成）；
  * 升级 `scripts/validate_handover.py`（全面整合此前修复的 5 项校验缺陷，并适配 `FEED_DROP/` + `00_CONTEXT_MANIFEST.md` + `--l0`）；
  * 为两套项目模板添加 `AI_Context/PROJECT_BOARD.md`，升级 `.gitignore` 与 `pyproject.toml` 隔离规则，同步 Unity `ProjectAuditWindow.RunBatchAudit` 与模板文字修正。
  * *阶段验收标准*：Python `unittest` 全绿、两套模板工具链对含 `FEED_DROP/` 的模拟任务目录 100% 免疫污染且门禁通过。

* **Iteration 2（组织重构与全套规范切换——Roles, Skills & Docs Overhaul）**：
  * 创建 `skills/secretary-router/SKILL.md`；
  * 将 `executor-engine` 重构更名为 `skills/worker-engine/SKILL.md`；
  * 将 `engineering-verifier` + `failure-retrospector` 合并重构为 `skills/watchdog-inspector/SKILL.md`；
  * 清洗三份顾问技能越权残留与 `GAMEDEV.EditorTools` 漂移；
  * 全面重写 `AGENTS.md`、`README.md`、`docs/USAGE.md` 及模板内 `AGENTS.md` / `_templates/`（彻底清除 ABC 旧路径与旧名词 `Executor`）。
  * *阶段验收标准*：用重构后的 Kit 模拟完整跑通一次“Secretary 备菜 → Chat 拖拽 Planner 出草案 → Worker 施工 → Watchdog 验收 → Secretary 回写”全链路演练无阻断。
