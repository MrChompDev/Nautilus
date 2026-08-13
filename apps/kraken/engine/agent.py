"""
Kraken AI — Single agent loop.

Runs a spec'd agent against a chat backend with a tool-use loop. When a tool
or terminal command fails, the Self-Correction Loop queries the local memory
store for past resolutions and re-runs the step before surfacing to the user.
"""

import json
import re
import threading
import time
import uuid
from dataclasses import dataclass, field

from apps.kraken.engine.logger import engine_logger
from apps.kraken.engine.memory import MemoryStore
from apps.kraken.engine.providers import ChatClient, ProviderError
from apps.kraken.engine.spec import AgentSpec
from apps.kraken.engine.tools import (
    PermissionGate,
    ToolContext,
    call_tool,
    describe_tools,
)

log = engine_logger()

TOOL_BLOCK_RE = re.compile(
    r'<tool\s+name\s*=\s*["\']([a-z_]+)["\']\s*>\s*(.*?)\s*</tool>',
    re.DOTALL,
)


def visible_text(raw: str) -> str:
    """Return the part of a raw reply that is NOT inside a <tool>...</tool> block.

    Handles unterminated blocks (streaming cutoff) by dropping everything from
    the last opening <tool onward. Used to keep tool call XML out of the chat.
    """
    out: list[str] = []
    i, n = 0, len(raw)
    while i < n:
        if raw.startswith("<tool", i):
            j = raw.find("</tool>", i + 5)
            if j == -1:
                i = n
            else:
                i = j + len("</tool>")
            continue
        out.append(raw[i])
        i += 1
    return "".join(out)


@dataclass
class AgentMessage:
    role: str
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


@dataclass
class AgentEvent:
    """Out-of-band notification emitted by the running agent."""

    kind: str  # token | tool | status | error | done
    message: str
    data: dict = field(default_factory=dict)


