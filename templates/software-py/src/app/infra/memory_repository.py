"""基础设施层：内存任务仓库（TaskRepository 协议的默认实现）。

注意：非线程安全、仅进程生命周期内有效；
替换为 SQLite / PostgreSQL 实现时，只新增本层文件并修改组合根，不动应用层。
"""

from __future__ import annotations

from app.domain.models import Task


class InMemoryTaskRepository:
    """dict 存储的最小实现，满足 TaskRepository 协议。"""

    def __init__(self) -> None:
        self._tasks: dict[str, Task] = {}

    def save(self, task: Task) -> None:
        self._tasks[task.task_id] = task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list_all(self) -> list[Task]:
        return [self._tasks[key] for key in sorted(self._tasks)]

    def remove(self, task_id: str) -> bool:
        return self._tasks.pop(task_id, None) is not None
