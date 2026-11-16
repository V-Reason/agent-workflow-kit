# Agent 工作流套件 · 使用指南

> 本文回答一个问题：**这套东西拿到手，怎么用起来。**
> 套件内三份人读/机读文件的分工如下，按需查阅，不必都读。

| 文件 | 读者 | 回答的问题 | 什么时候读 |
| --- | --- | --- | --- |
| `README.md` | 人 | 套件是什么、装在哪、怎么维护 | 第一次接触套件 |
| `docs/USAGE.md`（本文） | 人 | 目录为什么这样分、技能何时用哪个、校验器怎么跑、一个任务从头到尾怎么走 | 准备真正开始用 |
| `AGENTS.md` | AI Agent（机读） | 状态机、分级、交接包七件套、额度、指标等全部协议 | 交给 Agent，每个会话启动必读；人只需查第 0、10 节红线 |

---

## 1. 目录划分：这套文件怎么组织

### 1.1 完整目录树（带注释）

```text
agent-workflow-kit/
├── README.md                 人读导览：安装、快速开始、维护节奏
├── AGENTS.md                 机读总纲（协议唯一事实源）：角色边界、状态机、
│                             L0–L3/R0–R3 分级、路由表、上下文红线、交接包、
│                             A01–A03 额度、六项指标、宁停勿猜红线
├── .gitignore                套件自身作为 git 仓库时的忽略规则
│
├── docs/                     人读文档层
│   └── USAGE.md              本文（详细使用手册）
│
├── skills/                   能力层：一个角色一个目录，目录内一个 SKILL.md
│   ├── planner-orchestrator/     Planner 编排者（大脑）
│   ├── executor-engine/          Executor 执行者（手替）
│   ├── task-brief-writer/        任务书撰写器（Planner 写 PLAN 时加载）
│   ├── software-architect/       顾问：Python/通用软件架构
│   ├── unity2d-architect/        顾问：Unity 2D 架构与性能
│   ├── game-systems-designer/    顾问：玩法系统与数值规格
│   ├── engineering-verifier/     验证员（VALIDATING 阶段独立裁判）
│   └── failure-retrospector/     复盘员（失败归因与流程治理）
│
├── templates/                资产层：一种项目类型一个模板，复制即起步
│   ├── software-py/              Python 通用软件（uv + ruff + mypy + pytest，src 四层）
│   │   ├── src/app/              domain / application / infra / interfaces 四层骨架
│   │   ├── tests/                unit + integration，9 个示例用例开箱全绿
│   │   ├── AI_Context/           上下文体系（9 文件 + TASKS + EVIDENCE）
│   │   ├── AI_Context/TASKS/_templates/   交接包七件套模板（与校验器一一对应）
│   │   ├── scripts/validate_handover.py   校验器副本（项目内直接可用）
│   │   └── AGENTS.md / pyproject.toml / .gitignore / .gitattributes / .editorconfig
│   └── unity2d/                  Unity 2D 游戏（asmdef 物理分层 + 组合根引导）
│       ├── Assets/Scripts/       Core / Gameplay / UI / Editor 四个 asmdef 程序集
│       ├── Assets/Tests/Editor/  GameClock 6 个 EditMode 用例
│       ├── AI_Context/           上下文体系 + 交接包模板（Unity 版）
│       ├── Packages/manifest.json
│       └── scripts/validate_handover.py   校验器副本
│
├── scripts/                  工具层
│   └── validate_handover.py      交接包校验器（唯一实现；模板内是同步副本）
└── tests/                    校验器标准库回归测试
    └── test_validate_handover.py（python -m unittest discover -s tests）
```

### 1.2 划分逻辑：五层各管一件事

