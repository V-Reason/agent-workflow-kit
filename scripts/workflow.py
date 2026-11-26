#!/usr/bin/env python3
"""Agent Workflow Kit v4.0 project create/attach/status entry point."""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
for _stream in (sys.stdout, sys.stderr):
    reconfigure = getattr(_stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8")

from workflow_kit.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
