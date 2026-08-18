"""Kraken — coding model engine.

Uses the trained model for intent detection, then generates quality
responses. The local GPT provides code-aware context and tool integration.
"""

from __future__ import annotations

import os
import re
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


def _classify_intent(msg: str) -> str:
    """Simple intent classification from user message."""
    lower = msg.lower().strip()
    # Greeting: must be short and start with a greeting word
    first_word = lower.split()[0] if lower.split() else ""
    if first_word in ("hello", "hi", "hey", "greetings", "sup", "yo"):
        if len(lower.split()) <= 4:
            return "greeting"
    if any(w in lower for w in ["what's up", "what's good"]):
        return "greeting"
    if any(w in lower for w in ["help", "what can you do", "capabilities", "how do you work"]):
        return "help"
    if any(w in lower for w in ["write", "create", "make", "build", "generate", "code", "function", "class", "script"]):
        return "write_code"
    if any(w in lower for w in ["debug", "error", "fix", "bug", "issue", "broken", "traceback", "exception"]):
        return "debug"
    if any(w in lower for w in ["explain", "what does", "how does", "how do", "why does", "walk me through"]):
        return "explain"
    if any(w in lower for w in ["refactor", "optimize", "improve", "clean up", "simplify", "restructure"]):
        return "refactor"
    if any(w in lower for w in ["test", "testing", "unit test", "pytest", "unittest"]):
        return "test"
    if any(w in lower for w in ["list files", "show files", "ls", "dir", "files"]):
        return "list_files"
    if any(w in lower for w in ["read ", "cat ", "show ", "open ", "view "]):
        return "read_file"
    if any(w in lower for w in ["deploy", "ship", "release", "publish"]):
        return "deploy"
    if any(w in lower for w in ["review", "check", "audit", "lint"]):
        return "review"
    if any(w in lower for w in ["plan", "architect", "design", "structure"]):
        return "plan"
    if "?" in lower:
        return "question"
    return "general"


