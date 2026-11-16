# Agent Workflow Kit v3.0 使用指南

本指南面向 CEO 和本地 Agent，说明如何用 Secretary / Planner / Worker / Watchdog 四角色完成一个任务。

## 1. 安装与目录

### 1.1 套件目录

```text
agent-workflow-kit/
  AGENTS.md
  README.md
  docs/
    DESIGN_CHARTER.md
    USAGE.md
  scripts/
    stage_context.py
    validate_handover.py
  tests/
  skills/
    secretary-router/
    planner-orchestrator/
    worker-engine/
    watchdog-inspector/
    task-brief-writer/
    unity2d-architect/
    software-architect/
    game-systems-designer/
  templates/
    software-py/
    unity2d/
```

### 1.2 技能装载

| 使用场景 | 加载 |
| --- | --- |
| 运营、台账、备菜、回写 | `secretary-router` |
| 架构、任务书、重规划 | `planner-orchestrator` + `task-brief-writer` |
| Python 规划 | 再叠加 `software-architect` |
| Unity 规划 | 再叠加 `unity2d-architect`，玩法系统再加 `game-systems-designer` |
| 施工 | `worker-engine` 单装 |
| L1/L2 验证 | `watchdog-inspector`，独立会话/实例 |
| L0 | CEO 直接找 Worker；需要时 Watchdog 快检 |

原则：按阶段装载，同一会话不混 Worker 与 Watchdog；施工期不加载领域顾问。

## 2. 创建项目

### 2.1 Python

```bash
cp -R agent-workflow-kit/templates/software-py <project-root>
cd <project-root>
uv sync
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest
```

实例化后填写：

- `AI_Context/PROJECT_OVERVIEW.md`
- `AI_Context/PROJECT_BOARD.md`
- `AI_Context/MODULE_MAP.md`
- `AI_Context/ARCHITECTURE.md`
- `AI_Context/DEPENDENCIES.md`

### 2.2 Unity 2D

1. 用 Unity 2022.3 LTS 或 Unity 6 新建 2D 工程。
2. 合并模板的 `Assets/`、`Packages/manifest.json`、`AI_Context/`、`scripts/`、`AGENTS.md`、`README.md`、`.gitignore`、`.gitattributes`。
3. Unity 打开后等待编译，Console 0 error。
4. 运行 EditMode 测试和结构审计。
5. 填写 `PROJECT_OVERVIEW.md`、`PROJECT_BOARD.md`、`MODULE_MAP.md`。

Unity 资产红线：

- Agent 不写 `.prefab / .unity / .asset / .meta / .xlsx`。
- 需要资产操作时，PLAN 给 CEO 手工清单：路径、操作、期望值、判据。
- `.meta` 必须跟随资产；GUID 不确定即停止。

## 3. PROJECT_BOARD

Secretary 维护 `AI_Context/PROJECT_BOARD.md`：

```markdown
## Attention Queue
| 事项 | Task ID | 当前状态 | 一句话决策提示 | 更新时间 |

## Ticket Index
| Task ID | 级别 | 状态 | 分支 | 当前 PLAN 版本 | 变更模块摘要 | 一句话结论 |
```

Attention Queue 仅放：

- 待 CEO 批准计划。
- 待 CEO 手工完成资产操作。
- 待 CEO 签收验收。
- Watchdog 异常或流程触发线。

不要把普通进度写入 Attention Queue。

## 4. Secretary 接单与备菜

### 4.1 接单

Secretary 读项目 AGENTS、看板、上下文和 Git 状态，然后：

1. 创建 `AI_Context/TASKS/GD-YYYY-NNNN/`。
2. 填写 `TASK_BRIEF.md`，或在 L0 写三行 mini 简报。
3. 初判 L0–L3 / R0–R3。
4. 更新 Ticket Index。
5. 每次最多向 CEO 问一个具体问题。

### 4.2 生成 FEED_DROP

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --files src/app/domain/models.py src/app/interfaces/cli.py
```

批量清单：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --from-list ai/files.txt
```

补料：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --append --files Assets/Scripts/Core/GameClock.cs
```

关闭 chat-safe 扩展名重命名：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --no-chat-safe --files Assets/Scripts/Editor/Editor.asmdef
```

