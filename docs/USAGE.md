# Agent Workflow Kit v4.0 使用指南

v4.0 的主变化是：项目创建与装配由 `scripts/workflow.py` 完成，用户不再手工复制模板或逐项合并 Unity 文件。

## 1. 首次使用

从套件根目录运行：

```bash
python scripts/workflow.py
```

无参数进入中文向导。向导按顺序询问：

1. 创建新项目或装配现有项目。
2. 目标路径、项目名与项目类型。
3. 是否允许 Git 初始化。
4. 新 Python starter 是否执行 `uv sync`。
5. 现有项目是否允许脏工作区或受保护配置差异。

向导会先给出完整计划，再由用户确认。`Ctrl+C` 或回答 `N` 不写入文件。

## 2. 装配模式与 Layer

项目由有序 layer 组合：

| Layer | 必需 | 适用 |
| --- | --- | --- |
| `core` | 是 | 工作流宪法、脚本、技能、任务模板和通用上下文 |
| `generic` | 常用 | 语言无关 README 与通用项目入口 |
| `python` | 按需 | 现有 Python 项目规则与门禁 |
| `python-starter` | 按需 | 新 Python 四层业务代码骨架 |
| `unity2d` | 按需 | 现有 Unity 项目规则、静态审计和受保护包配置 |
| `unity2d-starter` | 按需 | Unity Hub 空项目上的最小 asmdef、组合根和测试 |

`core` 自动加入。`python-starter` 依赖 `python`，`unity2d-starter` 依赖 `unity2d`。检测到多个技术栈时可以组合，例如在 Unity 仓库中维护 Python 工具：

```bash
python scripts/workflow.py attach <repo> \
  --layers core,generic,python,unity2d --dry-run
```

## 3. 创建新项目

### 3.1 通用项目

```bash
python scripts/workflow.py create ../my-project \
  --layers core,generic \
  --name "My Project" \
  --yes
```

只创建工作流和上下文骨架，不生成业务代码、依赖清单或特定语言配置。

### 3.2 Python starter

```bash
python scripts/workflow.py create ../my-python \
  --layers core,generic,python,python-starter \
  --name "My Python Project" \
  --yes
```

完成后可由用户选择：

```bash
python scripts/workflow.py create ../my-python \
  --layers core,generic,python,python-starter \
  --git-init \
  --install-python-deps \
  --yes
```

`--git-init` 只运行 `git init -b main`，不 commit。`--install-python-deps` 运行 `uv sync`，需要本机已有 `uv`。

### 3.3 Unity

v4.0 不直接生成完整 Unity 工程。先由 Unity Hub 创建空 2D 项目，再运行：

```bash
python scripts/workflow.py attach <unity-project> \
  --layers core,generic,unity2d,unity2d-starter \
  --yes
```

对于已有内容的 Unity 项目，只选择：

```bash
python scripts/workflow.py attach <unity-project> \
  --layers core,generic,unity2d \
  --yes
```

第二种方式不注入 `GameBootstrap`、GameClock 或示例 gameplay 代码。Unity 工程必须存在：

```text
Assets/
ProjectSettings/ProjectVersion.txt
Packages/manifest.json
```

`unity2d` 会安装 `Assets/AgentWorkflow/Editor/` 下的独立静态审计工具，菜单入口为 `Tools > Agent Workflow > Workflow Audit`。

## 4. 装配现有项目

### 4.1 自动检测

```bash
python scripts/workflow.py attach <project> --dry-run --json
```

不带 `--layers` 时，装配器始终选择 `core,generic`，并按项目标记追加 `python` 和/或 `unity2d`。自动检测不会选择 starter layer。

### 4.2 显式选择

```bash
python scripts/workflow.py attach <project> \
  --layers core,generic,python --name "Existing Project" --yes
```

项目名默认使用目录名。已经装配的 v4.0 项目可以重复 `attach` 相同 layers/name，作为幂等检查；修改 layer 集合需要手工更新 `WORKFLOW_PROFILE.toml` 后走受控迁移。

### 4.3 安全合并