| 层 | 位置 | 设计意图 | 变更频率 |
| --- | --- | --- | --- |
| 协议层 | `AGENTS.md`（+ 各模板内项目级 `AGENTS.md`） | 全套件的"宪法"。协议细节只在此定义一处，其他文件引用而不复制 | 低；修订集中进行 |
| 能力层 | `skills/` | 按**角色**划分：每个角色独立目录、独立 SKILL.md，可按阶段和项目类型自由组合装载 | 中；随方法论演进而改 |
| 资产层 | `templates/` | 按**项目类型**划分：每种类型一个完整骨架，自带上下文体系、交接包模板、门禁命令与校验器副本 | 中；随项目经验回写 |
| 工具层 | `scripts/` | 全套件只有一份实现（校验器），模板内副本仅随模板分发，升级以根目录版本为准覆盖 | 低 |
| 文档层 | `docs/` + `README.md` | 人读文档。机读协议永远不进文档层 | 低 |

三条划分原则，日后你自己新增文件时照此归位：

1. **机读与人读分离**：给 Agent 看的协议写进 `AGENTS.md`，给人看的说明写进 `docs/` 与 `README.md`；同一细节只在一处维护（唯一事实源），避免两处改了一处忘。
2. **角色与资产分离**：`skills/` 按"一个人一个文件夹"分（角色），`templates/` 按"一种项目一个骨架"分（资产）。新角色进 `skills/`，新项目类型进 `templates/`，工具进 `scripts/`。
3. **唯一实现 + 同步副本**：校验器只在套件根 `scripts/` 维护；模板内的副本用于项目内直接调用，升级时以根目录版本复制覆盖。

### 1.3 文件的去向：使用时会复制到三个地方

套件是"仓库"，用起来时文件会离开套件、各去一处：

```text
skills/<角色>/SKILL.md      ──复制到──>  Agent 平台技能目录（如项目 .claude/skills/）
                                        或粘贴为系统提示词（对话式 Agent）
templates/<类型>/*          ──复制到──>  新项目根目录（实例化，见第 5 节）
scripts/validate_handover.py ──已随模板进入项目──>  项目 scripts/（套件根这份只用于升级覆盖）
AGENTS.md                   ──不复制──>  留在套件；模板内的项目级 AGENTS.md 已
                                        继承其全部协议并与项目约定叠加
```

---

## 2. 十分钟上手

### 2.1 第一步：装载技能

按你的 Agent 形态选一条路径：

**路径 A：Claude Code / Antigravity（有技能目录机制的平台）**

```bash
# 在你的项目根目录执行（先装双核，够用再扩）
mkdir -p .claude/skills
cp -r <套件路径>/skills/planner-orchestrator  .claude/skills/
cp -r <套件路径>/skills/executor-engine       .claude/skills/
cp -r <套件路径>/skills/task-brief-writer     .claude/skills/
```

Agent 会按各 `SKILL.md` 的 `description` 自动触发；也可在对话里点名："加载 planner-orchestrator 技能"。

**路径 B：其他有规则/技能目录机制的平台（Cursor、Windsurf 等）**

复制到平台等效的规则/技能目录，机制同路径 A：目录名即技能名，Agent 按 description 触发。

**路径 C：任意对话式 Agent（无技能目录机制）**

打开对应 `SKILL.md`，把 YAML frontmatter（开头 `---` 块）以外的正文整段粘贴为系统提示词。每次会话只贴**当前角色**那一份；需要叠加顾问时，把顾问技能正文追加在同一条系统提示词之后。

**验证装载是否成功**：问 Agent 两个问题——"你现在的角色是什么？"和"你的禁止事项有哪些？"。能准确复述角色边界（如 Planner"不写入项目文件、不批准自己的计划"）即装载成功。

### 2.2 第二步：从模板建项目

**通用软件（Python）——5 步**（详见 `templates/software-py/README.md`）：

```bash
cp -r templates/software-py/ ~/my-project && cd ~/my-project
# 1. 改包名：全局替换 src/app、app.、pyproject 中的 "app"（沿用 app 可跳过）
# 2. 填 AI_Context/PROJECT_OVERVIEW.md 与 MODULE_MAP.md
# 3. 更新 pyproject.toml 的 name / description
uv sync                    # 4. 装依赖
uv run pytest              # 5. 9 个用例全绿即骨架可用
git init && git add -A && git commit   # 由你执行，不交 Agent
```

**Unity 2D 游戏——7 步**（详见 `templates/unity2d/README.md`）：

