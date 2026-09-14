"""Kraken slash commands — builtins + opencode-style custom commands.

Custom commands come from the config `command` section or JSON/MD files in
~/.config/kraken/commands/. Templates support:
  $ARGUMENTS, $1..$n  positional args
  !`shell cmd`        inject command output
  @file               inject file contents
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass

from models.kraken.config import config_dir

SHELL_RE = re.compile(r"!`([^`]+)`")
FILE_RE = re.compile(r"(?<![\w/@])@([\w./~-]+)")
ARG_RE = re.compile(r"\$(\d+)")

BUILTIN_COMMANDS = {
    "model": "switch model: /model <id|provider/model>",
    "models": "list all available models",
    "providers": "list configured providers",
    "clear": "reset the conversation",
    "new": "reset the conversation (alias for /clear)",
    "history": "show the conversation so far",
    "image": "generate an image: /image <prompt>",
    "help": "show this help",
    "mcp": "list MCP servers/tools, or: /mcp add <name> --command ... [-u url]",
    "status": "show session/model/provider status",
    "config": "show resolved config.json path and contents",
    "addmodel": "register a model: /addmodel <id> <provider> [--remote NAME] [--kind text|image]",
    "addprovider": "register a provider: /addprovider <name> <base_url> [--api-key VALUE]",
    "auth": "manage API keys: /auth <provider> [KEY]",
    "quit": "exit",
    "exit": "exit",
    "q": "exit",
}


@dataclass
class Command:
    name: str
    template: str
    description: str = ""
    model: str | None = None
    builtin: bool = False


def _render_shell(template: str, cwd: str) -> str:
    def repl(m: re.Match) -> str:
        try:
            r = subprocess.run(m.group(1), shell=True, capture_output=True,
                               text=True, timeout=60, cwd=cwd)
            return r.stdout.strip() + (f"\nSTDERR: {r.stderr.strip()}" if r.stderr.strip() else "")
        except (OSError, subprocess.TimeoutExpired):
            return f"<command failed: {m.group(1)}>"
    return SHELL_RE.sub(repl, template)


def _render_files(template: str, cwd: str) -> str:
    def repl(m: re.Match) -> str:
        raw = m.group(1)
        path = os.path.expanduser(raw) if raw.startswith("~/") else os.path.join(cwd, raw)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                return f.read()
        except OSError:
            return f"@<missing {raw}>"
    return FILE_RE.sub(repl, template)


def render_template(template: str, argstr: str, cwd: str | None = None) -> str:
    """Expand opencode-style custom-command templates."""
    cwd = cwd or os.getcwd()
    args = argstr.split() if argstr else []
    out = template.replace("$ARGUMENTS", argstr).replace("$1_", "__PLACEHOLDER_ONE__")
    out = re.sub(r"\$(\d+)(?!=)", lambda m: args[int(m.group(1)) - 1] if 1 <= int(m.group(1)) <= len(args) else "",
                 out)
    out = out.replace("__PLACEHOLDER_ONE__", "$1_")
    out = _render_files(out, cwd)
    out = _render_shell(out, cwd)
    return out


class CommandRegistry:
    def __init__(self, config, builtin: bool = True):
        self._cmds: dict[str, Command] = {}
        if builtin:
            for name, desc in BUILTIN_COMMANDS.items():
                self._cmds[name] = Command(name=name, template=name, description=desc, builtin=True)
        for name, entry in (config.commands or {}).items():
            self._cmds[name] = Command(name=name, template=entry.get("template", ""),
                                       description=entry.get("description", ""),
                                       model=entry.get("model"))
        self._load_dir(os.path.join(config_dir(), "commands"))

    def _load_dir(self, d: str) -> None:
        if not os.path.isdir(d):
            return
        for fname in sorted(os.listdir(d)):
            path = os.path.join(d, fname)
            name = fname.rsplit(".", 1)[0]
            try:
                if fname.endswith(".json"):
                    with open(path, encoding="utf-8") as f:
                        entry = json.load(f)
                    self._cmds[name] = Command(name=name, template=entry.get("template", ""),
                                               description=entry.get("description", ""),
                                               model=entry.get("model"))
                elif fname.endswith(".md"):
                    with open(path, encoding="utf-8") as f:
                        raw = f.read()
                    desc, model, template = "", None, raw
                    if raw.startswith("---"):
                        end = raw.find("---", 3)
                        if end != -1:
                            front, template = raw[3:end], raw[end + 3:].strip()
                            for line in front.splitlines():
                                k, _, v = line.partition(":")
                                k, v = k.strip(), v.strip()
                                if k == "description":
                                    desc = v
                                elif k == "model":
                                    model = v
                            template = template.lstrip("\n")
                    self._cmds[name] = Command(name=name, template=template,
                                               description=desc, model=model)
            except (OSError, ValueError):
                continue

    def get(self, name: str) -> Command | None:
        return self._cmds.get(name)

    def names(self) -> list[str]:
        return sorted(self._cmds)

    def custom_names(self) -> list[str]:
        return sorted(n for n, c in self._cmds.items() if not c.builtin)