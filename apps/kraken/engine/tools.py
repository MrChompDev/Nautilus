"""
Kraken AI — Tool registry & implementations.

Agents act through three primitives: file_read, file_write, terminal_exec.
Every state-changing tool is gated by a PermissionGate so terminal actions
never run silently unless --auto-approve is set.
"""

import os
import re
import subprocess
import time
from collections.abc import Callable
from typing import Any

from apps.kraken.engine.logger import engine_logger

log = engine_logger()

MAX_READ_BYTES = 512 * 1024
MAX_OUTPUT_BYTES = 64 * 1024
TERM_TIMEOUT = 300


class ToolError(Exception):
    """A recoverable tool-level failure (fed into the learning loop)."""


class PermissionDenied(Exception):
    """Raised when the operator rejects a state-changing action."""


class PermissionGate:
    """Interactive or auto-approving gate for state-changing tools."""

    def __init__(
        self,
        auto_approve: bool = False,
        allow_force: bool = False,
        confirm_fn: Callable[[str, str, str], bool] | None = None,
    ):
        self.auto_approve = auto_approve
        self.allow_force = allow_force
        self._confirm = confirm_fn

    def confirm(self, action: str, description: str, details: str) -> bool:
        if self.auto_approve:
            return True
        if self._confirm:
            return self._confirm(action, description, details)
        return False  # fail-closed: no approver wired → deny


class ToolResult:
    """Structured result returned by every tool."""

    def __init__(self, ok: bool, output: str, error: str = ""):
        self.ok = ok
        self.output = output
        self.error = error

    def to_dict(self) -> dict:
        return {"ok": self.ok, "output": self.output, "error": self.error}


class ToolContext:
    """Shared context handed to each tool invocation."""

    def __init__(
        self,
        workspace: str,
        gate: PermissionGate,
        log_hook: Callable[[str, str], None] | None = None,
    ):
        self.workspace = os.path.abspath(workspace)
        self.gate = gate
        self.log_hook = log_hook
        os.makedirs(self.workspace, exist_ok=True)

    def log(self, level: str, message: str):
        if self.log_hook:
            self.log_hook(level, message)

    def resolve_path(self, path: str) -> str:
        """Resolve a path strictly inside the workspace (sandboxed)."""
        expanded = os.path.expanduser(os.path.expandvars(path))
        if os.path.isabs(expanded):
            candidate = os.path.abspath(expanded)
        else:
            candidate = os.path.abspath(os.path.join(self.workspace, expanded))
        real = os.path.realpath(candidate)
        ws = os.path.realpath(self.workspace)
        if real == ws or real.startswith(ws + os.sep):
            return real
        raise ToolError(f"path escapes workspace (blocked): {candidate}")


def _truncate(text: str, limit: int = MAX_OUTPUT_BYTES) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} bytes]"


# ── Tools ───────────────────────────────────────────────────────

def tool_file_read(ctx: ToolContext, path: str) -> ToolResult:
    abs_path = ctx.resolve_path(path)
    if not os.path.exists(abs_path):
        return ToolResult(False, "", f"File not found: {abs_path}")
    try:
        size = os.path.getsize(abs_path)
        with open(abs_path, encoding="utf-8", errors="replace") as f:
            content = f.read(MAX_READ_BYTES)
        snippet = content[:MAX_READ_BYTES]
        if size > MAX_READ_BYTES:
            snippet += f"\n... [file is {size} bytes, showing first {MAX_READ_BYTES}]"
        ctx.log("TOOL", f"file_read {path} ({size} bytes)")
        return ToolResult(True, snippet)
    except OSError as e:
        return ToolResult(False, "", f"read failed: {e}")


def tool_file_write(ctx: ToolContext, path: str, content: str) -> ToolResult:
    abs_path = ctx.resolve_path(path)
    if not ctx.gate.confirm(
        "file_write", f"Write file {path}", f"target: {abs_path}\n{content[:400]}"
    ):
        raise PermissionDenied(f"Operator rejected write to {path}")
    try:
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(content)
        ctx.log("TOOL", f"file_write {path} ({len(content)} bytes)")
        return ToolResult(True, f"Wrote {len(content)} bytes to {path}")
    except OSError as e:
        return ToolResult(False, "", f"write failed: {e}")


def tool_file_delete(ctx: ToolContext, path: str) -> ToolResult:
    abs_path = ctx.resolve_path(path)
    if not ctx.gate.confirm("file_delete", f"Delete file {path}", abs_path):
        raise PermissionDenied(f"Operator rejected delete of {path}")
    try:
        if os.path.isdir(abs_path) and not os.path.islink(abs_path):
            import shutil

            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)
        ctx.log("TOOL", f"file_delete {path}")
        return ToolResult(True, f"Deleted {path}")
    except OSError as e:
        return ToolResult(False, "", f"delete failed: {e}")


def tool_file_list(ctx: ToolContext, path: str = ".") -> ToolResult:
    abs_path = ctx.resolve_path(path)
    try:
        entries = sorted(os.listdir(abs_path))
        lines = []
        for name in entries:
            full = os.path.join(abs_path, name)
            tag = "/" if os.path.isdir(full) else ""
            lines.append(f"{name}{tag}")
        ctx.log("TOOL", f"file_list {path} ({len(lines)} entries)")
        return ToolResult(True, "\n".join(lines) if lines else "(empty)")
    except OSError as e:
        return ToolResult(False, "", f"list failed: {e}")