1. Unity Hub 新建 2D 工程（2022.3 LTS 或 Unity 6）；
2. 把模板的 `Assets/`、`Packages/manifest.json`、`AI_Context/`、`scripts/`、`AGENTS.md` 并入工程根（`.gitignore`/`.gitattributes` 是**合并**不是覆盖）；
3. Unity 打开，Console 期望 0 error；
4. Test Runner > EditMode > Run All，期望 6 用例全绿；GAMEDEV > 审计 > 项目结构审计，期望 FAIL = 0；
5. GAMEDEV > 搭建 > 当前场景插入 GameBootstrap，存为 `Assets/Scenes/Bootstrap.unity`；
6. 填 `AI_Context/PROJECT_OVERVIEW.md`（渲染管线、PPU、分辨率基线）；
7. `git init` 并首次提交（你执行）。

### 2.3 第三步：跑通首个任务

按第 5 节"完整走一遍"执行。首月建议按 v2.0 第 15 章节奏：**阶段 1 只规划不执行**（写 3 个任务书，练批准循环），**阶段 2 低风险执行**（3–5 个 L0/R0–R1），再进入 L1 试点。

---

## 3. 技能手册：8 个 SKILL.md 何时用哪个

### 3.1 技能总表

| 技能（frontmatter name） | 角色 | 何时加载 | 给它什么 | 期待产出 |
| --- | --- | --- | --- | --- |
| `planner-orchestrator` | Planner（大脑） | 新需求登记、任务分级、规划、交接编排、执行报告审查 | 需求描述 + `AI_Context/` 相关文件 | 分级结论（L/R）、PLAN_vNN 草案（终态只能是 DRAFT / NEED_INVESTIGATION）、路由建议 |
| `task-brief-writer` | Planner 的写作模式 | Planner 实际起草或升版 PLAN_vNN 时叠加 | 分级结论 + 上下文包 | 0.Metadata + 14 章固定骨架的任务书 |
| `executor-engine` | Executor（手替） | 收到**已批准**任务书要实施时（新会话） | PLAN_vNN（APPROVED）+ APPROVAL_RECORD + 上下文包 + 项目根路径 | EXECUTION_REPORT_Axx（Preflight、实际修改、命令证据、AC 映射、用量、偏离、回滚说明） |
| `engineering-verifier` | 验证员 | 任务进入 VALIDATING / ACCEPTANCE_REVIEW 时（必须新会话） | 执行报告 + 门禁命令清单 + 任务书 AC | ACCEPTANCE.md（逐条：项/期望/实测/证据，ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT） |
| `failure-retrospector` | 复盘员 | 升级、额度耗尽、批准率下降、周/月复盘时 | 升级诊断包或指标数据 | 归因结论、流程修正、路由表修订建议 |
| `software-architect` | 顾问（叠加） | Python 项目规划期，任务涉及架构/选型/审查 | 具体架构问题 + 相关模块 | 选型与审查意见（并入 PLAN，不单独落地） |
| `unity2d-architect` | 顾问（叠加） | Unity 项目规划期，任务涉及分层/物理/渲染/性能 | 具体架构问题 + 相关模块 | 同上 |
| `game-systems-designer` | 顾问（叠加） | 玩法机制、数值平衡、系统规格设计 | 设计需求 + 品类约束 | 系统规格、数值表结构、状态机穷举（并入 PLAN 或 GDD） |

### 3.2 装载组合速查

| 场景 | 装载组合 |
| --- | --- |
| 任何项目起步（最小双核） | `planner-orchestrator` + `executor-engine` + `task-brief-writer` |
| Python 项目 L1 规划 | 双核 + `software-architect` |
| Unity 2D 项目 L1 规划 | 双核 + `unity2d-architect`；涉及玩法数值再加 `game-systems-designer` |
| L2 深度任务规划 | 双核 + 对应顾问，Planner 用 xhigh 档；可选二审（只出 REVIEW_NOTE） |
| 执行阶段 | `executor-engine`，**单独会话** |
| 验证阶段 | `engineering-verifier`，**必须新会话/新实例** |
| 失败处理与周复盘 | `failure-retrospector` |

