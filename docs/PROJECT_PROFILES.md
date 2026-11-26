# Project Profile v4.0 规范

Project Profile 是纯声明式的项目装配单元。Profile 只描述文件来源、目标路径、变量、检测条件、必需路径和合并方式，不执行 profile 自带代码。

## 目录结构

```text
profiles/<layer-id>/
  profile.toml
  blocks/              # AGENTS/.gitignore 等托管块来源
  files/               # seed 文件或项目资产
```

内置 profile 位于仓库 `profiles/`。团队 profile 可通过 `--profile-root <dir>` 加载；该参数可重复使用，后加载的同 ID profile 会替换先前版本。

## 最小示例

```toml
schema_version = 1
id = "team-stack"
version = "1.0.0"
display_name = "Team Stack"
description = "团队内部声明式装配"
requires = ["core"]
conflicts = []
required_paths = ["TEAM_STACK.md"]
recommended_gates = ["python scripts/workflow.py doctor ."]

[detection]
all_paths = ["package.json"]
any_paths = []

[[actions]]
type = "managed_block"
source = "blocks/agents.md"
target = "AGENTS.md"
block_id = "team-stack"

[[actions]]
type = "copy_file"
source = "files/TEAM_STACK.md"
target = "TEAM_STACK.md"
ownership = "SEEDED"
```

## 元数据

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `schema_version` | 是 | 固定为 `1` |
| `id` | 是 | 小写字母开头，只含 `a-z0-9-` |
| `version` | 是 | layer 版本，写入 lock 和任务 Profile 身份 |
| `display_name` | 否 | 向导和 `profile list` 的显示名 |
| `description` | 否 | 一句话职责 |
| `requires` | 否 | 依赖 layer；装配器自动按依赖顺序展开 |
| `conflicts` | 否 | 不允许同时出现的 layer |
| `create_only` | 否 | `true` 时只允许 `create`，用于 starter layer |
| `required_paths` | 否 | 装配完成前必须存在的文件或目录 |
| `recommended_gates` | 否 | 展示给 Planner/Worker 的建议门禁，不会自动执行 |

## 自动检测

```toml
[detection]
all_paths = ["Assets", "ProjectSettings/ProjectVersion.txt", "Packages/manifest.json"]
any_paths = []
```

- `all_paths` 全部存在才算匹配。
- `any_paths` 至少存在一项才算匹配。
- 两个字段都为空表示通用 profile。
- 显式 `attach` 所选技术 profile 必须匹配检测；`create` Python starter 可以在空目录先创建。
- Unity 项目始终要求 `Assets/`、`ProjectSettings/ProjectVersion.txt` 与 `Packages/manifest.json`。

### Layer 顺序

`core` 自动置于最前。依赖先于当前 layer 装配；命令行 requested order 用于同层无依赖项。重复 ID 会去重，循环依赖和冲突直接失败。

## Actions

### `copy_file`

```toml
[[actions]]
type = "copy_file"
source = "files/pyproject.toml"
target = "pyproject.toml"
ownership = "SEEDED"
```

`source` 普通路径相对 profile 根目录；`kit:<path>` 指向套件根目录。目标必须是项目内相对路径。

### `copy_tree`

```toml
[[actions]]
type = "copy_tree"
source = "files/src"
target = "src"
ownership = "SEEDED"
exclude = ["__pycache__", "*.pyc"]
```

递归复制普通文件，并按文件名、相对路径或路径段排除。符号链接拒绝。目标已有文件按 ownership 策略处理。

### `managed_block`

```toml
[[actions]]
type = "managed_block"
source = "blocks/agents.md"
target = "AGENTS.md"
block_id = "team-stack"
```

Markdown 使用：

```text
<!-- BEGIN AGENT_WORKFLOW_KIT:<layer>:<block_id> -->
...
<!-- END AGENT_WORKFLOW_KIT:<layer>:<block_id> -->
```

其他文件使用 `#` 注释标记。标记外用户内容保留；标记缺失、重复、顺序错误或块内被修改会阻断同步。换行统一为 LF。

### `json_merge`

```toml
[[actions]]
type = "json_merge"
source = "files/Packages/manifest.json"
target = "Packages/manifest.json"
ownership = "MERGED_CONFIG"
protected = true
```

只添加缺失键，不覆盖已有值。`protected = true` 时，装配或同步必须显式提供 `--accept-protected`；否则只生成冲突报告，不写任何托管变更。

## Ownership

| 类型 | 首次装配 | `sync` 行为 |
| --- | --- | --- |
| `KIT_OWNED` | 目标不存在则写入；不同内容阻断 | 当前哈希等于 lock 时更新；用户修改则阻断 |
| `MANAGED_BLOCK` | 保留标记外内容并插入/更新块 | 块内未修改时更新；只改块外时可安全更新 |
| `SEEDED` | 目标不存在才写入 | 永不覆盖 |
| `MERGED_CONFIG` | 只补缺失配置；可能要求保护性确认 | 继续只补缺失配置并提示差异 |

## 模板变量

内置变量：

- `project_name`
- `project_slug`
- `python_package`

自定义变量通过 `--variable key=value` 提供。profile 文本中出现未提供变量时装配失败。

## 项目内 Profile 与 Lock

装配生成：

```text
AI_Context/WORKFLOW_PROFILE.toml
AI_Context/WORKFLOW_LOCK.toml
```

`WORKFLOW_PROFILE.toml` 是项目声明的 layer 与参数；`WORKFLOW_LOCK.toml` 是机器生成的版本、Profile Hash、文件所有权与 SHA-256。不要手工伪造 lock。

任务 Manifest、TASK_BRIEF 与 PLAN 必须记录：

```text
Project Profile: core@4.0.0 + generic@4.0.0
Profile Hash: sha256:...
```

值从 lock 原样复制。校验器会将其与项目锁文件比对。

## 安全与禁止项

- Profile 不能执行任意 Python/shell hook。
- 不能使用绝对目标、`..`、符号链接 source 或项目外目标。
- `.env`、私钥、credential/secret 文件不得作为 profile source。
- 同一文件不能由多个 `copy_file`/`copy_tree` action 写入不同内容；需要叠加文本时使用不同 marker 的 `managed_block`。
- 不允许 profile 自动 commit、push、联网、启动 Unity 或运行推荐门禁。
- `sync` 遇任何不可安全合并的差异时不应用部分结果。