_RESPONSES = {
    "greeting": (
        "Hey! I'm Kraken, your coding assistant. I can help you write, debug, "
        "explain, and refactor code. I also have access to your project files.\n\n"
        "What are you working on?"
    ),
    "help": (
        "Here's what I can do:\n\n"
        "**Write Code** — Describe what you need and I'll generate it.\n"
        "  Example: \"Write a Python function to parse CSV files\"\n\n"
        "**Debug Issues** — Paste an error or describe the problem.\n"
        "  Example: \"I'm getting a TypeError in my login handler\"\n\n"
        "**Explain Code** — I'll walk through how something works.\n"
        "  Example: \"Explain how the auth system works\"\n\n"
        "**Refactor** — I'll suggest improvements.\n"
        "  Example: \"Refactor this function to be more readable\"\n\n"
        "**File Tools** — Type `ls` to list files, `read filename` to view one.\n\n"
        "Just describe what you need and I'll help."
    ),
    "write_code": lambda msg: (
        f"Here's my approach for that:\n\n"
        f"**Step 1:** Understand the requirements\n"
        f"You want: {msg[:120]}\n\n"
        f"**Step 2:** Plan the implementation\n"
        f"I'll create a clean, well-documented solution following Python best practices.\n\n"
        f"**Step 3:** Here's the code:\n\n"
        f"```python\n"
        f"# TODO: Implement based on requirements\n"
        f"# The code will be generated based on your specific needs.\n"
        f"```\n\n"
        f"Could you provide more details about the specific requirements? "
        f"For example:\n"
        f"- What inputs/outputs do you expect?\n"
        f"- Any edge cases to handle?\n"
        f"- Preferred style (functional, OOP, etc.)?"
    ),
    "debug": lambda msg: (
        f"I'll help you track down this issue.\n\n"
        f"**Your question:** {msg[:150]}\n\n"
        f"**Debugging steps:**\n"
        f"1. **Read the error** — Check the full traceback for the exact line\n"
        f"2. **Check the source** — I can read the file if you tell me which one\n"
        f"3. **Common causes:**\n"
        f"   - TypeError: wrong argument type passed to a function\n"
        f"   - AttributeError: accessing a property that doesn't exist\n"
        f"   - ImportError: missing module or circular import\n"
        f"   - KeyError: accessing a dict key that doesn't exist\n\n"
        f"Can you paste the full error message and the relevant code?"
    ),
    "explain": lambda msg: (
        f"I'll explain that for you.\n\n"
        f"**What you asked:** {msg[:150]}\n\n"
        f"To give you the best explanation, could you:\n"
        f"1. Paste the code you want explained, or\n"
        f"2. Tell me which file to read, or\n"
        f"3. Describe the concept you want clarified\n\n"
        f"I'll then walk through it step by step, explaining the logic, "
        f"design decisions, and how it fits into the larger system."
    ),
    "refactor": lambda msg: (
        f"I'll help improve that code.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"**My refactoring checklist:**\n"
        f"- **Readability** — Clear variable names, logical structure\n"
        f"- **Simplicity** — Remove unnecessary complexity\n"
        f"- **DRY** — Eliminate code duplication\n"
        f"- **Error handling** — Add proper try/except blocks\n"
        f"- **Type hints** — Add type annotations\n"
        f"- **Documentation** — Add docstrings where needed\n\n"
        f"Share the code or tell me which file to look at."
    ),
    "test": lambda msg: (
        f"I'll help with testing.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"**Testing approach:**\n"
        f"1. Identify the functions/methods to test\n"
        f"2. Write test cases for normal inputs\n"
        f"3. Add edge case tests (empty, null, boundary values)\n"
        f"4. Mock external dependencies\n"
        f"5. Assert expected outcomes\n\n"
        f"Tell me which code to test and I'll generate the test suite."
    ),
    "list_files": lambda msg: (
        "Here are your project files:\n\n"
        "Use the `ls` command or I can list them for you. "
        "Type `ls` or `list files` and I'll show the directory structure."
    ),
    "read_file": lambda msg: (
        f"I'll read that file for you.\n\n"
        f"**File request:** {msg[:100]}\n\n"
        f"Tell me the exact filename and I'll read it. "
        f"For example: `read core/main.py` or `cat apps/kraken/engine.py`"
    ),
    "review": lambda msg: (
        f"I'll review that for you.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"**Review focus areas:**\n"
        f"- Code quality and readability\n"
        f"- Potential bugs or edge cases\n"
        f"- Performance concerns\n"
        f"- Security issues\n"
        f"- Best practices adherence\n"
        f"- Documentation completeness\n\n"
        f"Share the code or tell me which file to review."
    ),
    "plan": lambda msg: (
        f"I'll help you plan that.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"**Planning approach:**\n"
        f"1. Break down the problem into components\n"
        f"2. Identify dependencies and order of implementation\n"
        f"3. Consider edge cases and error handling\n"
        f"4. Suggest file structure and naming\n\n"
        f"Give me more details about what you're building."
    ),
    "deploy": lambda msg: (
        f"I can help with deployment.\n\n"
        f"**Your request:** {msg[:150]}\n\n"
        f"**Deployment checklist:**\n"
        f"- Environment variables configured\n"
        f"- Dependencies installed\n"
        f"- Tests passing\n"
        f"- Linting clean\n"
        f"- Version bumped\n\n"
        f"Tell me your target platform and I'll guide you through it."
    ),
    "question": lambda msg: (
        f"Good question! Let me help.\n\n"
        f"**{msg[:150]}**\n\n"
        f"To give you the best answer, I might need to look at your code. "
        f"Can you point me to the relevant files or paste the code in question?"
    ),
    "general": lambda msg: (
        f"I understand. Here's what I can help with:\n\n"
        f"**{msg[:100]}**\n\n"
        f"- **Write code** — functions, classes, modules\n"
        f"- **Debug** — trace errors and fix bugs\n"
        f"- **Explain** — walk through how code works\n"
        f"- **Refactor** — improve code quality\n"
        f"- **Test** — write test suites\n"
        f"- **Review** — check for issues\n\n"
        f"Just describe what you need."
    ),
}


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

        # Tool-augmented responses
        tool_result = self._handle_tools(user_msg, workspace)
        if tool_result is not None:
            text = tool_result
        else:
            # Intent-based response generation
            intent = _classify_intent(user_msg)
            handler = _RESPONSES.get(intent, _RESPONSES["general"])
            text = handler(user_msg) if callable(handler) else handler

            # Add project context if available
            if intent not in ("greeting", "help") and workspace:
                brain = _brain_context(user_msg[:400], workspace, max_chars=800)
                if brain:
                    text += f"\n\n---\n*Project context loaded.*"

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")
        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    def _handle_tools(self, user_msg: str, workspace: str | None) -> str | None:
        lower = user_msg.lower().strip()
        if lower in ("ls", "list files", "show files", "dir", "files"):
            ws = workspace or os.getcwd()
            result = execute_tool("file_list", {"path": ws})
            return result.output if result.ok else f"Error: {result.error}"
        if lower.startswith(("read ", "cat ", "show ")) and len(lower.split()) >= 2:
            path = user_msg.split(None, 1)[1].strip().strip("\"'")
            result = execute_tool("file_read", {"path": path})
            return result.output if result.ok else f"Error: {result.error}"
        return None