原则：**按阶段装载，不一次性全装**。执行会话里只放 Executor 一份，避免角色串台。

### 3.3 会话纪律（三条铁律）

1. **禁止自证**：Executor 与 Verifier 必须由不同会话、不同模型实例或人工担任。同一实例"自己写自己验"= 验收无效（L0 快速通道除外：免独立验证员，由你直接检查 Diff 并签收）。
2. **Planner 可叠加**：同一会话内 Planner 主技能 + 专业顾问可以共存（架构类任务先加载顾问再规划）。
3. **批准只出自人**：无论哪个技能，`APPROVED` 状态与 APPROVAL_RECORD 只能由用户写入；Agent 输出终态停在 DRAFT / NEED_INVESTIGATION。

### 3.4 逐技能要点

**planner-orchestrator（Planner）**：双 Agent 工作流的"大脑"。给它需求时要附上项目根路径与 `AI_Context/` 相关文件，它负责六问分级（L0–L3/R0–R3）、裁剪上下文包、起草任务书。注意两点：它不写任何项目文件；它产出的是草案，批准权在你。

**task-brief-writer（任务书撰写器）**：Planner 写 PLAN 时的"格式与质量插件"，保证任务书"一键可执行"——Executor 拿到文本无需追问即可 Preflight。你不直接调用它，而是确认 Planner 装载了它；检查产出时看三样：0.Metadata 是否带 Plan Version、第 6 章文件范围是否精确到路径、第 9 章验收标准是否可测。

**executor-engine（Executor）**：只做一件事——把批准的任务书变成带证据的工程事实。交接时必须给全四样：批准版任务书、批准记录、上下文包、项目根路径。它会先回报"已读取的批准版本、文件范围、Preflight 结果"，确认无冲突才开始写入；这一步是你拦截越权的最后闸门。

**engineering-verifier（验证员）**：独立裁判，职责是"判定"不是"修复"——发现问题开回执退回 REWORK，绝不亲自改代码凑通过。给它任务书 AC 与执行报告即可；无证据一律判 NOT RUN。

**failure-retrospector（复盘员）**：流程的"免疫系统"。触发条件：任务升级、A01–A03 额度耗尽、一次批准率 < 70%、周喂上下文 > 2 小时、或月 L1+ 任务 ≥ 8 个。产出三类东西：诚实归因（模型决策 / 上下文过期 / 流程缺口 / 需求歧义）、流程修正、路由表修订建议。

**三个专业顾问（software-architect / unity2d-architect / game-systems-designer）**：规划期叠加加载，只出意见不落地。按项目类型选：Python 项目用 software-architect，Unity 2D 用 unity2d-architect，玩法设计再加 game-systems-designer。它们与 planner-orchestrator 同会话共存；其结论由 Planner 并入任务书，不单独产生文件。

---

## 4. 校验器手册：validate_handover.py

### 4.1 四种模式：校什么、什么时候跑

| `--for` | 必查件 | 校验要点 | 什么时候跑 | 谁跑 |
| --- | --- | --- | --- | --- |
| `planner` | TASK_BRIEF + CONTEXT_PACKET_vNN + PLAN_vNN | 任务书 10 段齐全；PLAN 含 0.Metadata + 14 章；状态为草案态（DRAFT / NEED_INVESTIGATION） | Planner 交出草案后、发给你审批前 | Planner 产出侧（你抽查） |
| `executor` | planner 三件 + 状态=APPROVED + APPROVAL_RECORD | 批准版本一致、批准记录存在且含授权范围 | 你批准后、把包交给 Executor 前（交接七步第 5 步） | 你 |
| `verifier` | executor 四件 + EXECUTION_REPORT_Axx | 执行报告章节齐全、尝试号合法（A01–A03） | Executor 交报告后、验证员开工前 | 你或验证员 |
| `archive` | verifier 五件 + ACCEPTANCE | 验收决定字段合法（ACCEPT / ACCEPT WITH FOLLOW-UP / REJECT） | 归档进 ARCHIVED 前 | 你或复盘员 |

