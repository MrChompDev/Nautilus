"""
Kraken AI — Markdown Agent Builder.

Turns any .md instruction file into a specialized autonomous agent by
parsing YAML-ish frontmatter (name, model, tools, auto_retry, ...) plus the
markdown body into the system prompt.

Build:  kraken build --spec ./agents/DatabaseArchitect.md
"""

import os
import re
from dataclasses import dataclass, field
from typing import Any

from apps.kraken.engine.config import DEFAULT_MODEL, DEFAULT_TOOLS

_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)
_HEADER_RE = re.compile(r"^\s*([A-Za-z][A-Za-z0-9_-]*)\s*:\s*(.*?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.+)$")
_LIST_RE = re.compile(r"^\s*\[([^\]]*)\]\s*$")

# Tool names that actually exist in the registry.
KNOWN_TOOL_NAMES = ("file_read", "file_write", "file_delete", "file_list", "terminal_exec")

# Roles an agent may serve inside the Agent Mode workforce.
KNOWN_ROLES = ("planner", "exec", "qa", "worker")

# Valid file/agent-name slugs.
_NAME_RE = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")


class SpecError(Exception):
    """Raised when an agent spec is malformed or fails validation."""


def _parse_scalar(value: str) -> Any:
    """Coerce a frontmatter scalar to bool/int/float/string."""
    v = value.strip()
    low = v.lower()
    if low in ("true", "yes", "on"):
        return True
    if low in ("false", "no", "off"):
        return False
    if low in ("null", "none", "~"):
        return None
    if v.startswith("[") and v.endswith("]"):
        inner = v[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip('"\'') for item in inner.split(",")]
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v.strip('"')


