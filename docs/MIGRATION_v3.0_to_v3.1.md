# Agent Workflow Kit v3.0 → v3.1 迁移说明

v3.1 全面切换，不自动读取或升级 v3.0 任务包。历史任务如需再次审阅，应保留原目录并从新任务包重建。

## 行为变化

| v3.0 | v3.1 |
| --- | --- |
| `File Scope` 精确文件白名单 | `Write Boundaries + Forbidden + Read Policy + Protected Changes` |
| Worker 只改预列文件 | Worker 非敏感全仓读取，在批准边界内自动发现并修改 |
| `--append` 合并进 `FEED_DROP` | `--append --reason ...` 创建 `NEED_FILES/ROUND_NN/`，原基线不变 |
| FEED_DROP 映射只有 Token | 基线与轮次均记录 SHA-256；轮次 append-only |
| AC 只要求文本 | AC 必须声明 Class、Executor、Criterion、Primary Evidence |
| V4 可用截图/录屏 | 机器项不得以视觉证据为主；视觉项记录目的、场景、期望 |
| Unity GUI 边界模糊 | GUI 默认由 CEO 执行；Worker 仅凭 Computer-Use 专项授权 |
| 范围检查偏人工 | watchdog/archive 自动审计批准 Base Commit 到工作区的 Git Diff |

## 现有任务处理

1. 不原地修改已归档的 v3.0 凭证。
2. 需要继续执行时，创建新 Task ID 或经 CEO 明确批准重建任务目录。
3. 用 v3.1 模板重新生成 TASK_BRIEF、PLAN、APPROVAL_RECORD、执行报告与 ACCEPTANCE。
4. 运行：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-YYYY-NNNN
python scripts/validate_handover.py AI_Context/TASKS/GD-YYYY-NNNN --for planner
```

5. 如果任务已存在 v3.0 `NEED_FILES` 平铺目录，不要直接运行新 `--append`；先核对文件、目标版本和审计因果链，再决定是否新建任务。

## `--append` 迁移

旧命令：

```text
stage_context.py <task> --append --files <extra>
```

旧行为会重建 `FEED_DROP` 并合并旧清单。v3.1 必须写明原因：

```bash
python scripts/stage_context.py <task> \
  --append --reason "本轮解决的具体未知项" \
  --files <extra>
```

输出为下一个 `NEED_FILES/ROUND_NN/`。已有轮次后不能重建基线；需要新基线时新建任务。

## 非 Git 任务

v3.1 仍支持无 Git 的可恢复时间基线，但 `watchdog/archive` 会给出 `Diff 未自动核验` WARN。Watchdog 与 CEO 必须补充分支状态、文件清单、Diff 或等价证据，不能把 WARN 当作已验证。
