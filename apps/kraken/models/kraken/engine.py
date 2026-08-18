"""Kraken — coding model engine.

Provides coding assistance with project-brain context and file/terminal tools.
Uses intelligent template responses until models are trained large enough.
"""

from __future__ import annotations

import os
import textwrap
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import execute_tool


def _brain_context(query: str, workspace: str | None, max_chars: int = 2000) -> str:
    try:
        from apps.kraken.engine.brain import ProjectBrain
    except Exception:
        return ""
    if not workspace or not os.path.isdir(workspace):
        return ""
    brain = ProjectBrain(workspace)
    if not os.path.exists(brain.db_path):
        try:
            brain.scan()
        except Exception:
            return ""
    try:
        relevant = brain.context(query, k=5)
        tree = brain.file_map()
    except Exception:
        return ""
    lines = tree.splitlines()[:100]
    body = f"# Project files ({workspace})\n" + "\n".join(lines) + f"\n\n# Relevant\n{relevant}"
    return body[:max_chars]


class KrakenEngine(BaseEngine):
    model_id = "kraken"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()

        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = (m.get("content") or "").strip()
                break

        query = user_msg[:400]
        brain = _brain_context(query, workspace)

        # Tool-augmented responses for common coding tasks
        text = self._handle_tools(user_msg, workspace)
        if text is None:
            text = self._generate_response(user_msg, brain)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    def _handle_tools(self, user_msg: str, workspace: str | None) -> str | None:
        lower = user_msg.lower()
        if lower.startswith(("list files", "show files", "ls")):
            ws = workspace or os.getcwd()
            result = execute_tool("file_list", {"path": ws})
            return result.output if result.ok else f"Error: {result.error}"
        if lower.startswith(("read ", "cat ")):
            path = user_msg.split(None, 1)[1].strip().strip("\"'")
            result = execute_tool("file_read", {"path": path})
            return result.output if result.ok else f"Error: {result.error}"
        return None

    def _generate_response(self, user_msg: str, brain: str) -> str:
        lower = user_msg.lower()

        if any(w in lower for w in ["hello", "hi", "hey", "greetings"]):
            return (
                "Hello! I'm Kraken, your coding assistant. I can help you with:\n\n"
                "- Writing and reviewing code\n"
                "- Debugging errors\n"
                "- Explaining how code works\n"
                "- Refactoring and optimizing\n"
                "- File operations (read, list, create)\n\n"
                "What would you like to work on?"
            )

        if any(w in lower for w in ["help", "what can you do", "capabilities"]):
            return (
                "I'm Kraken, a coding assistant for Nautilus OS. Here's what I can do:\n\n"
                "**Code Generation** — Write functions, classes, and modules in Python, JavaScript, and more.\n\n"
                "**Code Review** — Find bugs, suggest improvements, and explain issues.\n\n"
                "**Debugging** — Help trace errors and suggest fixes.\n\n"
                "**File Tools** — I can read and list files in your workspace:\n"
                "  - Type `list files` or `ls` to see your project\n"
                "  - Type `read filename.py` to view a file\n\n"
                "**Project Context** — I understand your project structure and can reference relevant files."
            )

        if any(w in lower for w in ["write", "create", "make", "build", "generate"]):
            return (
                f"I'd be happy to help you build that. Here's my approach:\n\n"
                f"1. **Understand the requirements** — {user_msg[:100]}\n"
                f"2. **Plan the structure** — I'll outline the key components\n"
                f"3. **Write the code** — Clean, documented, following your project conventions\n\n"
                "Could you provide a bit more detail about what you need? For example:\n"
                "- What language or framework?\n"
                "- Any specific requirements or constraints?\n"
                "- Where should the file be placed?"
            )

        if any(w in lower for w in ["debug", "error", "fix", "bug", "issue", "broken"]):
            return (
                "I'll help you track down this issue. Here's my debugging approach:\n\n"
                "1. **Read the error message** — Let's start with the exact error\n"
                "2. **Check the source** — I can read the relevant file\n"
                "3. **Trace the cause** — Walk through the logic step by step\n"
                "4. **Apply the fix** — Make the minimal change needed\n\n"
                "Can you paste the error message or tell me which file is having problems?"
            )

        if any(w in lower for w in ["explain", "what does", "how does", "understand"]):
            return (
                "I can explain code and concepts. To give you the best answer:\n\n"
                "- Paste the code you want explained\n"
                "- Or tell me which file to read\n"
                "- Let me know your experience level so I can tailor the explanation\n\n"
                "What would you like me to explain?"
            )

        if any(w in lower for w in ["refactor", "optimize", "improve", "clean up", "simplify"]):
            return (
                "I can help refactor and improve your code. My focus areas:\n\n"
                "- **Readability** — Clear naming, logical structure\n"
                "- **Performance** — Identify bottlenecks and optimize\n"
                "- **Maintainability** — Reduce complexity, add documentation\n"
                "- **Best practices** — Follow Python/JS conventions\n\n"
                "Share the code or tell me which file to look at, and I'll suggest improvements."
            )

        # Default response
        response = (
            f"I understand you're asking about: \"{user_msg[:80]}\"\n\n"
            "I'm Kraken, your coding assistant. I can help with:\n\n"
            "- **Writing code** — functions, classes, modules\n"
            "- **Debugging** — trace errors and fix bugs\n"
            "- **Explaining** — walk through how code works\n"
            "- **Refactoring** — improve code quality\n"
            "- **File operations** — read and list project files\n\n"
            "Try asking me to write something, debug an error, or explain some code."
        )

        if brain:
            response += f"\n\n---\n\n*Project context loaded from {len(brain)} characters of project files.*"

        return response
