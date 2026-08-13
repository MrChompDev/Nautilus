#!/usr/bin/env python3
"""
Kraken AI — engine unit tests (no model backend required).

Covers the Markdown Agent Builder, the memory (learning loop) store, tool
execution + safety gates, tool-block parsing, and orchestration planning.

Usage:  python3 tests/test_kraken_engine.py
"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from apps.kraken.engine.agent import Agent  # noqa: E402
from apps.kraken.engine.memory import MemoryStore  # noqa: E402
from apps.kraken.engine.orchestrator import BULLET_RE  # noqa: E402
from apps.kraken.engine.spec import AgentSpec  # noqa: E402
from apps.kraken.engine.tools import (  # noqa: E402
    PermissionGate,
    ToolContext,
    call_tool,
    check_dangerous,
)

PASS = 0


def check(name: str, condition: bool):
    global PASS
    if not condition:
        print(f"[FAIL] {name}")
        raise SystemExit(1)
    PASS += 1
    print(f"[ ok ] {name}")


def test_spec_parsing():
    text = """---
name: DatabaseArchitect
model: qwen2.5-coder:14b
tools: [file_read, file_write, terminal_exec]
auto_retry: true
max_retries: 3
temperature: 0.1
---

# Role
You are a database specialist for Nautilus OS.

# Constraints
- Always use SQL optimization best practices.
- Never execute drop database commands without explicit user permission.
"""
    spec = AgentSpec.from_text(text)
    check("spec.name", spec.name == "DatabaseArchitect")
    check("spec.model", spec.model == "qwen2.5-coder:14b")
    check("spec.tools", spec.tools == ["file_read", "file_write", "terminal_exec"])
    check("spec.auto_retry", spec.auto_retry is True)
    check("spec.max_retries", spec.max_retries == 3)
    check("spec.temperature", spec.temperature == 0.1)
    check("spec.role", "database specialist" in spec.role)
    check("spec.constraints", any("drop database" in c for c in spec.constraints))
    check("spec.system_prompt", "You are DatabaseArchitect" in spec.system_prompt)
    check("spec.system_prompt has constraints", "Never execute drop database" in spec.system_prompt)


def test_spec_defaults():
    spec = AgentSpec.from_text("# Foo\n\nYou do things.\n")
    check("spec default name", spec.name == "Kraken")
    check("spec default tools", set(spec.tools) == {"file_read", "file_write", "terminal_exec"})
    check("spec default auto_retry", spec.auto_retry is True)


def test_memory_loop():
    d = tempfile.mkdtemp()
    mem = MemoryStore(os.path.join(d, "memory.db"))
    eid = mem.remember(
        "file_write :: /src/auth.py\nTraceback (most recent call last)\nImportError: No module named bcrypt",
        "add missing import: pip install bcrypt / import at top",
        {"tool": "file_write"},
        source="self-correction",
    )
    check("memory.remember returns id", bool(eid))

    recall = mem.recall("ImportError No module named bcrypt in auth.py", top_k=2)
    check("memory.recall finds entry", len(recall) == 1)
    check("memory.recall fix", "bcrypt" in recall[0].fix_summary)

    exact = mem.find_exact(eid if False else recall[0].error_signature)
    check("memory.find_exact", exact is not None)

    stats = mem.stats()
    check("memory.stats entries", stats["entries"] == 1)

    mem.bump_hit(recall[0].entry_id)
    check("memory.hit increment", mem.find_exact(recall[0].error_signature).hits == 1)

    mem.close()
    # Reopen to verify persistence.
    mem2 = MemoryStore(os.path.join(d, "memory.db"))
    check("memory persistence", mem2.stats()["entries"] == 1)
    mem2.close()


def test_tools():
    d = tempfile.mkdtemp()
    ctx = ToolContext(workspace=d, gate=PermissionGate(auto_approve=True))

    r = call_tool(ctx, "file_write", {"path": "src/hello.txt", "content": "kraken"})
    check("tool.file_write ok", r.ok)
    r = call_tool(ctx, "file_read", {"path": "src/hello.txt"})
    check("tool.file_read content", r.ok and r.output == "kraken")
    r = call_tool(ctx, "file_list", {"path": "src"})
    check("tool.file_list", r.ok and "hello.txt" in r.output)
    r = call_tool(ctx, "terminal_exec", {"command": "echo kraken-works"})
    check("tool.terminal_exec ok", r.ok and "kraken-works" in r.output)
    r = call_tool(ctx, "terminal_exec", {"command": "exit 3"})
    check("tool.terminal_exec failure", not r.ok and "exit=3" in r.error)

    # Path traversal is blocked by workspace resolution.
    r = call_tool(ctx, "file_read", {"path": "/etc/hostname"})
    check("tool.path traversal", "/etc/hostname" in r.output or not r.ok)

    # Danger patterns are refused.
    danger = check_dangerous("rm -rf / && echo gone")
    check("tool.danger detection", danger is not None)


def test_permission_gate():
    d = tempfile.mkdtemp()
    denied = PermissionGate(auto_approve=False, confirm_fn=lambda *a: False)
    ctx = ToolContext(workspace=d, gate=denied)
    r = call_tool(ctx, "file_write", {"path": "nope.txt", "content": "x"})
    check("gate denies write", not r.ok and "rejected" in r.error.lower())


def test_tool_block_parsing():
    text = 'Let me look.\n<tool name="file_read">{"path": "src/main.py"}</tool>\n'
    blocks = Agent.parse_tool_blocks(text)
    check("parse single block", len(blocks) == 1 and blocks[0]["name"] == "file_read")
    check("parse args", blocks[0]["args"]["path"] == "src/main.py")

    mixed = 'a\n<tool name="terminal_exec">{"command": "ls"}</tool>b<tool name="file_write">{"path":"x","content":"y"}</tool>'
    blocks = Agent.parse_tool_blocks(mixed)
    check("parse multiple blocks", len(blocks) == 2)
    check("parse no blocks", Agent.parse_tool_blocks("just text") == [])


def test_orchestrator_plan_parsing():
    lines = [
        "1. Scaffold the REST API endpoints",
        "2. Implement the auth middleware",
        "- Write integration tests",
        "not a plan line",
        "3) Add documentation",
    ]
    items = [BULLET_RE.match(l.strip()).group(1) for l in lines if BULLET_RE.match(l.strip())]
    check("orchestrator plan bullets", len(items) == 4)
    check("orchestrator plan skip", "not a plan line" not in items)


def main():
    print("Kraken AI engine tests\n")
    test_spec_parsing()
    test_spec_defaults()
    test_memory_loop()
    test_tools()
    test_permission_gate()
    test_tool_block_parsing()
    test_orchestrator_plan_parsing()
    print(f"\n{PASS} checks passed")


if __name__ == "__main__":
    main()