规律：**后一模式包含前一模式的全部必查件**，链条 = 四道闸门依次收紧。

**L0 快速通道（`--l0`，与 `--for` 正交）**：L0 任务免 PLAN 与批准记录——必查件降为 mini 任务书（含 L0 标识、目标与验收、文件范围三要素，无 `<>` 占位符）+（verifier/archive 模式）执行报告与验收；CONTEXT_PACKET 可选（存在则照常校格式）。若目录内存在 PLAN，其 Task Level 必须为 L0，L1/L2/L3 直接 FAIL，防止高风险任务借 L0 绕过审批。对应 AGENTS.md 第 2 节规则：L0 免独立验证员会话，由你直接检查 Diff 并签收；L1/L2 强制独立验证员。

### 4.2 命令与输出

```bash
cd <项目根目录>     # 模板内已自带 scripts/validate_handover.py 副本

python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0099 --l0 --for executor   # L0 快速通道
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor --json   # 机器可读
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor --list   # 先看必查件清单
```

读输出：每件给出 **PASS / WARN / FAIL** 三态——FAIL 必须处理；WARN 不拦截但建议补齐。退出码：`0` 全部通过（WARN 不影响），`1` 存在 FAIL。

### 4.3 挂进脚本或 CI

```bash
# 示例：把校验器作为执行前置门禁
TASK_DIR=AI_Context/TASKS/GD-2026-0001
python scripts/validate_handover.py "$TASK_DIR" --for executor --json > /tmp/handover.json \
  || { echo "交接包未过校验，停止执行"; exit 1; }
```

同理可挂 Git pre-commit 钩子（拦截未归档任务）或 CI 步骤（归档前自动校验）。

### 4.4 校验边界（必读）

校验器**只做结构校验**：文件在不在、章节齐不齐、状态字段合不合法。它不能验证：APPROVED 是否真出自你手（要你核对批准记录）、测试是否真跑过（以工具实际输出为准）、验收是否真通过（以验证员证据为准）。结构合规 + 真实证据，两样齐才算流程完整。

---

## 5. 完整走一遍：一个 L1 任务的十一步

以 `GD-2026-0001`（给 CLI 看板加一个导出功能）为例。标 **[停等]** 的步骤是人工决策点，Agent 在此必须停下等你。

### 5.1 时间轴总表

| # | 状态机位置 | 谁动 | 动作 | 产出 / 命令 |
| --- | --- | --- | --- | --- |
| 1 | INTAKE → TRIAGED | 你 | 写任务简报（10 段固定结构）；按六问预判分级 | `AI_Context/TASKS/GD-2026-0001/TASK_BRIEF.md` |
| 2 | CONTEXT_READY | 你 / 取材员 | 裁剪上下文包（版本号 + 核验 commit）；上下文不足先派只读调查 | `CONTEXT_PACKET_v01.md`（按需 `RECON_REPORT.md`） |
| 3 | PLANNING | Planner 会话 | 装载 planner-orchestrator（+ 对应顾问），产出草案 | `PLAN_v01.md`；`--for planner` 校验 |
| 4 | PLAN_REVIEW **[停等]** | 你 | 审草案：不批 → REJECTED 退回修订；批准 → 改状态 APPROVED、写批准记录 | `APPROVAL_RECORD.md` |
| 5 | 交接前 **[停等]** | 你 | 跑交接校验，退出码 0 才交接 | `--for executor` |
| 6 | READY_TO_EXECUTE → EXECUTING | Executor 新会话 | 装载 executor-engine；先回报批准版本、文件范围、Preflight，确认无冲突才写入 | Preflight 记录 |
| 7 | EXECUTING | Executor | 按第 7 章步骤实施、跑门禁、逐条取证；受阻即停 | 门禁输出、Diff |
| 8 | EXECUTED | Executor | 产出执行报告 | `EXECUTION_REPORT_A01.md`；`--for verifier` 校验 |
| 9 | VALIDATING | 验证员新会话 | 装载 engineering-verifier；跑门禁、逐条 AC 核对 | `ACCEPTANCE.md` |
| 10 | ACCEPTANCE_REVIEW **[停等]** | 你 | 读回执做最终决定：ACCEPT / WITH FOLLOW-UP / REJECT | 回执签收 |
| 11 | ARCHIVED | 你 + 复盘员 | 证据落盘 EVIDENCE/；24 小时内提交上下文回写提案；登记六项指标 | `CONTEXT_UPDATE_PROPOSAL.md`、`METRICS.md` |

