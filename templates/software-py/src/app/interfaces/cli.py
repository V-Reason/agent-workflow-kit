"""接口层：命令行入口（组合根——装配具体实现并注入应用层）。

纪律：只做输入输出转换与异常到退出码的映射；
替换存储实现时只改 build_service()，不动 application 与 domain。
main(argv, service=...) 的注入参数仅供测试与嵌入调用方使用。
"""

from __future__ import annotations

import argparse
import sys

from app.application.service import TaskService
from app.domain.errors import DomainError
from app.infra.memory_repository import InMemoryTaskRepository


def build_service() -> TaskService:
    """组合根：把 infra 实现注入应用层；替换存储时只改这里。"""
    return TaskService(InMemoryTaskRepository())


def main(argv: list[str] | None = None, service: TaskService | None = None) -> int:
    parser = argparse.ArgumentParser(prog="app", description="任务看板最小示例")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="登记新任务")
    p_add.add_argument("task_id", help="任务编号，格式 GD-YYYY-NNNN")
    p_add.add_argument("title", help="任务标题")
    p_add.add_argument("--level", type=int, default=1, help="复杂度 0-3，对齐 L0-L3")

    sub.add_parser("list", help="按 ID 升序列出全部任务")

    p_advance = sub.add_parser("advance", help="沿最小闭环推进任务状态一格")
    p_advance.add_argument("task_id", help="任务编号")

    p_remove = sub.add_parser("remove", help="删除任务")
    p_remove.add_argument("task_id", help="任务编号")

    args = parser.parse_args(argv)
    svc = service if service is not None else build_service()

    try:
        if args.command == "add":
            task = svc.create_task(args.task_id, args.title, args.level)
            print(f"created {task.task_id} [{task.status.value}] {task.title}")
        elif args.command == "list":
            for task in svc.list_tasks():
                print(f"{task.task_id}  L{task.level}  {task.status.value}  {task.title}")
        elif args.command == "advance":
            status = svc.advance(args.task_id)
            print(f"{args.task_id} -> {status.value}")
        elif args.command == "remove":
            svc.remove_task(args.task_id)
            print(f"removed {args.task_id}")
    except DomainError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
