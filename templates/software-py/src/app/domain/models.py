"""领域模型：任务实体与状态（纯数据与纯规则，零 I/O、零外部依赖）。

纪律：本模块不得 import 任何框架、数据库或网络库；
一切副作用（存储、I/O）都在 infra 层，编排都在 application 层。
"""

from __future__ import annotations

import enum
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.errors import TaskValidationError

# 与交接包目录命名一致（AGENTS.md 第 6 节）
TASK_ID_PATTERN = re.compile(r"^GD-\d{4}-\d{4}$")


class TaskStatus(enum.Enum):
    """最小闭环状态；完整状态机见 AGENTS.md 第 2 节。"""

    TRIAGED = "TRIAGED"
    EXECUTING = "EXECUTING"
    VALIDATING = "VALIDATING"
    ARCHIVED = "ARCHIVED"

    @property
    def next(self) -> "TaskStatus":
        """返回最小闭环中的下一状态；ARCHIVED 再推进视为错误。"""
        order: list[TaskStatus] = [
            TaskStatus.TRIAGED,
            TaskStatus.EXECUTING,
            TaskStatus.VALIDATING,
            TaskStatus.ARCHIVED,
        ]
        idx = order.index(self)
        if idx == len(order) - 1:
            raise TaskValidationError(f"task already archived: {self.value}")
        return order[idx + 1]


@dataclass(frozen=True, slots=True)
class Task:
    """不可变任务实体；跨层传递保持值语义，状态推进用 dataclasses.replace。"""

    task_id: str
    title: str
    level: int
    status: TaskStatus = TaskStatus.TRIAGED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not TASK_ID_PATTERN.match(self.task_id):
            raise TaskValidationError(
                f"task_id 必须符合 GD-YYYY-NNNN，实际为 {self.task_id!r}"
            )
        if not self.title.strip():
            raise TaskValidationError("title 不能为空字符串")
        if not 0 <= self.level <= 3:
            raise TaskValidationError(f"level 必须在 0-3（对齐 L0-L3），实际为 {self.level}")