| Ownership | 首次装配 | 同步 |
| --- | --- | --- |
| `KIT_OWNED` | 不存在才写；不同内容阻断 | lock 哈希未变才更新 |
| `MANAGED_BLOCK` | 保留标记外内容 | 只更新标记内块 |
| `SEEDED` | 只补缺失文件 | 永不覆盖 |
| `MERGED_CONFIG` | JSON 只补缺失键 | 再次检查缺失键 |

现有 `AGENTS.md`、`README.md`、`.gitignore`、`.gitattributes` 可保留用户内容并追加托管块。已有 `AI_Context/*.md` 会作为用户文档保留，不用 seed 覆盖。

Unity `Packages/manifest.json`、依赖、配置、公共接口等属于 Protected Changes。发现缺失包时默认阻断并写 `AI_Context/WORKFLOW_CONFLICTS.md`；CEO 审阅后可显式追加：

```text
--accept-protected
```

## 5. Git 工作区与副作用

装配器检测到项目 Git 工作区有未提交修改时默认停止。CEO 确认目标范围后可以：

```bash
python scripts/workflow.py attach <project> \
  --layers core,generic,python \
  --allow-dirty \
  --dry-run
```

`--allow-dirty` 不降低写入安全规则；它只允许流程继续检查。目标文件仍受 ownership 和冲突规则保护。

默认不执行：

- `git init`
- 依赖安装或网络请求
- Unity Editor、Test Runner 或游戏启动
- commit、merge、push、tag、remote 修改

## 6. Profile 与 Lock

装配后检查：

```bash
python -c "from pathlib import Path; print(Path('AI_Context/WORKFLOW_PROFILE.toml').read_text(encoding='utf-8'))"
python -c "from pathlib import Path; print(Path('AI_Context/WORKFLOW_LOCK.toml').read_text(encoding='utf-8'))"
```

`WORKFLOW_PROFILE.toml`：

```toml
schema_version = 1
workflow_version = "v4.0"
name = "My Project"
layers = ["core", "generic", "python"]

[parameters]
project_slug = "my-project"
```

`WORKFLOW_LOCK.toml` 由工具维护，包含：

- kit 与 workflow 版本。
- ordered layer 和 `layer_versions`。
- Profile Hash。
- 每个托管文件的 owner、SHA-256、托管块 fragment hash 和来源 layer。

不要手工编辑 lock。Task Brief、Plan、Manifest 或 L0 mini 中的 Profile 身份必须与 lock 完全一致。

## 7. 状态、自检与升级

### 7.1 status

```bash
python scripts/workflow.py status .
python scripts/workflow.py status . --json
```

报告 clean、modified、missing、invalid 和“托管块外用户编辑”数量。该命令只读。

### 7.2 doctor

```bash
python scripts/workflow.py doctor .
python scripts/workflow.py doctor . --json
```

检查 profile/lock 一致性、托管文件哈希、必需上下文、task templates、`.agents/skills/` 数量和 Unity 标记。Python 项目未在工具配置中排除 `AI_Context/` 时给 WARN。

退出码：

- `0`：PASS 或只有 WARN。
- `1`：存在完整性错误或命令执行失败。
- `2`：用户输入、冲突、路径或受保护动作被阻断。

### 7.3 sync

先检查：

```bash
python scripts/workflow.py sync <project> \
  --from <agent-workflow-kit-root> \
  --check
```

确认后应用：

```bash
python scripts/workflow.py sync <project> \
  --from <agent-workflow-kit-root> \
  --apply
```

- `--check` 零写入。
- `KIT_OWNED` 当前 hash 与 lock 不一致时不覆盖。
- `MANAGED_BLOCK` 块内未变时可以更新，保留块外用户内容。
- 任一不可安全合并项会阻断整个 apply，并生成 `AI_Context/WORKFLOW_CONFLICTS.md`。
- `SEEDED` 项目文档不随 sync 更新。

## 8. 自定义 Profile

```bash
python scripts/workflow.py profile list
python scripts/workflow.py profile init ./profiles/team-stack --id team-stack
python scripts/workflow.py profile validate ./profiles/team-stack
```

从外部目录装配：

```bash
python scripts/workflow.py create <project> \
  --layers core,generic,team-stack \
  --profile-root ./profiles \
  --dry-run
```

