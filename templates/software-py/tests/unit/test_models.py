"""领域模型单测：校验规则与状态机推进（纯规则，无 I/O）。"""

from __future__ import annotations

import pytest

from app.domain.errors import TaskValidationError
from app.domain.models import Task, TaskStatus


def _make(task_id: str = "GD-2026-0001", title: str = "示例任务", level: int = 1) -> Task:
    return Task(task_id=task_id, title=title, level=level)


@pytest.mark.parametrize(
    ("task_id", "title", "level"),
    [
        ("BAD-1", "x", 1),
        ("GD-26-01", "x", 1),
        ("gd-2026-0001", "x", 1),
        ("GD-2026-0001", "   ", 1),
        ("GD-2026-0001", "x", -1),
        ("GD-2026-0001", "x", 4),
    ],
)
def test_task_validation_rejects_bad_fields(task_id: str, title: str, level: int) -> None:
    with pytest.raises(TaskValidationError):
        Task(task_id=task_id, title=title, level=level)


def test_task_accepts_valid_fields() -> None:
    task = _make()
    assert task.status is TaskStatus.TRIAGED


def test_status_progression() -> None:
    assert TaskStatus.TRIAGED.next is TaskStatus.EXECUTING
    assert TaskStatus.EXECUTING.next is TaskStatus.VALIDATING
    assert TaskStatus.VALIDATING.next is TaskStatus.ARCHIVED


def test_archived_has_no_next() -> None:
    with pytest.raises(TaskValidationError):
        _ = TaskStatus.ARCHIVED.next
