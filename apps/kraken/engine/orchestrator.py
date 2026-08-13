"""
Kraken AI — Agent Mode orchestrator.

Breaks a high-level task into sub-tasks and fans them out to a workforce of
specialized sub-agents that run in parallel, each with a dedicated workspace
context. The orchestrator collects results and synthesizes a final report.

Topology:
    Orchestrator
      ├─ Planner Agent      (planning + task decomposition)
      ├─ Code Execution Agent (file work, terminals)
      └─ Review/QA Agent    (verify + final synthesis)
"""

import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from apps.kraken.engine.agent import Agent, AgentEvent
from apps.kraken.engine.logger import engine_logger
from apps.kraken.engine.providers import ChatClient
from apps.kraken.engine.spec import AgentSpec
from apps.kraken.engine.tools import PermissionGate

log = engine_logger()

BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(.+)$")

PLANNER_PROMPT = """You are the Planner Agent in a multi-agent workforce.
Given a high-level task, decompose it into 2-5 concrete, independent sub-tasks
that can be executed in parallel. Output ONLY a numbered list. Each line must
start with a number followed by a period, and must be self-contained.
Do not include any preamble or explanation."""

REVIEW_PROMPT = """You are the Review/QA Agent in a multi-agent workforce.
Below are the results produced by worker agents. Review each for correctness,
completeness, and consistency. Produce a final consolidated report that:
1. Summarizes what was accomplished.
2. Flags any issues or gaps.
3. Lists follow-up recommendations.
Be concise and concrete."""


@dataclass
class SubTask:
    id: str
    title: str
    status: str = "pending"  # pending | running | done | failed | stopped
    output: str = ""
    error: str = ""
    tokens: int = 0
    agent_id: str = ""


@dataclass
class Workforce:
    """A runnable multi-agent workforce spawned by the orchestrator."""

    id: str
    plan: list[SubTask]
    workers: dict[str, SubTask] = field(default_factory=dict)
    started_at: float = field(default_factory=time.time)
    stopped: bool = False
    _lock: threading.Lock = field(default_factory=threading.Lock)


