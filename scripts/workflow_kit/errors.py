"""Typed errors used by the workflow assembler."""

from __future__ import annotations


class WorkflowError(Exception):
    """Base user-facing workflow error."""

    exit_code = 1


class UsageError(WorkflowError):
    """Invalid command input or project shape."""

    exit_code = 2


class ConflictError(WorkflowError):
    """Safe assembly cannot continue without user resolution."""

    exit_code = 2


class DoctorError(WorkflowError):
    """The installed workflow failed an integrity check."""

    exit_code = 1
