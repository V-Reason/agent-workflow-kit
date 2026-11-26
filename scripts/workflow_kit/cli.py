"""Command-line and interactive wizard for Agent Workflow Kit v4.0."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from . import KIT_VERSION, PROFILE_SCHEMA_VERSION, WORKFLOW_VERSION
from .assembly import AssemblyResult, assemble_project, write_conflict_report
from .errors import DoctorError, UsageError, WorkflowError
from .lockfile import PROFILE_PATH, read_lock, read_profile
from .profile import discover_profiles, load_profile
from .status import doctor_project, project_status


def _kit_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _split_layers(values: list[str] | None) -> list[str]:
    if not values:
        return []
    result: list[str] = []
    for value in values:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return result


def _parse_variables(values: list[str] | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for item in values or []:
        if "=" not in item:
            raise UsageError(f"--variable 需要 key=value，收到：{item}")
        key, value = item.split("=", 1)
        key = key.strip()
        if not key or not key.replace("_", "").isalnum():
            raise UsageError(f"变量名无效：{key!r}")
        result[key] = value
    return result


def _emit(payload: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    if payload.get("profiles"):
        print("可用 Project Profiles：")
        for profile in payload["profiles"]:
            required = f"；requires={', '.join(profile['requires'])}" if profile["requires"] else ""
            print(
                f"  - {profile['id']}@{profile['version']} "
                f"{profile['display_name']}{required}"
            )
        return
    if "counts" in payload:
        print(f"Workflow {payload['workflow_version']} / {payload['status']}")
        print(f"项目：{payload['project_name']}")
        print("装配层：" + ", ".join(payload.get("layer_versions", payload["layers"])))
        counts = payload["counts"]
        print(
            "文件状态："
            f"clean={counts['clean']} modified={counts['modified']} "
            f"missing={counts['missing']} invalid={counts['invalid']}"
        )
        for item in payload["files"]:
            if item["state"] != "clean":
                print(f"  - {item['state']}: {item['path']}")
        return
    if "errors" in payload:
        print(f"Workflow doctor: {payload['status'].upper()}")
        for error in payload["errors"]:
            print(f"  ERROR: {error}")
        for warning in payload["warnings"]:
            print(f"  WARN: {warning}")
        return
    if payload.get("status") in {"ok", "dry-run", "blocked", "error"}:
        print(f"Workflow {payload.get('workflow_version', WORKFLOW_VERSION)}")
        print(f"状态：{payload['status']}")
        print(f"项目：{payload.get('project_name') or payload.get('project')}")
        if payload.get("layers"):
            print(
                "装配层："
                + ", ".join(
                    item.get("label", item.get("id", "")) for item in payload["layers"]
                )
            )
        if payload.get("changes"):
            print("计划/已写入：")
            for path in payload["changes"]:
                print(f"  - {path}")
        if payload.get("skipped"):
            print(f"已存在并保留：{len(payload['skipped'])} 个文件")
        if payload.get("dry_run"):
            print("DRY RUN：未写入任何文件")
        for conflict in payload.get("conflicts", []):
            print(f"  CONFLICT: {conflict}")
        for item in payload.get("protected", []):
            print(f"  PROTECTED: {item}")
        return
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _assemble_command(args: argparse.Namespace, mode: str) -> int:
    if args.json and not args.yes and not args.dry_run:
        raise UsageError("--json 装配输出必须配合 --yes 或 --dry-run")
    project = Path(args.path).expanduser().resolve()
    if mode == "create" and project.exists():
        if not project.is_dir():
            raise UsageError(f"目标不是目录：{project}")
        if any(project.iterdir()):
            has_unity = (
                (project / "Assets").is_dir()
                and (project / "ProjectSettings" / "ProjectVersion.txt").is_file()
                and (project / "Packages" / "manifest.json").is_file()
            )
            if not has_unity:
                raise UsageError(
                    "create 的目标必须不存在、为空目录，或已经是 Unity Hub 创建的空项目"
                )
    if mode == "attach" and not project.is_dir():
        raise UsageError(f"现有项目目录不存在：{project}")

    extra_roots = tuple(Path(path).expanduser().resolve() for path in args.profile_root)
    old_lock = None
    old_profile = None
    if mode == "attach" and (project / PROFILE_PATH).is_file():
        old_profile = read_profile(project)
        old_lock = read_lock(project)

    layers = _split_layers(args.layers)
    if not layers:
        if old_profile is not None:
            layers = list(old_profile.layers)
        elif mode == "create":
            layers = ["core", "generic"]
        else:
            registry = discover_profiles(_kit_root(), extra_roots)
            layers = ["core", "generic"]
            for profile_id in ("python", "unity2d"):
                profile = registry.profiles.get(profile_id)
                if profile is not None and profile.detects(project):
                    layers.append(profile_id)
    if (
        old_lock is not None
        and old_lock.workflow_version == WORKFLOW_VERSION
        and old_profile is not None
    ):
        if tuple(layers) != tuple(old_profile.layers):
            raise UsageError(
                "项目已经装配 v4.0，重复 attach 必须保持相同 layers；"
                "修改 layers 需要显式重建项目配置"
            )
        if args.name and args.name != old_profile.name:
            raise UsageError(
                "项目已经装配 v4.0，重复 attach 必须保持相同项目名"
            )
    if args.install_python_deps and shutil.which("uv") is None:
        raise UsageError("请求了 --install-python-deps，但找不到 uv")
    if args.git_init and shutil.which("git") is None:
        raise UsageError("请求了 --git-init，但找不到 git")

    result = assemble_project(
        kit_root=_kit_root(),
        project_root=project,
        layer_ids=layers,
        name=args.name or (old_profile.name if old_profile else None),
        variables=_parse_variables(args.variable),
        extra_profile_roots=extra_roots,
        mode=mode,
        dry_run=args.dry_run or not args.yes,
        accept_protected=args.accept_protected,
        allow_dirty=args.allow_dirty,
        old_lock=old_lock,
    )
    if result.status == "blocked":
        if not args.dry_run:
            report = write_conflict_report(result)
            result.conflicts.append(f"冲突报告：{report}")
        _emit(result.to_dict(), args.json)
        return result.exit_code

    if not args.yes and not args.dry_run:
        print("即将执行以下变更：")
        for path in result.changes:
            print(f"  - {path}")
        if input("继续？[y/N] ").strip().lower() not in {"y", "yes"}:
            print("已取消。")
            return 1
        result = assemble_project(
            kit_root=_kit_root(),
            project_root=project,
            layer_ids=layers,
            name=args.name or (old_profile.name if old_profile else None),
            variables=_parse_variables(args.variable),
            extra_profile_roots=extra_roots,
            mode=mode,
            dry_run=False,
            accept_protected=args.accept_protected,
            allow_dirty=args.allow_dirty,
            old_lock=old_lock,
        )

    if args.dry_run:
        _emit(result.to_dict(), args.json)
        return 0

    if result.status != "ok":
        # assemble_project returns before writing when blocked; reaching here means
        # a dry-run or an unexpected state.
        _emit(result.to_dict(), args.json)
        return result.exit_code

    # assemble_project already applied the planned changes in non-dry-run mode.
    if args.git_init and not (project / ".git").exists():
        _run_checked(["git", "init", "-b", "main"], project)
    if args.install_python_deps and "python" in {item["id"] for item in result.layers}:
        uv = shutil.which("uv")
        assert uv is not None
        _run_checked([uv, "sync"], project)
    _emit(result.to_dict(), args.json)
    return 0


def _run_checked(command: list[str], cwd: Path) -> None:
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        encoding="utf-8",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise UsageError(
            f"命令失败：{' '.join(command)}\n{result.stdout}{result.stderr}"
        )


def _status_command(args: argparse.Namespace) -> int:
    payload = project_status(Path(args.path))
    _emit(payload, args.json)
    return 0 if payload["status"] == "ok" else 1


def _doctor_command(args: argparse.Namespace) -> int:
    payload = doctor_project(Path(args.path))
    _emit(payload, args.json)
    return 0 if payload["status"] in {"ok", "warn"} else 1


def _sync_command(args: argparse.Namespace) -> int:
    project = Path(args.path).expanduser().resolve()
    profile = read_profile(project)
    old_lock = read_lock(project)
    kit_root = Path(args.from_kit).expanduser().resolve()
    if not (kit_root / "profiles").is_dir():
        raise UsageError(f"--from 不是有效的 kit 根：{kit_root}")
    extra_roots = tuple(Path(path).expanduser().resolve() for path in args.profile_root)
    result = assemble_project(
        kit_root=kit_root,
        project_root=project,
        layer_ids=list(profile.layers),
        name=profile.name,
        variables=profile.variables,
        extra_profile_roots=extra_roots,
        mode="sync",
        dry_run=args.check,
        accept_protected=args.accept_protected,
        allow_dirty=args.allow_dirty,
        old_lock=old_lock,
    )
    if result.status == "blocked":
        if not args.check:
            report = write_conflict_report(result)
            result.conflicts.append(f"冲突报告：{report}")
        _emit(result.to_dict(), args.json)
        return result.exit_code
    _emit(result.to_dict(), args.json)
    return 0


def _profile_command(args: argparse.Namespace) -> int:
    if args.profile_action == "list":
        registry = discover_profiles(
            _kit_root(),
            tuple(Path(path).expanduser().resolve() for path in args.profile_root),
        )
        payload = {
            "status": "ok",
            "profiles": [
                {
                    "id": profile.id,
                    "version": profile.version,
                    "display_name": profile.display_name,
                    "description": profile.description,
                    "requires": list(profile.requires),
                    "create_only": profile.create_only,
                }
                for profile in sorted(registry.profiles.values(), key=lambda item: item.id)
            ],
        }
        _emit(payload, args.json)
        return 0
    if args.profile_action == "validate":
        if not args.path:
            raise UsageError("profile validate 需要 profile 目录")
        profile = load_profile(Path(args.path) / "profile.toml")
        _emit(
            {
                "status": "ok",
                "project": str(Path(args.path).resolve()),
                "id": profile.id,
                "version": profile.version,
                "source_hash": profile.source_hash,
            },
            args.json,
        )
        return 0
    if args.profile_action == "init":
        if not args.path or not args.id:
            raise UsageError("profile init 需要目录和 --id")
        if re.fullmatch(r"[a-z][a-z0-9-]*", args.id) is None:
            raise UsageError("profile id 必须匹配 ^[a-z][a-z0-9-]*$")
        destination = Path(args.path).expanduser().resolve()
        if destination.exists() and not destination.is_dir():
            raise UsageError(f"profile init 目标不是目录：{destination}")
        if destination.exists() and any(destination.iterdir()):
            raise UsageError(f"profile init 目标必须为空：{destination}")
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "files").mkdir(exist_ok=True)
        content = (
            f"schema_version = {PROFILE_SCHEMA_VERSION}\n"
            f'id = "{args.id}"\n'
            'version = "1.0.0"\n'
            f'display_name = "{args.id}"\n'
            'description = "团队自定义声明式 profile"\n'
            "requires = []\n"
            "conflicts = []\n"
            "required_paths = []\n"
            "recommended_gates = []\n\n"
            "[detection]\n"
            "all_paths = []\n"
            "any_paths = []\n\n"
            "# [[actions]]\n"
            '# type = "copy_file"\n'
            '# source = "files/example.txt"\n'
            '# target = "example.txt"\n'
            '# ownership = "SEEDED"\n'
        )
        (destination / "profile.toml").write_text(content, encoding="utf-8")
        (destination / "files" / ".gitkeep").write_text("", encoding="utf-8")
        _emit(
            {"status": "ok", "project": str(destination), "profile_id": args.id},
            args.json,
        )
        return 0
    raise UsageError(f"未知 profile 子命令：{args.profile_action}")


def _wizard() -> int:
    print(f"Agent Workflow Kit {WORKFLOW_VERSION} 装配向导")
    action = input("1. 创建新项目  2. 装配现有项目 [1]: ").strip() or "1"
    path = input("项目路径：").strip()
    if not path:
        raise UsageError("项目路径不能为空")
    if action == "2":
        argv = ["attach", path]
        if input("若 Git 工作区已有未提交修改，是否允许继续？[y/N] ").strip().lower() in {
            "y",
            "yes",
        }:
            argv.append("--allow-dirty")
        if input("是否允许明确的受保护配置差异？[y/N] ").strip().lower() in {
            "y",
            "yes",
        }:
            argv.append("--accept-protected")
        return _assemble_command(_build_parser().parse_args(argv), "attach")
    name = input(f"项目名称 [{Path(path).name}]：").strip() or Path(path).name
    kind = input("1. 通用  2. Python starter  3. Unity 空项目 [1]: ").strip() or "1"
    layers = {
        "1": "core,generic",
        "2": "core,generic,python,python-starter",
        "3": "core,generic,unity2d,unity2d-starter",
    }.get(kind)
    if layers is None:
        raise UsageError("未知项目类型")
    argv = ["create", path, "--layers", layers, "--name", name]
    if input("允许 Git 初始化？[y/N] ").strip().lower() in {"y", "yes"}:
        argv.append("--git-init")
    if kind == "2" and input("安装 Python 开发依赖？[y/N] ").strip().lower() in {
        "y",
        "yes",
    }:
        argv.append("--install-python-deps")
    return _assemble_command(_build_parser().parse_args(argv), "create")


def _add_assembly_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("path")
    parser.add_argument("--layers", action="append", help="逗号分隔或重复传入的 layer")
    parser.add_argument("--name")
    parser.add_argument("--variable", action="append", help="模板变量 key=value")
    parser.add_argument("--profile-root", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--allow-dirty", action="store_true")
    parser.add_argument("--accept-protected", action="store_true")
    parser.add_argument("--git-init", action="store_true")
    parser.add_argument("--install-python-deps", action="store_true")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workflow.py",
        description=f"Agent Workflow Kit {WORKFLOW_VERSION} 创建、装配与自检工具",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {KIT_VERSION}")
    subparsers = parser.add_subparsers(dest="command")

    create = subparsers.add_parser("create", help="创建新项目或空 Unity 项目")
    _add_assembly_options(create)

    attach = subparsers.add_parser("attach", help="装配现有项目")
    _add_assembly_options(attach)

    status = subparsers.add_parser("status", help="读取 workflow 状态")
    status.add_argument("path")
    status.add_argument("--json", action="store_true")

    doctor = subparsers.add_parser("doctor", help="离线完整性检查")
    doctor.add_argument("path")
    doctor.add_argument("--json", action="store_true")

    sync = subparsers.add_parser("sync", help="检查或应用 kit 托管更新")
    sync.add_argument("path")
    sync.add_argument("--from", dest="from_kit", required=True)
    action = sync.add_mutually_exclusive_group()
    action.add_argument("--check", action="store_true")
    action.add_argument("--apply", action="store_true")
    sync.add_argument("--profile-root", action="append", default=[])
    sync.add_argument("--allow-dirty", action="store_true")
    sync.add_argument("--accept-protected", action="store_true")
    sync.add_argument("--json", action="store_true")

    profile = subparsers.add_parser("profile", help="管理声明式 profile")
    profile_sub = profile.add_subparsers(dest="profile_action", required=True)
    profile_list = profile_sub.add_parser("list")
    profile_list.add_argument("--profile-root", action="append", default=[])
    profile_list.add_argument("--json", action="store_true")
    profile_validate = profile_sub.add_parser("validate")
    profile_validate.add_argument("path")
    profile_validate.add_argument("--json", action="store_true")
    profile_init = profile_sub.add_parser("init")
    profile_init.add_argument("path")
    profile_init.add_argument("--id", required=True)
    profile_init.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        try:
            return _wizard()
        except (EOFError, KeyboardInterrupt):
            print("\n已取消。", file=sys.stderr)
            return 1
        except WorkflowError as exc:
            print(f"workflow: {exc}", file=sys.stderr)
            return exc.exit_code

    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.command in {"create", "attach"}:
        try:
            return _assemble_command(args, args.command)
        except WorkflowError as exc:
            if getattr(args, "json", False):
                _emit(
                    {
                        "status": "error",
                        "error": str(exc),
                        "exit_code": exc.exit_code,
                    },
                    True,
                )
            else:
                print(f"workflow: {exc}", file=sys.stderr)
            return exc.exit_code
    if args.command == "status":
        try:
            return _status_command(args)
        except WorkflowError as exc:
            if args.json:
                _emit(
                    {
                        "status": "error",
                        "error": str(exc),
                        "exit_code": exc.exit_code,
                    },
                    True,
                )
            else:
                print(f"workflow status: {exc}", file=sys.stderr)
            return exc.exit_code
    if args.command == "doctor":
        try:
            return _doctor_command(args)
        except DoctorError as exc:
            if args.json:
                _emit(
                    {"status": "fail", "error": str(exc), "errors": [str(exc)]}, True
                )
            else:
                print(f"workflow doctor: {exc}", file=sys.stderr)
            return exc.exit_code
    if args.command == "sync":
        if not args.apply and not args.check:
            args.check = True
        try:
            return _sync_command(args)
        except WorkflowError as exc:
            if args.json:
                _emit(
                    {
                        "status": "error",
                        "error": str(exc),
                        "exit_code": exc.exit_code,
                    },
                    True,
                )
            else:
                print(f"workflow: {exc}", file=sys.stderr)
            return exc.exit_code
    if args.command == "profile":
        try:
            return _profile_command(args)
        except WorkflowError as exc:
            if getattr(args, "json", False):
                _emit(
                    {
                        "status": "error",
                        "error": str(exc),
                        "exit_code": exc.exit_code,
                    },
                    True,
                )
            else:
                print(f"workflow: {exc}", file=sys.stderr)
            return exc.exit_code
    parser.print_help()
    return 2
