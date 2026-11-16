"""应用层单测：用例编排与错误路径（用内存仓库作端口测试替身）。"""

from __future__ import annotations

import pytest

from app.application.service import TaskService
from app.domain.errors import DomainError, TaskNotFoundError
from app.domain.models import TaskStatus
from app.infra.memory_repository import InMemoryTaskRepository


@pytest.fixture()
def service() -> TaskService:
    return TaskService(InMemoryTaskRepository())


def test_create_and_list_sorted(service: TaskService) -> None:
    service.create_task("GD-2026-0002", "任务B", 0)
    service.create_task("GD-2026-0001", "任务A", 1)
    tasks = service.list_tasks()
    assert [t.task_id for t in tasks] == ["GD-2026-0001", "GD-2026-0002"]


def test_duplicate_id_rejected(service: TaskService) -> None:
    service.create_task("GD-2026-0001", "第一次", 1)
    with pytest.raises(DomainError):
        service.create_task("GD-2026-0001", "第二次", 1)


def test_advance_full_cycle(service: TaskService) -> None:
    service.create_task("GD-2026-0001", "循环", 1)
    assert service.advance("GD-2026-0001") is TaskStatus.EXECUTING
    assert service.advance("GD-2026-0001") is TaskStatus.VALIDATING
    assert service.advance("GD-2026-0001") is TaskStatus.ARCHIVED
    with pytest.raises(DomainError):
        service.advance("GD-2026-0001")


def test_remove_missing_raises(service: TaskService) -> None:
    with pytest.raises(TaskNotFoundError):
        service.remove_task("GD-2026-9999")