class Orchestrator:
    """Breaks tasks down and runs a parallel workforce of sub-agents."""

    def __init__(
        self,
        client: ChatClient,
        workspace: str,
        gate: PermissionGate,
        spec: AgentSpec,
        max_parallel: int = 3,
        callbacks: list | None = None,
        store=None,
    ):
        self.client = client
        self.workspace = workspace
        self.gate = gate
        self.spec = spec
        self.max_parallel = max(1, max_parallel)
        self.callbacks: list = callbacks or []
        self.store = store
        self.workforce: Workforce | None = None
        self._agent_pool: list[Agent] = []

    # ── Callbacks ──────────────────────────────────────────────
    def _emit(self, kind: str, message: str = "", data: dict | None = None):
        ev = AgentEvent(kind=kind, message=message, data=data or {})
        for cb in self.callbacks:
            try:
                cb(ev)
            except Exception as e:  # defensive
                log.error(f"orchestrator callback failed: {e}")

    # ── Planning ───────────────────────────────────────────────
    def _plan(self, task: str) -> list[str]:
        messages = [
            {"role": "system", "content": PLANNER_PROMPT},
            {"role": "user", "content": f"Task: {task}\nWorkspace: {self.workspace}"},
        ]
        self._emit("status", "orchestrator planning…")
        plan_text = "".join(self.client.stream(messages))
        items = []
        for line in plan_text.splitlines():
            m = BULLET_RE.match(line.strip())
            if m:
                items.append(m.group(1).strip())
        if not items:
            # Fallback: one sub-task carrying the whole task.
            items = [task]
        return items

    # ── Execution ──────────────────────────────────────────────
    def _build_spec(self, role: str, tool_filter: list[str] | None = None) -> AgentSpec:
        import copy

        worker = copy.copy(self.spec)
        worker.name = f"{self.spec.name}::{role}"
        tools = [t for t in self.spec.tools]
        if tool_filter:
            tools = [t for t in tools if t in tool_filter]
        worker.tools = tools
        worker.system_prompt = (
            f"{self.spec.system_prompt}\nYou are assigned the role of {role} in a "
            "parallel workforce. Work in the given workspace and finish your sub-task "
            "autonomously. Do not wait for other agents."
        )
        return worker

    def _resolve_role_spec(self, role: str) -> AgentSpec:
        """Pick the spec for a worker role.

        Priority:
          1. The base spec itself when it declares the role (workforce_roles).
          2. A library agent that declares the role (AgentStore.role_spec).
          3. A role-tagged copy of the base spec.
        """
        if role in self.spec.workforce_roles:
            return self.spec
        if self.store is not None:
            custom = self.store.role_spec(role)
            if custom is not None:
                self._emit(
                    "agent_start",
                    f"custom agent loaded for {role} role: {custom.name}",
                    {"role": role, "agent": custom.name},
                )
                return custom
        return self._build_spec(role)

    def _client_for(self, spec: AgentSpec) -> ChatClient:
        """Reuse the shared client, or build a per-worker client for a custom model."""
        if spec.model and spec.model != self.client.model:
            return ChatClient(
                provider=self.client.provider,
                base_url=self.client.base_url,
                model=spec.model,
                temperature=spec.temperature if spec.temperature is not None else self.client.temperature,
                max_tokens=spec.max_tokens or self.client.max_tokens,
                num_ctx=spec.num_ctx or self.client.num_ctx,
                timeout=self.client.timeout,
            )
        return self.client

    def _worker(self, client: ChatClient, sub: SubTask, index: int):
        sub.status = "running"

        role = "planner" if index == 0 else ("qa" if index == self.workforce_size - 1 else "exec")
        worker_spec = self._resolve_role_spec(role)
        worker_client = self._client_for(worker_spec)

        def _wrap(cb, agent_id):
            def inner(ev):
                ev.data.setdefault("agent_id", agent_id)
                cb(ev)

            return inner

        agent = Agent(
            spec=worker_spec,
            client=worker_client,
            workspace=self.workspace,
            gate=self.gate,
            memory=None,
            callbacks=list(self.callbacks),
        )
        agent.callbacks = [_wrap(cb, agent.agent_id) for cb in self.callbacks]
        self._agent_pool.append(agent)
        sub.agent_id = agent.agent_id
        self._emit(
            "agent_start",
            f"worker: {sub.title}",
            {"agent_id": agent.agent_id, "subtask": sub.id},
        )

        try:
            agent.run(sub.title)
            sub.output = agent.result or ""
            sub.tokens = agent.tokens_used
            sub.status = "done" if agent.status != "error" else "failed"
            sub.error = agent.error or ""
        except Exception as e:  # defensive
            sub.status = "failed"
            sub.error = str(e)
        self._emit(
            "agent_done",
            f"worker finished: {sub.title}",
            {"agent_id": agent.agent_id, "subtask": sub.id, "status": sub.status},
        )

    @property
    def workforce_size(self) -> int:
        return len(self.workforce.plan) if self.workforce else 0

    def run(self, task: str) -> str:
        plan = self._plan(task)
        prefix = f"T{int(time.time()) % 10000}-"
        self.workforce = Workforce(
            id=uuid.uuid4().hex[:8],
            plan=[SubTask(id=f"{prefix}{i+1}", title=t) for i, t in enumerate(plan)],
        )
        self._emit("plan", "workforce plan generated", {"plan": plan})

        # Fan out in parallel batches, capped by max_parallel.
        threads: list[threading.Thread] = []
        for i, sub in enumerate(self.workforce.plan):
            if self.workforce.stopped:
                break
            t = threading.Thread(target=self._worker, args=(self.client, sub, i), daemon=True)
            threads.append(t)
            t.start()
            if (i + 1) % self.max_parallel == 0:
                for done in threads:
                    done.join()
                threads.clear()

        for t in threads:
            t.join()

        report = self._synthesize(task)
        return report

    def run_async(self, task: str, on_finish: Any = None):
        def _target():
            report = self.run(task)
            if on_finish:
                try:
                    on_finish(report)
                except Exception as e:  # defensive
                    log.error(f"on_finish failed: {e}")

        threading.Thread(target=_target, daemon=True, name="kraken-orchestrator").start()

    def stop(self):
        if self.workforce:
            self.workforce.stopped = True
        for agent in self._agent_pool:
            agent.stop()
        self._emit("status", "workforce stop requested")

    # ── Synthesis ──────────────────────────────────────────────
    def _synthesize(self, task: str) -> str:
        if not self.workforce:
            return "No workforce results available."
        lines = ["=== KRAKEN WORKFORCE REPORT ===", f"Task: {task}", ""]
        all_done = True
        for sub in self.workforce.plan:
            mark = {"done": "[OK]", "failed": "[FAIL]", "running": "[...]", "stopped": "[STOP]"}.get(sub.status, "[?]")
            lines.append(f"{mark} {sub.title}")
            lines.append(f"      status: {sub.status}  tokens: {sub.tokens}")
            if sub.output:
                snippet = sub.output.strip().splitlines()
                lines.append("      " + "\n      ".join(snippet[:12]))
            if sub.error:
                lines.append(f"      error: {sub.error[:300]}")
            if sub.status != "done":
                all_done = False
            lines.append("")

        if not all_done:
            lines.append("Some workers did not complete. Review the failures above.")
        return "\n".join(lines)


def run_workforce(
    task: str,
    client: ChatClient,
    workspace: str,
    gate: PermissionGate,
    spec: AgentSpec,
    max_parallel: int = 3,
    callbacks: list | None = None,
    store=None,
) -> str:
    """Convenience wrapper for one-shot workforce execution."""
    orch = Orchestrator(
        client=client,
        workspace=workspace,
        gate=gate,
        spec=spec,
        max_parallel=max_parallel,
        callbacks=callbacks,
        store=store,
    )
    return orch.run(task)