### 5.2 关键步骤的要点

**第 1 步（写 TASK_BRIEF）**：10 段结构在 `AI_Context/TASKS/_templates/TASK_BRIEF.md`，照抄填空即可。分级拿不准就填"待 Planner 判定"，不要自己拍 L0。

**第 3 步（规划）**：给 Planner 的输入 = 任务简报路径 + 上下文包路径 + 项目根。产出草案后你自己跑一遍 `--for planner`，PASS 再进入审批，避免来回。

**第 4 步（批准）**：这是全流程唯一授权点。批准动作 = 把 PLAN 内状态字段改为 `APPROVED` + 填写 `APPROVAL_RECORD.md`（批准版本、授权路径清单、条件与禁止项、批准时间）。只把任务书发给 Executor **不构成授权**。

**第 6 步（交接）**：给 Executor 的消息模板——"项目根 `<路径>`；执行 `GD-2026-0001`，批准版本 `PLAN_v01.md`，范围见批准记录；先回报 Preflight。"若它没先回报版本与范围就要写文件，立即叫停。

**第 9 步（验证）**：验证员是新会话。给它三样：任务书 AC、执行报告、门禁命令清单（模板 README 的"常用门禁命令"表）。

**第 11 步（归档与回写）**：执行中发现的"代码与文档不一致"，24 小时内按 `_templates/CONTEXT_UPDATE_PROPOSAL.md` 提交回写提案，由你审阅合入 `AI_Context/`。这是上下文体系不过期的主要机制。

### 5.3 L0 快速通道（对照）

条件满足时（六问全否、局部修改、模式成熟、R0 级），可走快速通道：

```text
INTAKE → TRIAGED(L0) → EXECUTING → VALIDATING → ACCEPTED → ARCHIVED
```

