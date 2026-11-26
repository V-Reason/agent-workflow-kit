# Agent Workflow Kit v3.1 → v4.0 迁移说明

v4.0 全面切换任务协议到 `Workflow Version: v4.0`。已有 v3.1 任务目录不会自动重写，也不能继续作为 v4.0 活跃任务交接；需要继续执行时，请保留历史凭证并创建新的 v4.0 任务包。

## 主要变化

| v3.1 | v4.0 |
| --- | --- |
| 手工复制模板、手工合并 Unity 文件 | `scripts/workflow.py` 向导或子命令 |
| Python/Unity 模板各带一份脚本副本 | `core` profile 从 canonical 源装配脚本和技能 |
| 无项目级装配状态 | `WORKFLOW_PROFILE.toml` + `WORKFLOW_LOCK.toml` |
| 任务只记录 Workflow Version / Base Commit | 增加 Project Profile、layer 版本与 Profile Hash |
| 没有统一升级检查 | `status`、`doctor`、`sync --check/--apply` |
| Unity 受保护配置依赖人工纪律 | JSON 缺失键合并需专项 `--accept-protected` |
| 现有项目冲突靠手工判断 | 托管块、hash、seed 和冲突报告 |

## 现有 v3.1 项目

1. 在套件目录先查看将发生的变更：

```bash
python scripts/workflow.py attach <project-root> \
  --layers core,generic,python --dry-run --json
```

Unity：

```bash
python scripts/workflow.py attach <unity-project-root> \
  --layers core,generic,unity2d --dry-run --json
```

2. 如果 Git 工作区有未提交修改，先判断这些修改是否属于本次目标文件。默认会阻断；确需在脏工作区装配时由 CEO 明确追加 `--allow-dirty`。

3. Unity 项目若缺少必需包，先审阅差异，再由 CEO 决定是否追加 `--accept-protected`。装配器不会静默覆盖已有包版本。

4. 确认计划后重跑并去掉 `--dry-run`，或者去掉 `--yes` 使用交互确认。

5. 运行：

```bash
python scripts/workflow.py status <project-root>
python scripts/workflow.py doctor <project-root>
```

6. 填写生成的 `AI_Context` 文档。已有同名 `AI_Context` 文档会保留，不会用 seed 覆盖。

## 现有 v3.1 任务

- 不原地修改已批准、执行中或已归档的 v3.1 凭证。
- 继续同一需求时，创建新的 `GD-YYYY-NNNN` 目录，并使用装配后的 v4.0 task templates。
- TASK_BRIEF、PLAN 和 Context Manifest 必须从 `WORKFLOW_LOCK.toml` 复制 `Project Profile` 与 `Profile Hash`。
- v3.1 任务可保留在仓库中作为历史；v4.0 校验器会将其视为旧协议并拒绝作为活跃交接。

## 升级已装配的 v4.0 项目

从套件目录执行：

```bash
python scripts/workflow.py sync <project-root> --from <agent-workflow-kit-root> --check
python scripts/workflow.py sync <project-root> --from <agent-workflow-kit-root> --apply
```

安全规则：

- `KIT_OWNED` 文件只有在当前哈希仍等于 lock 时才更新。
- `MANAGED_BLOCK` 只更新标记内内容，保留标记外用户文本。
- 用户修改过托管块或托管的普通文件时，`sync` 阻断并生成 `AI_Context/WORKFLOW_CONFLICTS.md`。
- `SEEDED` 文档永不覆盖。
- 不自动执行 Git、依赖安装、Unity 或推荐门禁。

## 自定义 Profile 迁移

团队若曾手工维护第三套模板，建议将其改造成 `profiles/<id>/profile.toml`：

1. 用 `profile init` 创建骨架。
2. 把模板文件移动到 `files/`。
3. 对 AGENTS、README、`.gitignore` 等可共存内容改用 `managed_block`。
4. 对不可覆盖的既有配置使用 `SEEDED` 或 `json_merge` + `protected`。
5. 运行 `profile validate`，再用临时目录执行 `create --dry-run`。

完整 schema 见 [PROJECT_PROFILES.md](PROJECT_PROFILES.md)。

## 历史迁移文档

v3.0 → v3.1 的旧迁移记录仍保留在 [MIGRATION_v3.0_to_v3.1.md](MIGRATION_v3.0_to_v3.1.md)，仅供历史追溯。
