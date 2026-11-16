# MODULE_MAP — 模块、目录与职责索引（L2 模块级引用项）

> 每个任务验收后由取材员/Planner 核对本表与工程漂移；漂移项标 STALE 并回写修正。

| 路径 | 职责 | 公共接口 | 备注 |
| --- | --- | --- | --- |
| `src/app/domain/errors.py` | 领域错误基类与子类 | `DomainError`、`TaskValidationError`、`TaskNotFoundError` | 全部业务错误继承基类 |
| `src/app/domain/models.py` | 任务实体与状态机 | `Task`、`TaskStatus`（含 `.next`） | frozen dataclass，校验在 `__post_init__` |
| `src/app/application/ports.py` | 仓库端口协议 | `TaskRepository` | infra 提供实现 |
| `src/app/application/service.py` | 任务看板用例 | `TaskService`（create/list/advance/remove） | 只依赖 domain + ports |
| `src/app/infra/memory_repository.py` | 内存仓库实现 | `InMemoryTaskRepository` | 非线程安全；生产替换点 |
| `src/app/interfaces/cli.py` | CLI 组合根与命令 | `main(argv)`、`build_service()` | 退出码：0 成功 / 1 领域错误 |
| `tests/unit/` | 领域与应用层快测 | — | 无 I/O |
| `tests/integration/` | CLI 端到端测试 | — | 真实组合根装配 |
| `scripts/validate_handover.py` | 交接包校验器 | CLI | 与套件同源副本 |

## 漂移记录

| 日期 | 漂移内容 | 处理 |
| --- | --- | --- |
| <日期> | <漂移描述> | <已修正/待修正> |

---
最后核验日期：2026-11-16｜分支：main｜维护人：<项目 Owner>
