"""Kraken AI — shared tool system.

File read/write, terminal exec, and permission gate.
All four creature models share these tools.
"""

from __future__ import annotations

import fnmatch
import os
import subprocess
import threading
from dataclasses import dataclass, field

DANGEROUS_PATTERNS = [
    "rm -rf /", "rm -rf /*", "mkfs", "dd if=", ":(){ :|:& };:",
    "chmod -R 777 /", "wget", "curl.*|sh", "> /dev/sda",
    "mv /*", "rm -r ~",
]


@dataclass
class PermissionGate:
    auto_approve: bool = False
    _denied: list[str] = field(default_factory=list)

    def ask(self, tool: str, args: dict) -> bool:
        if self.auto_approve:
            return True
        path = args.get("path", "")
        if tool == "file_write" and any(fnmatch.fnmatch(path, p) for p in self._denied):
            return False
        return True

    def deny(self, pattern: str):
        self._denied.append(pattern)


class ToolResult:
    __slots__ = ("ok", "output", "error")

    def __init__(self, ok: bool, output: str = "", error: str = ""):
        self.ok = ok
        self.output = output
        self.error = error


def file_read(path: str, offset: int = 0, limit: int = 2000) -> ToolResult:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            if offset:
                for _ in range(offset):
                    next(f, None)
            lines = []
            for i, line in enumerate(f):
                if i >= limit:
                    break
                lines.append(line)
        return ToolResult(True, "".join(lines))
    except Exception as e:
        return ToolResult(False, error=str(e))


def file_write(path: str, content: str) -> ToolResult:
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(True, f"wrote {len(content)} bytes to {path}")
    except Exception as e:
        return ToolResult(False, error=str(e))


def file_list(path: str = ".") -> ToolResult:
    try:
        entries = []
        for name in sorted(os.listdir(path)):
            full = os.path.join(path, name)
            kind = "dir" if os.path.isdir(full) else "file"
            entries.append(f"{'[D] ' if kind == 'dir' else '    '}{name}")
        return ToolResult(True, "\n".join(entries))
    except Exception as e:
        return ToolResult(False, error=str(e))


_LOCK = threading.Lock()


def terminal_exec(cmd: str, timeout: int = 30) -> ToolResult:
    if any(p in cmd for p in DANGEROUS_PATTERNS):
        return ToolResult(False, error=f"blocked dangerous command: {cmd}")
    try:
        with _LOCK:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, timeout=timeout,
            )
        output = result.stdout
        if result.stderr:
            output += f"\n[stderr]\n{result.stderr}"
        return ToolResult(result.returncode == 0, output=output.strip(), error="" if result.returncode == 0 else f"exit {result.returncode}")
    except subprocess.TimeoutExpired:
        return ToolResult(False, error=f"timeout after {timeout}s")
    except Exception as e:
        return ToolResult(False, error=str(e))


TOOLS = {
    "file_read": file_read,
    "file_write": file_write,
    "file_list": file_list,
    "terminal_exec": terminal_exec,
}


def execute_tool(name: str, args: dict, gate: PermissionGate | None = None) -> ToolResult:
    fn = TOOLS.get(name)
    if fn is None:
        return ToolResult(False, error=f"unknown tool: {name}")
    if gate and not gate.ask(name, args):
        return ToolResult(False, error=f"permission denied by operator for {name}")
    try:
        return fn(**args)
    except TypeError as e:
        return ToolResult(False, error=f"bad args for {name}: {e}")
