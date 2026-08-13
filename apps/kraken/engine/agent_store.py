"""
Kraken AI — custom agent catalog.

Agents built from Markdown specs are stored as plain `.md` files under
`~/.kraken/agents/` and become a first-class library you can invoke by name:

    kraken agent new ReviewCritic --model qwen2.5-coder:7b
    kraken agent list
    kraken agent run ReviewCritic "review the auth pipeline"
    kraken --spec ReviewCritic "review the auth pipeline"

Every stored spec is validated on load, so a hand-edited agent surfaces a
clear `SpecError` instead of silently misbehaving.
"""

import os
import re
from typing import Any

from apps.kraken.engine.spec import KNOWN_TOOL_NAMES, AgentSpec, SpecError

_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")


class AgentStore:
    """A directory-backed catalog of custom Markdown agents."""

    def __init__(self, agents_dir: str):
        self.agents_dir = agents_dir
        os.makedirs(self.agents_dir, exist_ok=True)

    @classmethod
    def from_config(cls, cfg) -> "AgentStore":
        return cls(cfg.agents_dir)

    # ── Paths ──────────────────────────────────────────────────
    def path_for(self, name: str) -> str:
        return os.path.join(self.agents_dir, f"{name}.md")

    # ── Listing ────────────────────────────────────────────────
    def names(self) -> list[str]:
        out = []
        if not os.path.isdir(self.agents_dir):
            return out
        for entry in sorted(os.listdir(self.agents_dir)):
            if entry.endswith(".md"):
                out.append(entry[:-3])
        return out

    def list_agents(self) -> list[dict[str, Any]]:
        rows = []
        for name in self.names():
            try:
                spec = self.get(name)
            except SpecError as e:
                rows.append({"name": name, "path": self.path_for(name),
                             "description": f"[invalid] {e}", "model": "", "tools": [], "source": "invalid"})
                continue
            rows.append({
                "name": spec.name,
                "path": spec.source_path,
                "description": spec.description,
                "model": spec.model,
                "tools": spec.tools,
                "roles": spec.workforce_roles,
                "default_mode": spec.default_mode,
                "source": "library",
            })
        return rows

    # ── Reads ──────────────────────────────────────────────────
    def get(self, name: str) -> AgentSpec | None:
        path = self.path_for(name)
        if not os.path.isfile(path):
            return None
        return AgentSpec.from_file(path)

    def get_or_raise(self, name: str) -> AgentSpec:
        spec = self.get(name)
        if spec is None:
            raise SpecError(
                f"no agent named {name!r} in the library ({self.agents_dir}) — "
                f"try `kraken agent list`"
            )
        return spec

    # ── Writes ─────────────────────────────────────────────────
    def create(self, name: str, *, model: str | None = None,
               tools: list[str] | None = None, description: str = "",
               role: str = "", force: bool = False) -> AgentSpec:
        """Scaffold a new agent spec in the library and return it."""
        if not _NAME_RE.fullmatch(name):
            raise SpecError(
                f"invalid agent name {name!r} — use [A-Za-z][A-Za-z0-9_-]*, "
                f"e.g. ReviewCritic or db_architect"
            )
        path = self.path_for(name)
        if os.path.exists(path) and not force:
            raise SpecError(f"agent {name!r} already exists at {path} (use --force to overwrite)")

        if tools is None:
            tools = ["file_read", "file_write", "terminal_exec"]
        unknown = [t for t in tools if t not in KNOWN_TOOL_NAMES]
        if unknown:
            raise SpecError(
                f"unknown tool(s): {', '.join(unknown)} — known tools: {', '.join(KNOWN_TOOL_NAMES)}"
            )

        spec = AgentSpec(
            name=name,
            model=model or "qwen2.5-coder:14b",
            tools=tools,
            description=description,
            role=role,
            source_path=path,
        )
        spec.validate()
        return self.save(spec)

    def save(self, spec: AgentSpec) -> AgentSpec:
        """Write (or update) a spec file and return it with source_path set."""
        spec.validate()
        path = self.path_for(spec.name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(spec.render())
        spec.source_path = path
        return spec

    def remove(self, name: str) -> bool:
        path = self.path_for(name)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    def import_file(self, path: str, name: str | None = None) -> AgentSpec:
        """Copy an external .md spec into the library."""
        spec = AgentSpec.from_file(path)
        if name and name != spec.name:
            spec.name = name
        spec.source_path = self.path_for(spec.name)
        return self.save(spec)

    # ── Resolution ─────────────────────────────────────────────
    def resolve(self, ref: str) -> AgentSpec:
        """Resolve `ref` as a library name, or a filesystem path, or raise.

        Paths win (so `kraken --spec ./agents/Foo.md` keeps working), then
        library names (`kraken --spec Foo`).
        """
        if os.path.isfile(ref):
            return AgentSpec.from_file(ref)
        if os.sep in ref or ref.endswith(".md"):
            raise SpecError(f"agent spec file not found: {ref}")
        return self.get_or_raise(ref)

    # ── Workforce role lookup ──────────────────────────────────
    def role_spec(self, role: str) -> AgentSpec | None:
        """Return the first library agent that serves the given workforce role."""
        for name in self.names():
            try:
                spec = self.get(name)
            except SpecError:
                continue
            if spec is not None and role in spec.workforce_roles:
                return spec
        return None