关闭近期 Git 摘要：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 --git-diff 0
```

### 4.3 stage_context 规则

- 默认清空重建 `FEED_DROP/`；`--append` 按原路径合并去重。
- 固定装入 L1/L2 文件；缺失必需文件直接失败。
- L3 扁平命名示例：

```text
Assets/Scripts/Core/GameClock.cs -> L3__Assets_Scripts_Core_GameClock.cs
Assets/UI/Hud.uxml               -> L3__Assets_UI_Hud.uxml.txt
```

- `.cs .py .md .json .txt .yml .yaml .toml .cpp .h .hpp .c` 保留后缀。
- 其他扩展名在 chat-safe 模式只生成 `.txt` 安全名。
- 拒绝 `..`、仓库外路径、符号链接逃逸、`.env`、私钥和 credential/secret 文件。
- `--json` 输出机器可读结果。
- 预算警告不阻断；错误以退出码 1 结束。

### 4.4 Manifest 检查

`00_CONTEXT_MANIFEST.md` 应包含：

- Task ID
- Base Commit 或非 Git 可恢复时间
- 生成时间与模式
- L1/L2/L3/Total Token
- 文件映射表
- 项目目录摘要
- 明确排除项
- 警告

Token 启发式：

- 每个 CJK 字符计 1。
- 其他非空白字符数 ÷ 4 后向上取整。
- 两层相加后再总计。

## 5. Planner 规划

### 5.1 消费上下文

Chat 模式：把整个 `FEED_DROP/` 拖入对话，并附 Manifest。Planner 读取 Manifest 定位层级和原路径。

Agent 模式：Planner 从 `FEED_DROP/` 与 Manifest 起步，同时保留全仓只读检索权。

### 5.2 NEED_FILES

需要补文件时输出：

```text
NEED_FILES
- path/to/file.ext
理由：该文件决定哪个调用契约或错误边界
```

Secretary 用 `--append` 补齐。Planner 不应要求全仓投喂。

### 5.3 PLAN

加载 `task-brief-writer`，输出 `PLAN_vNN.md`：

- 0.Metadata
- 1. Objective
- 2. Non-goals
- 3. Current State
- 4. Constraints
- 5. Proposed Design
- 6. File Scope
- 7. Execution Steps
- 8. Engineering Rules
- 9. Acceptance Criteria
- 10. Test Plan
- 11. Risks
- 12. Rollback
- 13. Open Questions
- 14. Approval

Planner 只写 `DRAFT` / `NEED_INVESTIGATION`。APPROVED 和批准记录由 CEO 完成。

## 6. CEO 批准

CEO 审核：

1. 目标是否准确。
2. Non-goals 是否覆盖最容易顺手做的扩范围。
3. File Scope 是否精确。
4. 方案是否最小且符合架构。
5. 测试命令是否真实。
6. 风险和回滚是否足够。
7. 是否有未决问题。

批准动作：

1. 将 PLAN 的 Status 改为 `APPROVED`。
2. 填写 `APPROVAL_RECORD.md`：Task ID、Plan 版本、Scope、Conditions、Base Commit、Approver、时间。
3. 运行：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
```

退出码 0 后才能交给 Worker。只发送 PLAN 不等于授权。

## 7. Worker 施工

Worker 先做 Preflight：

- 读取批准版本。
- 核对 Task ID / Plan Version。
- 核对工作区、分支、Base Commit。
- 核对批准文件白名单。
- 确认引用的文件、接口和命令真实存在。
- 先回报计划，再写入。

施工纪律：

- 标准 L1/L2 使用 `ai/GD-YYYY-NNNN` 隔离分支。
- 只改批准范围。
- 不顺手重构或格式化。
- 不新增未批准依赖、配置或资产。
- 每阶段检查 Diff。
- 编译测试必须真跑。
- A01–A03 熔断。

Worker 每次尝试输出 `EXECUTION_REPORT_Axx.md`，固定 11 节，结论仅允许：

```text
PASS
PASS WITH WARNINGS
FAIL
BLOCKED
NOT RUN
```

## 8. Watchdog 验证

L1/L2 必须独立会话。先运行：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
```

然后：

1. 逐路径比较 Diff 与批准范围。
2. 本人实跑门禁。
3. 核对 AC 证据。
4. 检查既有断言未删改。
5. 写 `ACCEPTANCE.md` 事实表与 Watchdog 建议。
6. CEO 最终填写用户决定。

结论建议：

- PASS
- PASS WITH WARNINGS
- FAIL

CEO 最终决定：

- ACCEPT
- ACCEPT WITH FOLLOW-UP
- REJECT

归档前运行：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

## 9. L0 快速通道

L0 适用于局部、模式成熟、低耦合、可快速回退的修改。

三行简报：

```markdown
Task ID: GD-2026-0099（L0）
目标与验收: 修复某个局部问题；验收 = 指定测试命令 exit 0
文件范围: MODIFY src/app/example.py；FORBIDDEN pyproject.toml 与公共接口
```

CEO 可以直接派 Worker。仍须：

- Diff 检查。
- 真实命令证据。
- `ACCEPTANCE.md`。

归档：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0099 --l0 --for archive
```

若任务目录存在任意 L1/L2/L3 PLAN，`--l0` 失败。

