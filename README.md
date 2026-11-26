# Agent Workflow Kit v4.0

面向小型研发团队的本地 AI 协作工作流：CEO 掌管需求、批准与最终验收；Secretary、Planner、Worker、Watchdog 四个角色权责正交。v4.0 的重点是**一键创建/装配**与**声明式 Project Profile**。

## 一键开始

在套件目录运行：

```bash
python scripts/workflow.py
```

向导会询问项目路径、项目类型和可选副作用，先展示装配计划，再执行写入。所有装配文件都进入目标项目，不修改用户全局技能目录。

非交互示例：

```bash
# 新通用项目，不生成业务代码
python scripts/workflow.py create ../my-project \
  --layers core,generic --name "My Project" --yes

# 新 Python starter
python scripts/workflow.py create ../my-python \
  --layers core,generic,python,python-starter --yes

# 现有 Python 项目
python scripts/workflow.py attach ../existing-python \
  --layers core,generic,python --yes

# 现有 Unity 项目；不注入示例 gameplay 代码
python scripts/workflow.py attach ../my-game \
  --layers core,generic,unity2d --yes
```

新建 Unity 工程仍由 Unity Hub 完成。随后对空工程运行 `attach`，或使用向导的 Unity 选项；v4.0 不伪造 `ProjectSettings`。

## 装配后

目标项目会得到：

- `AGENTS.md` 内可安全更新的 v4.0 托管规则块。
- `AI_Context/WORKFLOW_PROFILE.toml`：项目名、ordered layers 和参数。
- `AI_Context/WORKFLOW_LOCK.toml`：版本、Profile 哈希、文件所有权和 SHA-256。
- `AI_Context/` 通用上下文、项目看板和 v4.0 任务凭证。
- `scripts/stage_context.py`、`scripts/validate_handover.py` 与 `scripts/workflow.py`。
- `.agents/skills/` 下的 8 个角色技能。

日常命令：

```bash
python scripts/workflow.py status .
python scripts/workflow.py doctor .
python scripts/workflow.py sync . --from <agent-workflow-kit-root> --check
python scripts/workflow.py sync . --from <agent-workflow-kit-root> --apply
```

`status` 和 `doctor` 只读。`sync --check` 零写入；`sync --apply` 只更新未被用户改动的托管内容。用户已修改的托管文件会阻断同步并生成 `AI_Context/WORKFLOW_CONFLICTS.md`。

## 声明式 Profile

内置 layer：

| Layer | 用途 |
| --- | --- |
| `core` | 工作流规则、脚本、技能、任务模板、通用上下文 |
| `generic` | 语言无关通用项目骨架 |
| `python` | 现有 Python 项目适配 |
| `python-starter` | 可选 Python 四层 starter |
| `unity2d` | 现有 Unity 项目适配和静态审计 |
| `unity2d-starter` | Unity Hub 空项目上的最小 asmdef/组合根示例 |

Profile 使用 TOML 声明，不允许执行 profile 自带代码。团队可以新增 layer，或通过 `--profile-root` 从外部目录加载：

```bash
python scripts/workflow.py profile list
python scripts/workflow.py profile init ./profiles/team-stack --id team-stack
python scripts/workflow.py profile validate ./profiles/team-stack
```

详细 schema、合并策略和示例见 [docs/PROJECT_PROFILES.md](docs/PROJECT_PROFILES.md)。

## 安全边界

- 默认只写项目文件并做离线自检；Git 初始化和 `uv sync` 需要显式选择。
- 现有业务文件和受保护配置不静默覆盖；Unity `Packages/manifest.json` 的缺失依赖需要 `--accept-protected`。
- 拒绝路径穿越、符号链接逃逸、敏感文件、损坏托管标记和不可判定冲突。
- Git commit、merge、push、tag、reset 仍须 CEO 明确授权；套件不默认联网、不 push。
- Unity Editor、游戏、Inspector、Test Runner 与最终视觉观察默认由 CEO 执行。

## 任务工作流

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 --files src/app/example.py
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

v4.0 任务必须记录 Project Profile layer 版本和 Profile Hash；Watchdog/archive 会把任务哈希与项目锁文件比对。v3.1 任务不自动迁移，见 [docs/MIGRATION_v3.1_to_v4.0.md](docs/MIGRATION_v3.1_to_v4.0.md)。

## 目录

| 路径 | 作用 |
| --- | --- |
| `AGENTS.md` | v4.0 工作流宪法、角色、状态机、路由和红线 |
| `docs/DESIGN_CHARTER.md` | 设计与需求总纲 |
| `docs/USAGE.md` | 创建、装配、任务、验收和同步手册 |
| `docs/PROJECT_PROFILES.md` | 声明式 Profile 规范 |
| `scripts/workflow.py` | 创建、装配、状态、自检、同步和 profile 工具 |
| `profiles/` | 内置可组合 layer 及托管块/seed 资源 |
| `scripts/stage_context.py` | FEED_DROP、NEED_FILES、Manifest 与 Token |
| `scripts/validate_handover.py` | v4.0 交接、证据、Profile 和 Git Diff 门禁 |
| `skills/` | 8 个正交角色技能 |
| `templates/` | Python 与 Unity starter 的业务骨架资源 |

## 验证

```bash
python -m unittest discover -s tests -v
```

结构校验不能替代编译、测试、Unity 审计和 CEO 验收。

## License

[MIT License](LICENSE)