Profile 是纯声明式 TOML，不支持任意 hook。schema、action 类型、ownership 和合并示例见 [PROJECT_PROFILES.md](PROJECT_PROFILES.md)。

## 9. 创建任务

从装配项目的 `AI_Context/TASKS/_templates/` 复制所需凭证到：

```text
AI_Context/TASKS/GD-YYYY-NNNN/
```

填写 `TASK_BRIEF.md` 时，从 lock 复制：

```text
Project Profile: core@4.0.0 + generic@4.0.0 + python@4.0.0
Profile Hash: sha256:...
```

Planner 的 `PLAN_vNN.md` 必须记录相同值。Secretary 更新 `AI_Context/PROJECT_BOARD.md`。

## 10. 生成上下文

Agent Planner 默认直接只读仓库，Secretary 可生成固定基线：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001
```

Chat Planner 需要具体源文件时：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --files src/app/domain/models.py
```

分轮补料：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --append --reason "确认调用契约" \
  --files src/app/interfaces/cli.py
```

`stage_context.py` 要求项目存在 v4.0 Profile/Lock，并在 Manifest 记录：

- Workflow Version
- Project Profile
- Profile Hash
- Base Commit / 非 Git 恢复时间
- Token、映射、SHA-256、排除项和 NEED_FILES 轮次索引

`FEED_DROP/` 与 `NEED_FILES/` 被 Git 忽略，不应提交。

## 11. 交接门禁

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

校验器会检查 Task Brief、Manifest、Plan 中的 Profile 身份与当前项目 lock 完全一致。v3.1 任务作为历史保留，但不能作为 v4.0 活跃交接通过。

Watchdog/archive 还会自动审计批准 Base Commit 到工作区的 Git Diff。非 Git 项目给 WARN，不能声称范围已机器验证。

## 12. L0 快速通道

L0 mini brief 必须包含：

```markdown
Task ID: GD-2026-0099 / Task Level: L0 / Workflow Version: v4.0 / Base Commit: <commit>
Project Profile: core@4.0.0 + generic@4.0.0
Profile Hash: sha256:...
目标与验收: WORKER_AUTOMATABLE / WORKER / TEST_RESULT / <命令> exit 0
文件边界: MODIFY `<path>`; FORBIDDEN `<path>`; Computer-Use Authorization: NONE
```

归档：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0099 --l0 --for archive
```

## 13. Unity 与 Computer-Use

- `UNITY_GUI_REQUIRED` 默认由 CEO 执行。
- Worker 只有 PLAN 和 APPROVAL_RECORD 同时写明以下三段式授权时才可操作原生 UI：

```text
AUTHORIZED: TARGET=<窗口/应用>; ACTIONS=<动作白名单>; SCOPE=<目录/场景范围>
```

- 截图只用于无法稳定文本断言的视觉结果，并记录 Visual Purpose / Visual Scenario / Visual Expected。
- `WORKER_AUTOMATABLE` 的主证据必须是命令、退出码、测试、Diff、Manifest、哈希或日志。
- Unity Editor 编译和 Test Runner 未实际运行时，证据只能写 `NOT RUN`。

## 14. FAQ

**装配器会修改全局技能目录吗？**

不会。技能进入项目 `.agents/skills/`。

**为什么项目已经装配后 `attach` 不换 layer？**

切换技术栈会改变 Profile Hash 与任务契约。手工修改 profile 后应创建新的受控迁移任务，而不要让重复 attach 静默替换。

**sync 能更新我改过的 AGENTS.md 吗？**

只改标记外内容时可以更新托管块；块内被修改会阻断。先审阅 `WORKFLOW_CONFLICTS.md`，解决后再 apply。

**为什么 Unity manifest 会阻断？**

包清单、ProjectSettings、渲染管线、公共接口和配置属于 Protected Changes。工具只显示缺失项，不替 CEO 批准依赖。

**v3.1 任务还能归档吗？**

历史目录可保留。若继续执行，请使用 v4.0 新任务包；迁移见 [MIGRATION_v3.1_to_v4.0.md](MIGRATION_v3.1_to_v4.0.md)。

**装配器会 commit 吗？**

不会。Git 初始化以外的 commit、merge、push、tag 和 remote 修改都需要 CEO 明确授权。