## 10. validate_handover

| 模式 | 主要检查 |
| --- | --- |
| planner | Brief + Manifest + FEED_DROP + 14 章 PLAN 草案 |
| worker | 再加 APPROVED 计划和批准记录 |
| watchdog | 再加最新执行报告 |
| archive | 再加 CEO 最终验收决定 |

```bash
python scripts/validate_handover.py <task_dir> --for planner
python scripts/validate_handover.py <task_dir> --for worker --json
python scripts/validate_handover.py <task_dir> --for watchdog
python scripts/validate_handover.py <task_dir> --for archive
python scripts/validate_handover.py --list --for worker
```

校验器会：

- 按数值选择最新版本。
- 拦截未填写枚举和整值占位符。
- 支持无 Git 时间戳。
- 允许 `APPROVED_WITH_CONDITIONS` 与空格形式。
- 核对 Task ID 和 Plan Version。
- 校验 Manifest 文件和 FEED_DROP 实体。
- 对额外未映射文件给 WARN。
- 旧模式参数退出并提示 v3 枚举。

结构合规不等于代码正确。编译、测试、审计和真实运行仍是必要证据。

## 11. 验收后回写

CEO ACCEPT 后 24 小时内，Secretary：

1. 读取批准记录、最新报告、验收和实际 diff。
2. 起草 `CONTEXT_UPDATE_PROPOSAL.md`。
3. 标清新事实、架构变化、依赖、已知问题和 STALE。
4. 更新 Ticket Index，清理 Attention Queue。
5. 更新 METRICS。
6. 交 CEO 审阅合入长期上下文。

## 12. 失败与升级

失败分类：

- 上下文缺失。
- 工程事实冲突。
- API 不确定。
- 编译/测试失败。
- 范围外依赖。
- 回归。
- 环境阻塞。
- 不可复现。

升级诊断包：

- Task ID / Plan / Attempt。
- 状态和环境。
- 首错与有效堆栈。
- 复现步骤。
- 已改文件和 Diff 摘要。
- 已尝试动作。
- 证据位置。
- 未知项。
- 需要 CEO 决策的问题。

升级和重规划不消耗 A01–A03。

## 13. 指标与巡检

| 指标 | 目标 |
| --- | --- |
| 越权修改 | 0 |
| 无证据声称 | 0 |
| 一次批准率 | ≥ 70% |
| Worker 首过率 | ≥ 60% |
| 最终成功率 | ≥ 85% |
| CEO 干预耗时 / 每任务成本 | 记录并复盘 |

触发复盘：

- 一次批准率 < 70%。
- 任意越权。
- CEO 每周因上下文搬运投入 > 2 小时。
- 月 L1+ 任务 ≥ 8 个。

Watchdog 必须选一个主因：模型决策、上下文过期、流程缺口、需求歧义。改进提案先标 `PROPOSED`，由 CEO 决定。

## 14. Git、网络与隐私

- 不默认联网，不上传工程，不下载依赖。
- 不默认配置 remote 或 push。
- `.env`、私钥、Token、日志和本地绝对路径不得入库。
- `FEED_DROP/` 永不入库。
- 提交前和合并前都要扫描 working tree 与 Git 历史。
- 未经 CEO 明确授权，不删除、重置或重写 Git 历史。

## 15. FAQ

**需要一次装载全部 8 个技能吗？**

不需要。按阶段装载，避免角色串台和上下文污染。

**Chat 模式看不到仓库怎么办？**

拖入 `FEED_DROP/` 和 Manifest。它是真实文件入口，不是手工摘要。

**Agent 模式还需要 FEED_DROP 吗？**

需要。Manifest 与 FEED_DROP 让任务基线可审计、上下文可复用；Agent 额外保留只读全仓搜索权。

**为什么不能全选源文件投喂？**

Token 成本、噪声和缓存命中都会变差。先从 L1/L2 起步，再按 NEED_FILES 补 L3。

**Worker 能自己验收吗？**

不能。L1/L2 必须独立 Watchdog；L0 由 CEO 直接看 Diff 与证据。

**Watchdog 发现问题是直接修吗？**

不。它只出失败事实、影响和重规划请求；修复必须走新批准范围。

**为什么 FEED_DROP 不提交？**

它是可重建的本地投喂缓存。Manifest 入库，真实源文件仍在业务路径。

## 16. 红线速查

1. 未批准不写。
2. 超范围即停。
3. 不删断言凑绿。
4. 未跑不写 PASS。
5. 不覆盖用户未提交修改。
6. 不碰 Unity 序列化资产。
7. 不默认联网、commit、merge 或 push。
8. 不带密钥、凭据和本地绝对路径。
9. Worker 不自证。
10. CEO 做最终验收。
