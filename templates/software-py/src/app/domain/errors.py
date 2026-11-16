"""领域错误基类与具体错误。

纪律：所有业务规则违反必须抛出 DomainError 及其子类；
严禁空 catch / 吞异常；错误信息必须面向定位（含参数值与约束描述）。
"""

from __future__ import annotations


class DomainError(Exception):
    """领域层错误基类。interfaces 层统一捕获并转换为用户可读输出。"""


class TaskValidationError(DomainError):
    """实体字段校验失败。"""


class TaskNotFoundError(DomainError):
    """按 ID 查找任务失败。"""

    def __init__(self, task_id: str) -> None:
        super().__init__(f"task not found: {task_id!r}")
        self.task_id = task_id