def _parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the leading `---` delimited block into a dict."""
    result: dict[str, Any] = {}
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return result
    current_key: str | None = None
    for line in match.group(1).splitlines():
        header = _HEADER_RE.match(line)
        if header:
            current_key = header.group(1)
            result[current_key] = _parse_scalar(header.group(2))
            continue
        bullet = _BULLET_RE.match(line)
        if bullet and current_key:
            existing = result.get(current_key)
            if isinstance(existing, list):
                existing.append(_parse_scalar(bullet.group(1)))
            elif existing is None or isinstance(existing, str):
                result[current_key] = [_parse_scalar(bullet.group(1))]
        else:
            list_match = _LIST_RE.match(line)
            if list_match and current_key:
                raw = list_match.group(1)
                result[current_key] = [
                    item.strip().strip('"\'') for item in raw.split(",") if item.strip()
                ]
    return result


def _strip_frontmatter(text: str) -> str:
    return _FRONTMATTER_RE.sub("", text, count=1).strip()


def _norm_tools(tools: Any) -> list[str]:
    if isinstance(tools, str):
        tools = [t.strip() for t in tools.split(",") if t.strip()]
    if not isinstance(tools, list):
        return list(DEFAULT_TOOLS)
    known = {t: t for t in KNOWN_TOOL_NAMES}
    return [known.get(str(t).strip(), str(t).strip()) for t in tools if str(t).strip()]


def _norm_roles(roles: Any) -> list[str]:
    if isinstance(roles, str):
        roles = [r.strip() for r in roles.split(",") if r.strip()]
    if not isinstance(roles, list):
        return []
    out: list[str] = []
    for role in roles:
        name = str(role).strip().lower()
        if name in KNOWN_ROLES and name not in out:
            out.append(name)
    return out


@dataclass
class AgentSpec:
    """A parsed Kraken agent definition from a .md spec file."""

    name: str = "Kraken"
    model: str = DEFAULT_MODEL
    tools: list[str] = field(default_factory=lambda: list(DEFAULT_TOOLS))
    auto_retry: bool = True
    max_retries: int = 2
    temperature: float | None = None
    max_tokens: int | None = None
    num_ctx: int | None = None
    description: str = ""
    role: str = ""
    constraints: list[str] = field(default_factory=list)
    capabilities: list[str] = field(default_factory=list)
    workforce_roles: list[str] = field(default_factory=list)
    default_mode: str = "single"
    system_prompt: str = ""
    source_path: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_text(cls, text: str, source_path: str = "") -> "AgentSpec":
        front = _parse_frontmatter(text)
        body = _strip_frontmatter(text)

        constraints: list[str] = []
        capabilities: list[str] = []
        role_parts: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            bullet = _BULLET_RE.match(stripped)
            if bullet:
                content = bullet.group(1).strip()
                if stripped.startswith("- !") or content.lower().startswith("must not") or \
                        content.lower().startswith("never") or content.lower().startswith("always"):
                    constraints.append(content)
                else:
                    capabilities.append(content)
            elif stripped and not stripped.startswith("#"):
                role_parts.append(stripped)

        name = str(front.get("name", "Kraken")).strip() or "Kraken"
        front_role = str(front.get("role", "")).strip()
        body_role = "\n".join(role_parts).strip()
        if front_role and front_role != body_role:
            role = front_role
            prompt_role_parts = [front_role]
        else:
            role = body_role
            prompt_role_parts = role_parts

        custom_prompt = str(front.get("system_prompt", "")).strip()
        if custom_prompt:
            system_prompt = custom_prompt
        else:
            system_prompt_lines = [f"You are {name}, an autonomous software engineering agent."]
            if prompt_role_parts:
                system_prompt_lines.append("\n".join(prompt_role_parts))
            if capabilities:
                system_prompt_lines.append("Capabilities:")
                system_prompt_lines.extend(f"- {c}" for c in capabilities)
            if constraints:
                system_prompt_lines.append("Constraints (always obey):")
                system_prompt_lines.extend(f"- {c}" for c in constraints)
            system_prompt = "\n".join(system_prompt_lines).strip()

        num_ctx = front.get("num_ctx")
        default_mode = str(front.get("default_mode", "single")).strip().lower()
        if default_mode not in ("single", "agent"):
            default_mode = "single"

        spec = cls(
            name=name,
            model=str(front.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
            tools=_norm_tools(front.get("tools")),
            auto_retry=bool(front.get("auto_retry", True)),
            max_retries=int(front.get("max_retries", 2)),
            temperature=front.get("temperature"),
            max_tokens=front.get("max_tokens"),
            num_ctx=int(num_ctx) if num_ctx is not None else None,
            description=str(front.get("description", "")).strip(),
            role=role,
            constraints=constraints,
            capabilities=capabilities,
            workforce_roles=_norm_roles(front.get("workforce_roles")),
            default_mode=default_mode,
            system_prompt=system_prompt,
            source_path=source_path,
            extra={k: v for k, v in front.items() if k not in
                   ("name", "model", "tools", "auto_retry", "max_retries",
                    "temperature", "max_tokens", "num_ctx", "description",
                    "role", "system_prompt", "workforce_roles", "default_mode")},
        )
        return spec

    @classmethod
    def from_file(cls, path: str) -> "AgentSpec":
        with open(path, encoding="utf-8") as f:
            text = f.read()
        spec = cls.from_text(text, source_path=os.path.abspath(path))
        spec.validate()
        return spec

    # ── Validation ─────────────────────────────────────────────
    def validate(self):
        if not _NAME_RE.fullmatch(self.name):
            raise SpecError(
                f"invalid agent name {self.name!r} — use [A-Za-z][A-Za-z0-9_-]*, "
                f"e.g. DatabaseArchitect or qa_reviewer"
            )
        if not str(self.model or "").strip():
            raise SpecError(f"agent {self.name!r} is missing the required `model` field")
        for tool in self.tools:
            if tool not in KNOWN_TOOL_NAMES:
                raise SpecError(
                    f"agent {self.name!r}: unknown tool {tool!r} — "
                    f"known tools: {', '.join(KNOWN_TOOL_NAMES)}"
                )
        for role in self.workforce_roles:
            if role not in KNOWN_ROLES:
                raise SpecError(
                    f"agent {self.name!r}: unknown workforce role {role!r} — "
                    f"known roles: planner, exec, qa"
                )
        if self.default_mode not in ("single", "agent"):
            raise SpecError(
                f"agent {self.name!r}: default_mode must be 'single' or 'agent', got {self.default_mode!r}"
            )

    # ── Convenience ────────────────────────────────────────────
    def describe(self) -> str:
        lines = [
            f"[ {self.name} ]",
            f"  model        : {self.model}",
            f"  tools        : {', '.join(self.tools) or 'none'}",
            f"  auto_retry   : {self.auto_retry}",
        ]
        if self.role:
            role_preview = " ".join(self.role.splitlines())[:80]
            lines.append(f"  role         : {role_preview}")
        if self.temperature is not None:
            lines.append(f"  temperature  : {self.temperature}")
        if self.max_tokens is not None:
            lines.append(f"  max_tokens   : {self.max_tokens}")
        if self.num_ctx is not None:
            lines.append(f"  num_ctx      : {self.num_ctx}")
        if self.workforce_roles:
            lines.append(f"  workforce    : {', '.join(self.workforce_roles)}")
        lines.append(f"  default_mode : {self.default_mode}")
        if self.description:
            lines.append(f"  desc         : {self.description}")
        if self.source_path:
            lines.append(f"  source       : {self.source_path}")
        return "\n".join(lines)

    def render(self) -> str:
        """Render a normalized spec back to markdown (frontmatter + body)."""
        fm = [
            "---",
            f"name: {self.name}",
            f"model: {self.model}",
            f"tools: [{', '.join(self.tools)}]",
            f"auto_retry: {str(self.auto_retry).lower()}",
        ]
        if self.max_retries != 2:
            fm.append(f"max_retries: {self.max_retries}")
        if self.temperature is not None:
            fm.append(f"temperature: {self.temperature}")
        if self.max_tokens is not None:
            fm.append(f"max_tokens: {self.max_tokens}")
        if self.num_ctx is not None:
            fm.append(f"num_ctx: {self.num_ctx}")
        if self.description:
            fm.append(f"description: {self.description}")
        if self.workforce_roles:
            fm.append(f"workforce_roles: [{', '.join(self.workforce_roles)}]")
        if self.default_mode != "single":
            fm.append(f"default_mode: {self.default_mode}")
        if self.system_prompt and not _has_built_prompt(self):
            fm.append(f"system_prompt: {self.system_prompt.replace(chr(10), ' ')}")
        fm.append("---")
        body = [f"# {self.name}"]
        if self.role:
            body.append("")
            body.append("## Role")
            body.append(self.role)
        if self.capabilities:
            body.append("")
            body.append("## Capabilities")
            body.extend(f"- {c}" for c in self.capabilities)
        if self.constraints:
            body.append("")
            body.append("## Constraints")
            body.extend(f"- {c}" for c in self.constraints)
        return "\n".join(fm + [""] + body)


def _has_built_prompt(spec: AgentSpec) -> bool:
    """True when the system prompt was derived from role/capabilities/constraints."""
    built = [f"You are {spec.name}, an autonomous software engineering agent."]
    if spec.role:
        built.append(spec.role)
    if spec.capabilities:
        built.append("Capabilities:")
        built.extend(f"- {c}" for c in spec.capabilities)
    if spec.constraints:
        built.append("Constraints (always obey):")
        built.extend(f"- {c}" for c in spec.constraints)
    return "\n".join(built).strip() == spec.system_prompt


def build_spec_from_cli(spec_path: str) -> AgentSpec:
    """Load and validate a spec file, raising a clear error when absent."""
    if not os.path.exists(spec_path):
        raise FileNotFoundError(f"Spec file not found: {spec_path}")
    return AgentSpec.from_file(spec_path)