def tool_terminal_exec(ctx: ToolContext, command: str, cwd: str | None = None) -> ToolResult:
    if not command or not command.strip():
        return ToolResult(False, "", "empty command")
    workdir = os.path.abspath(cwd) if cwd else ctx.workspace
    if not ctx.gate.confirm(
        "terminal_exec", f"Run command in {workdir}", command
    ):
        raise PermissionDenied(f"Operator rejected command: {command}")

    ctx.log("TOOL", f"terminal_exec in {workdir}: {command}")
    start = time.time()
    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            cwd=workdir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        try:
            out, _ = proc.communicate(timeout=TERM_TIMEOUT)
        except subprocess.TimeoutExpired:
            proc.kill()
            out, _ = proc.communicate()
            return ToolResult(
                False,
                "",
                f"command timed out after {TERM_TIMEOUT}s; killed\n{_truncate(out)}",
            )
        elapsed = time.time() - start
        summary = f"exit={proc.returncode} in {elapsed:.1f}s"
        if proc.returncode != 0:
            return ToolResult(
                False,
                _truncate(out),
                f"{summary}\n{_truncate(out)[:4000]}",
            )
        return ToolResult(True, f"{summary}\n{_truncate(out)}")
    except OSError as e:
        return ToolResult(False, "", f"spawn failed: {e}")


# ── Registry ────────────────────────────────────────────────────

TOOL_SCHEMA: dict[str, dict[str, Any]] = {
    "file_read": {
        "description": "Read a text file from the workspace. Args: path",
        "args": {"path": "string"},
    },
    "file_write": {
        "description": "Write or overwrite a file in the workspace. Args: path, content",
        "args": {"path": "string", "content": "string"},
    },
    "file_delete": {
        "description": "Delete a file or directory (with permission). Args: path",
        "args": {"path": "string"},
    },
    "file_list": {
        "description": "List directory contents. Args: path (default '.')",
        "args": {"path": "string"},
    },
    "terminal_exec": {
        "description": "Run a shell command. Args: command, optional cwd",
        "args": {"command": "string", "cwd": "string"},
    },
}

_DANGER_PATTERNS = [
    re.compile(r"\brm\s+-rf\s*/"),
    re.compile(r"\b:\(\)\s*\{\s*:\|:&\s*\};:"),  # fork bomb
    re.compile(r"\bmkfs\b"),
    re.compile(r"\bdd\s+.*\bof=\s*/dev/"),
]


def check_dangerous(command: str) -> str | None:
    """Return a warning string when a command looks destructive."""
    for pattern in _DANGER_PATTERNS:
        if pattern.search(command):
            return f"command matches destructive pattern: {pattern.pattern}"
    return None


def _invoke(ctx: ToolContext, name: str, args: dict) -> ToolResult:
    tool = TOOL_SCHEMA.get(name)
    if tool is None:
        return ToolResult(False, "", f"unknown tool: {name}")

    if name == "file_read":
        return tool_file_read(ctx, str(args.get("path", "")))
    if name == "file_write":
        return tool_file_write(ctx, str(args.get("path", "")), str(args.get("content", "")))
    if name == "file_delete":
        return tool_file_delete(ctx, str(args.get("path", "")))
    if name == "file_list":
        return tool_file_list(ctx, str(args.get("path", ".")))
    if name == "terminal_exec":
        command = str(args.get("command", ""))
        danger = check_dangerous(command)
        if danger:
            return ToolResult(False, "", f"blocked: {danger}")
        return tool_terminal_exec(ctx, command, args.get("cwd") or None)
    return ToolResult(False, "", f"unknown tool: {name}")


def call_tool(ctx: ToolContext, name: str, args: dict) -> ToolResult:
    """Invoke a tool by name, catching permission denials."""
    try:
        return _invoke(ctx, name, args)
    except PermissionDenied as e:
        log.warning(f"Permission denied: {e}")
        return ToolResult(False, "", str(e))
    except ToolError as e:
        return ToolResult(False, "", str(e))
    except Exception as e:  # defensive — tool boundaries must never crash the loop
        log.error(f"tool {name} crashed: {e}")
        return ToolResult(False, "", f"tool crash: {e}")


def tool_names(enabled: list[str] | None = None) -> list[str]:
    names = list(TOOL_SCHEMA.keys())
    if enabled:
        names = [n for n in names if n in enabled]
    return names


def describe_tools(enabled: list[str] | None = None) -> str:
    lines = ["You have the following tools. Always use the exact JSON format:"]
    lines.append('  <tool name="TOOL_NAME">{"arg": "value"}</tool>')
    lines.append("Available tools:")
    for name in tool_names(enabled):
        spec = TOOL_SCHEMA[name]
        lines.append(
            f"  - {name}: {spec['description']}  args: {', '.join(spec['args'])}"
        )
    lines.append(
        'When you need to act, end your message with a tool block. '
        "After a tool result, continue working until the task is complete."
    )
    return "\n".join(lines)