class Agent:
    """A single runnable agent bound to a spec, model client and workspace."""

    def __init__(
        self,
        spec: AgentSpec,
        client: ChatClient,
        workspace: str,
        gate: PermissionGate,
        memory: MemoryStore | None = None,
        callbacks: list | None = None,
        max_rounds: int = 12,
    ):
        self.spec = spec
        self.client = client
        self.workspace = workspace
        self.gate = gate
        self.memory = memory
        self.max_rounds = max_rounds
        self.callbacks: list = callbacks or []
        self.agent_id = uuid.uuid4().hex[:8]
        self.thread: threading.Thread | None = None
        self._stop = threading.Event()
        self.events: list[AgentEvent] = []
        self.tokens_used = 0
        self.tool_calls = 0
        self.retries = 0
        self.messages: list[AgentMessage] = []
        self.status = "idle"
        self.finished = False
        self.result: str | None = None
        self.error: str | None = None

    # ── Callbacks ──────────────────────────────────────────────
    def _emit(self, kind: str, message: str = "", data: dict | None = None):
        ev = AgentEvent(kind=kind, message=message, data=data or {})
        self.events.append(ev)
        for cb in self.callbacks:
            try:
                cb(ev)
            except Exception as e:  # defensive
                log.error(f"callback failed: {e}")

    # ── System prompt assembly ─────────────────────────────────
    def _system_prompt(self, task: str) -> str:
        parts = [self.spec.system_prompt]
        parts.append(f"\nWorkspace: {self.workspace}")
        parts.append(f"Task: {task}")
        parts.append("\n" + describe_tools(self.spec.tools))

        if self.memory and self.memory.enabled:
            recalls = self.memory.recall(task, top_k=3)
            if recalls:
                lines = ["\nRelevant past resolutions from memory (use if applicable):"]
                for i, entry in enumerate(recalls, 1):
                    lines.append(
                        f"{i}. [{entry.signature[:80]}]\n   fix: {entry.fix_summary[:300]}"
                    )
                parts.append("\n".join(lines))
        return "\n".join(parts)

    # ── Tool parsing / execution ───────────────────────────────
    @staticmethod
    def parse_tool_blocks(text: str) -> list[dict]:
        found: list[dict] = []
        for match in TOOL_BLOCK_RE.finditer(text):
            name = match.group(1)
            raw_args = match.group(2).strip() or "{}"
            try:
                args = json.loads(raw_args)
                if not isinstance(args, dict):
                    args = {"value": args}
            except ValueError:
                args = {"raw": raw_args[:200]}
            found.append({"name": name, "args": args})
        return found

    def _execute_tool(self, name: str, args: dict, ctx: ToolContext) -> str:
        self.tool_calls += 1
        self._emit("tool", f"[{self.spec.name}] running tool {name}", {"tool": name})
        result = call_tool(ctx, name, args)
        if not result.ok:
            return self._self_correct(name, args, ctx, result.error, result.output)
        self._emit("tool", f"[{self.spec.name}] tool {name} ok")
        return f"TOOL {name} OK\n{result.output}"

    # ── Self-correction loop ───────────────────────────────────
    def _self_correct(self, name: str, args: dict, ctx: ToolContext, error: str, output: str) -> str:
        """Analyze a failure, consult memory, and re-run before giving up."""
        self.retries += 1
        signature = f"{name} :: {args.get('path') or args.get('command') or ''}\n{error}"
        recalled: str = ""
        if self.memory and self.memory.enabled:
            matches = self.memory.recall(signature, top_k=2)
            if matches:
                recalled = matches[0].fix_summary
                self.memory.bump_hit(matches[0].entry_id)
                self._emit("memory", f"[{self.spec.name}] recovered resolution from memory")
            else:
                self._emit("memory", f"[{self.spec.name}] no memory match; storing new failure")

        if not self.spec.auto_retry or self.retries > self.spec.max_retries:
            self._emit(
                "error",
                f"[{self.spec.name}] gave up on tool {name}",
                {"error": error},
            )
            if self.memory and self.memory.enabled and recalled:
                self.memory.remember(signature, recalled, {"tool": name, "args": args}, source="tool")
            return (
                f"TOOL {name} FAILED after retries\nerror:\n{error}\n"
                f"output:\n{output[:2000]}"
            )

        self._emit("retry", f"[{self.spec.name}] retrying {name} ({self.retries}/{self.spec.max_retries})")

        # Ask the model to analyze the failure and propose a patched invocation.
        analysis_prompt = (
            f"Your tool {name} failed with this error:\n{error[:4000]}\n\n"
            f"Command/tool output:\n{output[:4000]}\n\n"
            + (f"A past resolution for a similar error:\n{recalled[:2000]}\n\n" if recalled else "")
            + "Analyze the failure and re-issue the SAME tool with corrected arguments "
            "as your next action. If the tool is file_write, output the full corrected "
            "file content. Respond only with the corrected tool block."
        )
        messages = self.messages_to_openai() + [{"role": "user", "content": analysis_prompt}]
        try:
            reply = "".join(self.client.stream(messages))
        except ProviderError as e:
            return f"TOOL {name} FAILED (retry analysis unavailable: {e})\n{error}"

        blocks = self.parse_tool_blocks(reply)
        if not blocks:
            self._emit("error", f"[{self.spec.name}] model produced no retry block")
            return f"TOOL {name} FAILED\n{error}"

        fixed = blocks[0]
        if fixed["name"] != name:
            self._emit("error", f"[{self.spec.name}] retry switched tool to {fixed['name']}")
            return f"TOOL {name} FAILED\n{error}"

        self._emit("tool", f"[{self.spec.name}] retry attempt {self.retries} on {name}")
        result = call_tool(ctx, name, dict(args, **fixed["args"]))
        if result.ok:
            if self.memory and self.memory.enabled:
                self.memory.remember(
                    signature,
                    result.output[:2000],
                    {"tool": name, "args": args},
                    source="self-correction",
                )
            self._emit("memory", f"[{self.spec.name}] learned fix for {name}")
            return f"TOOL {name} OK (after {self.retries} retries)\n{result.output}"
        return f"TOOL {name} FAILED after retries\n{result.error}"

    # ── Message history helpers ────────────────────────────────
    def messages_to_openai(self) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    # ── Main loop ──────────────────────────────────────────────
    def run(self, task: str):
        """Execute the agent in the calling thread (blocking)."""
        if self.thread and self.thread.is_alive():
            raise RuntimeError("agent already running")
        self.thread = threading.current_thread()
        self.status = "running"
        self.finished = False
        self.result = None
        self.error = None
        self._emit("status", f"[{self.spec.name}] started")

        ctx = ToolContext(
            workspace=self.workspace,
            gate=self.gate,
            log_hook=lambda level, msg: self._emit("log", msg),
        )
        self.messages = [AgentMessage(role="system", content=self._system_prompt(task))]
        self.messages.append(AgentMessage(role="user", content=task))

        try:
            self.result = self._loop(ctx)
        except ProviderError as e:
            self.error = str(e)
            self.status = "error"
            self._emit("error", f"[{self.spec.name}] {e}")
            self.result = f"ERROR: {e}"
        except Exception as e:  # defensive — never leak a crash to the caller
            self.error = str(e)
            self.status = "error"
            log.error(f"[{self.spec.name}] crashed: {e}", exc_info=True)
            self._emit("error", f"[{self.spec.name}] internal error: {e}")
            self.result = f"ERROR: {e}"
        finally:
            self.status = "done" if self.status != "error" else self.status
            self.finished = True
            self._emit("done", f"[{self.spec.name}] finished", {"status": self.status})

    def run_async(self, task: str):
        def _target():
            self.run(task)

        self.thread = threading.Thread(target=_target, daemon=True, name=f"kraken-agent-{self.agent_id}")
        self.thread.start()

    def stop(self):
        self._stop.set()
        self.status = "stopping"

    def _loop(self, ctx: ToolContext) -> str:
        last_reply = ""
        for _round in range(self.max_rounds):
            if self._stop.is_set():
                self._emit("status", f"[{self.spec.name}] stopped by operator")
                return last_reply + "\n[stopped]"

            self._emit("status", f"[{self.spec.name}] thinking…")

            before = self.client.stats["tokens"]
            reply = self._stream_reply()
            delta = self.client.stats["tokens"] - before
            self.tokens_used += delta
            self._emit("token", "", {"tokens": delta})

            self.messages.append(AgentMessage(role="assistant", content=reply))
            last_reply = reply

            blocks = self.parse_tool_blocks(reply)
            if not blocks:
                self._emit("status", f"[{self.spec.name}] finished")
                return reply

            for block in blocks:
                if self._stop.is_set():
                    return last_reply + "\n[stopped]"
                tool_result = self._execute_tool(block["name"], block["args"], ctx)
                self.messages.append(AgentMessage(role="user", content=tool_result))

        self._emit("status", f"[{self.spec.name}] reached max rounds {self.max_rounds}")
        return last_reply + "\n[reached max rounds]"

    def _stream_reply(self) -> str:
        """Stream the assistant reply, emitting visible text deltas as they arrive.

        The raw reply (including <tool> blocks) is buffered; only the visible,
        non-tool text is pushed to the UI in ~250ms flushes so the user sees
        output instead of a long silence while the model generates.
        """
        raw_buf: list[str] = []
        visible_emitted = 0
        last_flush = 0.0

        def flush():
            nonlocal visible_emitted
            visible = visible_text("".join(raw_buf))
            if len(visible) > visible_emitted:
                self._emit("text", visible[visible_emitted:])
                visible_emitted = len(visible)

        def on_chunk(chunk: str):
            nonlocal last_flush
            raw_buf.append(chunk)
            now = time.time()
            if now - last_flush >= 0.25:
                flush()
                last_flush = now

        self.client._on_chunk = on_chunk
        try:
            reply = "".join(self.client.stream(self.messages_to_openai()))
        finally:
            self.client._on_chunk = None
        flush()
        return reply


def run_agent(
    task: str,
    spec: AgentSpec,
    client: ChatClient,
    workspace: str,
    gate: PermissionGate,
    memory: MemoryStore | None = None,
    callbacks: list | None = None,
    max_rounds: int = 12,
) -> Agent:
    """Convenience wrapper that builds and runs an agent synchronously."""
    agent = Agent(
        spec=spec,
        client=client,
        workspace=workspace,
        gate=gate,
        memory=memory,
        callbacks=callbacks,
        max_rounds=max_rounds,
    )
    agent.run(task)
    return agent
