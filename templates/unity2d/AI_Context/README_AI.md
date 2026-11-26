# README_AI — v3.1 Unity 项目上下文入口

Secretary 准备基线，Planner 从 `FEED_DROP/` 与 `00_CONTEXT_MANIFEST.md` 开始分析，Worker 在批准 Write Boundaries 内自主发现和施工，Watchdog 独立跑编译、测试、审计和风险验证。

## 标准流程

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --files Assets/Scripts/Core/GameClock.cs
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
```

## 加载规则

1. L1：`PROJECT_OVERVIEW`、`CODING_STANDARDS`、`BUILD_AND_TEST`。
2. L2：`PROJECT_BOARD`、`ARCHITECTURE`、`MODULE_MAP`、`DEPENDENCIES`。
3. L3：任务真实脚本、asmdef、只读资产引用和近期 Git 摘要。
4. `.shader/.hlsl/.cginc/.uxml/.uss/.asmdef` 在 chat-safe 模式下使用 `.txt` 安全名。
5. `FEED_DROP/` 与 `NEED_FILES/` 被 Git 忽略，绝不直接拖入 Unity 编译。
6. Agent Planner 默认只读全仓，不产生普通 `NEED_FILES`；Chat Planner 缺文件时用 `--append --reason` 分轮补料。

## 项目文件

| 文件 | 内容 |
| --- | --- |
| `PROJECT_BOARD.md` | 待 CEO 事项与任务召回索引 |
| `PROJECT_OVERVIEW.md` | Unity 版本、平台、PPU、管线 |
| `ARCHITECTURE.md` | asmdef、生命周期和组合根 |
| `MODULE_MAP.md` | 程序集、类、职责 |
| `DEPENDENCIES.md` | Unity 包与插件 |
| `BUILD_AND_TEST.md` | 编译、测试、RunBatchAudit、证据 |
| `CODING_STANDARDS.md` | C#、GC、资源与资产规则 |
| `KNOWN_ISSUES.md` | 引擎与资产风险 |
| `DECISION_LOG.md` | 架构决策 |
| `METRICS.md` | 六项运营指标 |
| `TASKS/GD-YYYY-NNNN/` | v3.1 任务凭证 |

## 资产边界

`FEED_DROP` 可复制序列化资产供阅读，但 Agent 不修改 `.prefab / .unity / .asset / .meta / .xlsx`。
Unity Editor、游戏启动、Inspector 与最终视觉观察默认由 CEO 执行；Worker 只有获得 Computer-Use 专项授权才可使用原生 UI。
验收后的上下文回写由 Secretary 起草，CEO 审阅合入。
