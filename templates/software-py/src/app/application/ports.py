"""应用层端口：仓库协议（依赖倒置的关键接缝）。

纪律：application 只 import domain 与本模块；
infra 提供实现，interfaces（组合根）负责装配注入。
为单一实现新增端口语义前先问：三法则是否满足？
"""

from __future__ import annotations

from typing import Protocol

from app.domain.models import Task


class TaskRepository(Protocol):
    """任务仓库协议。实现必须保证 get/remove 对不存在 ID 的行为与本协议一致。"""

    def save(self, task: Task) -> None:
        """按 task_id 幂等写入（upsert）。"""
        ...

    def get(self, task_id: str) -> Task | None:
        """按 ID 读取；不存在返回 None。"""
        ...

    def list_all(self) -> list[Task]:
        """返回全部任务；实现保证按 task_id 升序。"""
        ...

    def remove(self, task_id: str) -> bool:
        """按 ID 删除；存在返回 True，不存在返回 False。"""
        ...
