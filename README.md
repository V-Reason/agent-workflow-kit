# Agent Workflow Kit v3.0

面向小型研发团队的本地 Super-Kit：由 CEO 掌控需求、批准和验收，四个正交 AI 角色分别管理运营、架构、施工和独立监督。

```text
CEO
 ├─ Secretary：进度、成本、看板、FEED_DROP 备菜
 ├─ Planner：架构、技术取舍、任务书、NEED_FILES
 ├─ Worker：批准范围施工与真实验证
 └─ Watchdog：独立门禁、验收事实、软故障复盘
```

核心变化：

- 不再使用手工拼贴 Markdown 上下文，改为 `stage_context.py` 复制真实源文件到 `FEED_DROP/`。
- 所有任务共用 `00_CONTEXT_MANIFEST.md` + `AI_Context/PROJECT_BOARD.md`。
- Chat 拖拽和 Agent 直读共用同一物理入口。
- 标准 L1/L2 必须经 CEO 批准并由独立 Watchdog 验证；L0 支持 CEO 直派 Worker。
- 8 个技能权责正交；施工期只加载 `worker-engine`，不叠加顾问。

## 目录

| 路径 | 作用 |
| --- | --- |
| `AGENTS.md` | v3.0 唯一工作流宪法、角色矩阵、状态机和模型路由 |
| `docs/DESIGN_CHARTER.md` | 设计总纲与架构边界 |
| `docs/USAGE.md` | 从安装到归档的操作手册 |
| `scripts/stage_context.py` | 生成 flat FEED_DROP、Manifest、Token 预算 |
| `scripts/validate_handover.py` | planner / worker / watchdog / archive 结构门禁 |
| `skills/` | Secretary、Planner、Worker、Watchdog、写作插件、3 个只读顾问 |
| `templates/software-py/` | Python 四层架构模板 |
| `templates/unity2d/` | Unity 2D asmdef 骨架与审计门禁 |

## 快速开始

1. 阅读 [AGENTS.md](AGENTS.md) 和 [DESIGN_CHARTER.md](docs/DESIGN_CHARTER.md)。
2. 复制一个模板到实际项目，填写 `AI_Context/PROJECT_BOARD.md`、总览、架构和模块地图。
3. 创建任务目录：

```bash
mkdir AI_Context/TASKS/GD-2026-0001
```

4. Secretary 生成真实文件投喂箱：

```bash
python scripts/stage_context.py AI_Context/TASKS/GD-2026-0001 \
  --files src/app/example.py
```

5. Chat 模式将 `FEED_DROP/` 拖给 Planner；Agent 模式让 Planner 从 Manifest 起步并保留只读全仓检索。
6. CEO 批准 `PLAN_vNN.md` 和 `APPROVAL_RECORD.md` 后交 Worker。
7. L1/L2 由独立 Watchdog 实跑门禁，CEO 填最终验收决定。

## 门禁

```bash
python -m unittest discover -s tests -v

python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for planner
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for worker
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for watchdog
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0001 --for archive
```

L0：

```bash
python scripts/validate_handover.py AI_Context/TASKS/GD-2026-0009 --l0 --for archive
```

v3 不再接受旧模式枚举；旧调用会收到迁移提示。

## 模板隔离

- 根、Python、Unity `.gitignore` 都忽略 `AI_Context/TASKS/**/FEED_DROP/`。
- Python 的 Ruff、mypy、pytest 显式排除 `AI_Context/`。
- Unity 的 `RunBatchAudit` 检查项目看板、两个 v3 脚本和程序集边界。
- Agent 不修改 Unity 序列化资产或 `.xlsx`；需要时由 CEO 按手工清单操作。

## 安全边界

- `.env`、`.env.*`（`.env.example` 除外）、私钥、凭据、日志和本地绝对路径不得入库。
- 默认无网络依赖、无 remote、无 push。
- 任何任务若需越出批准文件、依赖、配置、资产或额度，必须停止并请求 CEO 决策。

详细流程、常见问题和运维节奏见 [docs/USAGE.md](docs/USAGE.md)。

## License

本项目采用 [MIT License](LICENSE)。
