# Agent 工作流套件（Agent Workflow Kit）

《Agent 工作流 v2.0》（docx，2026-11-15）的方法论配套实施套件。方法论回答"为什么这样协作"，本套件回答"具体怎么做"：一套可直接装载的 Agent 技能、两套项目模板、以及贯穿全流程的交接包校验器。所有术语、状态机、分级与指标与 v2.0 文档严格对齐。

## 目录导览

| 路径 | 内容 | 给谁用 |
| --- | --- | --- |
| `AGENTS.md` | Agent 总纲：状态机、分级、路由表、上下文红线、交接包、额度、指标 | AI Agent（机读） |
| `docs/USAGE.md` | 使用指南：目录划分、技能手册、校验器手册、完整流程走读、FAQ | 人（详读） |
| `skills/` | 8 个 SKILL.md：Planner、Executor、任务书、Unity2D 架构师、软件架构师、游戏系统策划、验证员、复盘员 | AI Agent（装载） |
| `templates/software-py/` | Python 通用软件项目模板（uv + ruff + mypy + pytest，src 四层架构） | 新项目起步 |
| `templates/unity2d/` | Unity 2D 游戏开发项目模板（asmdef 物理分层 + 引导 + Editor 工具） | 新项目起步 |
| `scripts/validate_handover.py` | 交接包校验器（七件套结构校验，planner / executor / verifier / archive 四种模式，支持 `--l0` 快速通道） | 人 + Agent |
| `tests/test_validate_handover.py` | 校验器标准库回归测试（31 用例） | 维护者 |

## 快速开始

### 第一步：装载技能

把 `skills/` 下需要的技能目录复制到你的 Agent 平台技能目录：

- **Claude Code / Antigravity**：复制到项目的 `.claude/skills/` 或平台等效位置，Agent 会按 `SKILL.md` 的 description 自动触发，也可手动点名加载。
- **任意对话式 Agent**：直接把对应 `SKILL.md` 全文粘贴为系统提示词使用（frontmatter 忽略，正文自足）。

最小装载组合：`planner-orchestrator` + `executor-engine` + `task-brief-writer`（双核 + 任务书）。专业顾问（unity2d-architect / software-architect / game-systems-designer）按项目类型叠加；`engineering-verifier` 与 `failure-retrospector` 在进入 VALIDATING / 失败处理阶段时加载。装载方式、逐技能说明与组合速查表见 `docs/USAGE.md` 第 2、3 节。

### 第二步：从模板创建项目

- **通用软件（Python）**：复制 `templates/software-py/`，按其中 README 的"实例化"一节改名（包名、pyproject、AI_Context 概述），然后 `uv sync && uv run pytest` 验证骨架可用。
- **Unity 2D 游戏**：先用 Unity Hub 新建 2D 工程（2022.3 LTS 或 Unity 6），再把 `templates/unity2d/` 下的 `Assets/`、`Packages/`、`AI_Context/`、根配置文件并入工程，按其中 README 的步骤打开并确认 asmdef 编译通过。

两个模板都已内置：项目级 `AGENTS.md`（继承套件总纲）、完整 `AI_Context/` 上下文目录体系、交接包七件套模板、校验器副本。

### 第三步：跑通首个 L1 任务

按套件总纲（`AGENTS.md` 第 2、6 节）走一遍最小闭环：

```text
1. 写 TASK_BRIEF.md（10 段）放入 AI_Context/TASKS/GD-2026-0001/
2. 裁剪 CONTEXT_PACKET_v01.md（版本号 + 核验 commit）
3. 加载 planner-orchestrator → 产出 PLAN_v01.md（草案，14 章）
4. 你审批：改状态为 APPROVED，写 APPROVAL_RECORD.md
5. python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor
6. 加载 executor-engine 执行 → 产出 EXECUTION_REPORT_A01.md
7. 加载 engineering-verifier → 门禁 + 验收回执 ACCEPTANCE.md
8. 24 小时内按附录 H 提交上下文回写提案
```

首月建议按 v2.0 第 15 章实施路线走：阶段 1 只规划不执行（3 个任务书），阶段 2 低风险执行（3–5 个 L0/R0–R1），再进入 L1 试点。

## 交接包校验器

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner    # 草案齐全性
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for executor   # 批准完整性
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for verifier   # 执行报告
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive    # 归档齐全性
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0099 --l0 --for executor   # L0 快速通道
```

- 校验七件套是否齐全、章节是否完整、状态字段是否合法（如 executor 模式要求 `PLAN_vNN.md` 状态为 APPROVED 且存在批准记录）；占位符残留（`<...>` / `待填写` / `TBD`）与版本不一致会被拦截。
- `--l0` 快速通道：放行无 PLAN / 无批准记录（mini 任务书 + 执行报告 + 验收即可）；目录内若存在 PLAN，其 Task Level 必须为 L0，防止高风险任务绕过审批。
- `--json` 输出机器可读结果；退出码 0 通过、1 失败，可挂进脚本或 CI。
- 回归测试：`python -m unittest discover -s tests -v`（仅标准库，31 用例）。
- 校验器只做结构校验；编译、测试与验收判断仍以真实工具输出和人工审查为准。
- 模板内 `scripts/validate_handover.py` 为同步副本，项目内直接可用；升级时以套件根目录版本为准复制覆盖。

## 维护

| 事项 | 周期 | 做法 |
| --- | --- | --- |
| 模型路由表（AGENTS.md 第 4 节） | 每季度或厂商调价 | 复核官方价格页，整表替换，更新复核日期 |
| 指标打卡 | 每周 | 六项必记指标登记到项目 `AI_Context/`，触发条件见总纲第 9 节 |
| 上下文回写 | 每任务验收后 24 小时内 | 按 v2.0 附录 H 提交提案，人工合入 |
| 套件版本 | 每月复盘 | 参照 v2.0 第 15 章阶段 6：每月复盘规范并更新版本 |

## 与 v2.0 文档的章节映射

| 套件内容 | 对应文档章节 |
| --- | --- |
| AGENTS.md 第 0–3 节（角色/状态机/分级） | 第 2、3、4、5 章 |
| AGENTS.md 第 4 节（路由表） | 第 5.4、14.2、14.3 节 |
| AGENTS.md 第 5 节（上下文红线） | 第 6 章 |
| AGENTS.md 第 6 节（交接包七件套） | 第 7 章 + 附录 C–H |
| AGENTS.md 第 7 节（额度与停止条件） | 第 4.4、11.4、13 章节内容 |
| AGENTS.md 第 9 节（指标） | 第 15.1、15.2 节 |
| planner-orchestrator / task-brief-writer | 第 8、9 章 + 附录 A、C、D |
| executor-engine | 第 11 章 + 附录 B、E |
| engineering-verifier | 第 12 章 + 附录 G |
| failure-retrospector | 第 13 章 + 第 14 章护栏 |
| templates/*（AI_Context、门禁命令） | 第 6 章 + 第 12 章 |
