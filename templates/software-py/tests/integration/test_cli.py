"""集成测试：CLI 组合根端到端。

main() 每次调用都是一次独立的"进程语义"（默认新建仓库），
因此用 service 注入参数共享同一实例来验证完整链路。
"""

from __future__ import annotations

import pytest

from app.application.service import TaskService
from app.infra.memory_repository import InMemoryTaskRepository
from app.interfaces.cli import build_service, main


@pytest.fixture()
def service() -> TaskService:
    return TaskService(InMemoryTaskRepository())


def test_build_service_returns_configured_service() -> None:
    composed = build_service()
    assert isinstance(composed, TaskService)


def test_cli_full_flow(capsys: pytest.CaptureFixture[str], service: TaskService) -> None:
    assert main(["add", "GD-2026-0001", "首个任务", "--level", "2"], service=service) == 0
    out_first = capsys.readouterr().out
    assert "created GD-2026-0001 [TRIAGED] 首个任务" in out_first

    assert main(["list"], service=service) == 0
    listed = capsys.readouterr().out
    assert "GD-2026-0001  L2  TRIAGED  首个任务" in listed

    assert main(["advance", "GD-2026-0001"], service=service) == 0
    assert "GD-2026-0001 -> EXECUTING" in capsys.readouterr().out

    assert main(["remove", "GD-2026-0001"], service=service) == 0
    assert "removed GD-2026-0001" in capsys.readouterr().out


def test_cli_domain_error_exit_code(
    capsys: pytest.CaptureFixture[str], service: TaskService
) -> None:
    assert main(["add", "GD-2026-0001", "占位", "--level", "1"], service=service) == 0
    capsys.readouterr()
    assert main(["add", "GD-2026-0001", "重复", "--level", "1"], service=service) == 1
    err = capsys.readouterr().err
    assert "already exists" in err


def test_cli_invalid_id_rejected(
    capsys: pytest.CaptureFixture[str], service: TaskService
) -> None:
    assert main(["add", "BAD-ID", "非法编号", "--level", "1"], service=service) == 1
    err = capsys.readouterr().err
    assert "GD-YYYY-NNNN" in err