省掉 Planner、PLAN_REVIEW 与独立验证员会话，由 Executor 独立执行；但 **Diff 检查不可省**，ACCEPTANCE.md 由你本人签收。交接校验用 `--l0` 标志，任务简报可写三行 mini 版（含 L0 标识、目标与验收、文件范围）：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0099 --l0 --for executor
```

判断不了就按 L1 走——多花一次规划的代价远小于越权改动的代价；校验器也会拦下借 L0 通道混入的高级别任务书。

### 5.4 执行失败与额度（A01–A03）

- 每任务最多三次尝试：A01 首次实施，A02、A03 是两次**有依据**的范围内修复；每次报告必须写明与上一次的区别。
- 额度不是必须用满：出现架构假设错误、范围蔓延、数据风险、连续两轮无进展，**立即停**，产出升级诊断包交回 Planner——升级与重新规划不消耗额度。
- 你在任一时刻都可以说"停"：这是宁停勿猜红线的用户侧用法。

---

## 6. 日常运营节奏

| 节奏 | 做什么 | 依据 |
| --- | --- | --- |
| 每任务验收后 24 小时内 | 提交上下文回写提案（CONTEXT_UPDATE_PROPOSAL），你审阅合入 | AGENTS.md 第 5 节硬性条款 |
| 每周 | 六项必记指标登记到项目 `AI_Context/METRICS.md`（一次批准率、首过率、最终成功率、人工审核时间、每任务成本、越权次数） | AGENTS.md 第 9 节 |
| 触发式 | 周喂上下文 > 2 小时 / 批准率 < 70% / 月 L1+ ≥ 8 个 → 调 `failure-retrospector` 复盘 | AGENTS.md 第 9 节 |
| 每月 | 复盘方法论与套件版本，吸收回写沉淀 | v2.0 第 15 章阶段 6 |
| 每季度 | 复核 AGENTS.md 第 4 节模型路由表（对照厂商价格页），整表替换并更新日期 | AGENTS.md 第 4 节 |

---

## 7. 常见问题（FAQ）

**Q1：技能装了但不自动触发？**
自动触发依赖平台按 `description` 匹配，不一定稳定。直接点名："加载 planner-orchestrator 技能"；对话式 Agent 则检查系统提示词里是否真的贴了正文。

**Q2：需要一次装全部 8 个技能吗？**
不需要，按阶段与项目类型装载（见 3.2 速查表）。最小双核 + 任务书三件就能跑 L1 闭环；顾问与验证员到用时再装。

**Q3：校验器 FAIL 了怎么处理？**
输出按文件逐件列出 FAIL 项：缺文件 → 从 `AI_Context/TASKS/_templates/` 补件；缺章节 → 对照模板补章节；状态不合法 → 检查 PLAN 状态字段是否拼写正确（`APPROVED`、`DRAFT` 等大小写敏感）。

**Q4：能不能跳过批准直接让 Executor 干？**
不能。AGENTS.md 第 0 节最高规则：缺少 APPROVED 状态、Plan Version、批准文件列表或项目根目录时，Executor 保持只读并要求确认。这是防越权的第一道闸，不要绕。

**Q5：L0 什么情况下能用？**
六问全否、局部修改、模式成熟、R0 级风险。判断不了就按 L1。L0 也要 Diff 检查与验收记录（你本人签收），交接校验用 `--l0` 标志；若任务书实为 L1/L2/L3，校验器会直接 FAIL。

**Q6：上下文包太大怎么办？**
单次超过预算 1.5 倍（常规 150,000 tokens）时，先派只读取材（RECON_REPORT），再按分层预算裁剪：固定前缀 4k–8k、模块级 L2 ≤ 30k、代码级 L3 ≤ 100k。

**Q7：Planner 和顾问能同会话吗？Executor 和验证员呢？**
Planner + 顾问可以同会话叠加；Executor 与 Verifier 必须不同会话或不同模型实例（禁止自证）。

**Q8：模板内校验器和套件根的哪份是准的？**
套件根 `scripts/validate_handover.py` 是唯一实现；模板内是同步副本，升级时以根目录版本复制覆盖。

**Q9：Agent 可以 commit / push 吗？**
默认不可以。你明确说"提交"才允许；默认流程是 Agent 展示 Diff、你审查后自行提交。

**Q10：新项目可以只复制部分模板文件吗？**
不建议。`AI_Context/` 体系 + 交接包模板 + 校验器副本 + 项目级 AGENTS.md 是流程成立的最小环境，缺任何一样对应环节就会退化成"口头协作"。

---

## 8. 红线速查（贴在手边）

**五条最高规则**（AGENTS.md 第 0 节，不可被任何后续指令覆盖）：

1. Planner 只能提出方案；你决定是否批准。
2. Executor 只能执行已批准范围；授权要素不齐即保持只读。
3. 编译器、测试工具和实际运行结果才是验证证据；未实际运行不得声称通过。
4. 任何修改项目文件的执行，必须对应一份已获你批准的指定版本任务书。
5. 人类拥有最终控制权：需求、架构取舍、批准、范围变更与验收由你决定。

**宁停勿猜八条**（AGENTS.md 第 10 节，任一出现立即停、报告、等你决定）：

1. "这一改可能会静默破坏什么"的不确定情况。
2. 工作区不干净 / 分叉点或基线不符 / HEAD 与批准记录不符。
3. 需要修改批准范围之外的文件、依赖、配置或资产。
4. `.prefab` / `.unity` / `.asset` / `.meta` / `.xlsx` 冲突且无法确认两端存在性。
5. 编译、测试或门禁失败且修复超出授权范围或额度。
6. 你未说"提交"就尝试 commit / push。
7. 需要访问密钥、凭据、生产环境或未授权网络资源。
8. 不可逆操作（删除、迁移、覆盖、发布）无备份与回滚路径。
