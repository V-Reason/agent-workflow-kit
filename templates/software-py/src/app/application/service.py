"""应用层用例：任务看板服务（编排领域逻辑与端口，零 I/O）。

纪律：只依赖 domain 与 ports；不 import infra；
状态推进使用 dataclasses.replace 保持 Task 不可变语义。
"""

from __future__ import annotations

from dataclasses import replace

from app.application.ports import TaskRepository
from app.domain.errors import DomainError, TaskNotFoundError
from app.domain.models import Task, TaskStatus


class TaskService:
    """任务看板用例集合。"""

    def __init__(self, repository: TaskRepository) -> None:
        self._repository = repository

    def create_task(self, task_id: str, title: str, level: int) -> Task:
        """登记新任务；ID 冲突视为调用方错误。"""
        if self._repository.get(task_id) is not None:
            raise DomainError(f"task id already exists: {task_id!r}")
        task = Task(task_id=task_id, title=title, level=level)
        self._repository.save(task)
        return task

    def list_tasks(self) -> list[Task]:
        """按 ID 升序列出全部任务。"""
        return self._repository.list_all()

    def advance(self, task_id: str) -> TaskStatus:
        """沿最小闭环推进一格：TRIAGED -> EXECUTING -> VALIDATING -> ARCHIVED。"""
        task = self._require(task_id)
        next_status = task.status.next
        updated = replace(task, status=next_status)
        self._repository.save(updated)
        return next_status

    def remove_task(self, task_id: str) -> None:
        """删除任务；不存在则抛 TaskNotFoundError。"""
        if not self._repository.remove(task_id):
            raise TaskNotFoundError(task_id)

    def _require(self, task_id: str) -> Task:
        task = self._repository.get(task_id)
        if task is None:
            raise TaskNotFoundError(task_id)
        return task
