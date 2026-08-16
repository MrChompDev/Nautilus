#!/usr/bin/env python3
"""
Kraken AI — Command-line interface.

Usage:
  kraken                          Interactive mode (REPL / TUI)
  kraken "fix the auth pipeline"  Direct command mode
  kraken --agent-mode "build a REST API"
  kraken build --spec ./agents/MyAgent.md
  kraken config [key value]
  kraken models
  kraken doctor
  kraken memory
"""

import argparse
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from apps.kraken.engine import __version__  # noqa: E402
from apps.kraken.engine.agent_store import AgentStore  # noqa: E402
from apps.kraken.engine.config import DEFAULT_PROVIDERS, KrakenConfig  # noqa: E402
from apps.kraken.engine.discovery import (  # noqa: E402
    detect_provider_health,
    find_local_models,
    list_api_models,
    recommend_backend,
)
from apps.kraken.engine.keys import get_key, load_keys, mask_key, save_keys  # noqa: E402
from apps.kraken.engine.logger import engine_logger  # noqa: E402
from apps.kraken.engine.memory import MemoryStore  # noqa: E402
from apps.kraken.engine.providers import ChatClient  # noqa: E402
from apps.kraken.engine.spec import AgentSpec, SpecError  # noqa: E402

log = engine_logger()

ANSI = {
    "seafoam": "\033[38;5;85m",
    "coral": "\033[38;5;203m",
    "amber": "\033[38;5;214m",
    "dim": "\033[2m",
    "bold": "\033[1m",
    "reset": "\033[0m",
}
NO_ANSI = dict.fromkeys(ANSI, "")


def _c(color: str, text: str, use_color: bool = True) -> str:
    if not use_color:
        return text
    return f"{ANSI[color]}{text}{ANSI['reset']}"


BANNER = r"""
  _  __                 _
 | |/ /__ _ _ __ _ __ __| | __ _ _ __
 | ' // _` | '__| '_ ` _ \/ _` | '_ \
 | . \ (_| | |  | | | | | | (_| | | | |
 |_|\_\__,_|_|  |_| |_| |_|\__,_|_| |_|
"""


def _banner(use_color: bool) -> str:
    color = ANSI["seafoam"] if use_color else ""
    reset = ANSI["reset"] if use_color else ""
    return f"{color}{BANNER}{reset}"


# ═══════════════════════════════════════════════════════════════
#  SESSION BUILDERS
# ═══════════════════════════════════════════════════════════════

def build_store(cfg: KrakenConfig) -> AgentStore:
    return AgentStore(cfg.agents_dir)


def build_client(cfg: KrakenConfig, spec: AgentSpec | None = None) -> ChatClient:
    model = spec.model if spec is not None else cfg.model
    temperature = spec.temperature if spec is not None and spec.temperature is not None else cfg.get("temperature", 0.2)
    max_tokens = spec.max_tokens if spec is not None and spec.max_tokens else cfg.get("max_tokens", 4096)
    num_ctx = spec.num_ctx if spec is not None and spec.num_ctx else cfg.get("num_ctx", 8192)
    api_key = cfg.get("api_key") or get_key(cfg.home_dir, cfg.provider)
    return ChatClient(
        provider=cfg.provider,
        base_url=cfg.base_url,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        num_ctx=num_ctx,
        api_key=api_key,
        timeout=cfg.get("timeout", 300),
        workspace=cfg.workspace,
    )


def build_memory(cfg: KrakenConfig) -> MemoryStore:
    return MemoryStore(cfg.memory_path, enabled=bool(cfg.get("memory_enabled", True)))


def build_spec(cfg: KrakenConfig, spec_ref: str | None = None) -> AgentSpec:
    """Resolve a spec from a library name or a filesystem path."""
    if spec_ref:
        return build_store(cfg).resolve(spec_ref)
    return AgentSpec(name="Kraken", model=cfg.model, tools=cfg.get("tools") or ["file_read", "file_write", "terminal_exec"])


def _approve_prompt(action: str, description: str, details: str) -> bool:
    try:
        while True:
            answer = input(f"  {action} :: {description}\n  approve? [y/N] ").strip().lower()
            if answer in ("y", "yes"):
                return True
            if answer in ("n", "no", ""):
                return False
    except (EOFError, KeyboardInterrupt):
        return False


def _gate(cfg: KrakenConfig, auto_approve: bool):
    from apps.kraken.engine.tools import PermissionGate

    return PermissionGate(auto_approve=auto_approve or bool(cfg.get("auto_approve", False)),
                          confirm_fn=_approve_prompt)


# ═══════════════════════════════════════════════════════════════
#  SUBCOMMANDS
# ═══════════════════════════════════════════════════════════════

def cmd_doctor(cfg: KrakenConfig, use_color: bool = True):
    print(_banner(use_color))
    print(f"Kraken AI v{__version__} — environment check\n")
    print(f"  home      : {cfg.home_dir}")
    print(f"  config    : {cfg.config_path}")
    print(f"  memory    : {cfg.memory_path}")

    mem = build_memory(cfg)
    stats = mem.stats()
    print(f"  memory db : {'enabled, ' + str(stats['entries']) + ' entries' if stats['enabled'] else 'disabled'}")

    print(f"\n  configured: {cfg.provider} → {cfg.base_url}  (model: {cfg.model})")
    api_key = cfg.get("api_key") or get_key(cfg.home_dir, cfg.provider)
    print(f"  api key   : {mask_key(api_key) if api_key else 'not set'}")

    health = detect_provider_health()
    print("\n  local servers:")
    for name, state in health.items():
        marker = _c("seafoam", "up", use_color) if state["alive"] else _c("dim", "down", use_color)
        print(f"    {name:<10} {marker}  {DEFAULT_PROVIDERS[name]['base_url']}")

    local = find_local_models(cfg.base_url)
    if local:
        print("\n  downloaded / reachable models:")
        for m in local[:24]:
            print(f"    {m['provider']:<10} {m['name']}")
        if len(local) > 24:
            print(f"    … and {len(local) - 24} more")
    else:
        print(_c("amber", "\n  no local models detected (Ollama / LM Studio / GGUF)", use_color))

    keys = load_keys(cfg.home_dir)
    cloud = [p for p in DEFAULT_PROVIDERS if p not in ("ollama", "lmstudio", "vllm", "llamacpp")]
    if any(keys.get(p) for p in cloud):
        print("\n  api keys found:")
        for p in cloud:
            if keys.get(p):
                print(f"    {p:<10} {mask_key(keys[p])}  ({DEFAULT_PROVIDERS[p]['base_url']})")

    print(f"\n  tools     : {', '.join(cfg.get('tools') or [])}")
    print(f"  autoapprove : {cfg.get('auto_approve', False)}")
    print(f"  workspace : {cfg.workspace}")

    rec = recommend_backend(cfg.home_dir, cfg.base_url)
    if rec:
        print(_c("seafoam", f"\n  suggestion: use {rec['provider']} ({rec['hint']}) — run `kraken setup`", use_color))
    elif not api_key:
        print(_c("amber", "\n  suggestion: add an API key (`kraken keys add openai sk-...`) or start a local server", use_color))


def cmd_config(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    if not args:
        print("Kraken config:")
        for key in sorted(cfg.data):
            val = cfg.data[key]
            if isinstance(val, list):
                val = "[" + ", ".join(str(v) for v in val) + "]"
            print(f"  {key:<16} : {val}")
        print("\nproviders:")
        for name, meta in DEFAULT_PROVIDERS.items():
            print(f"  {name:<12} : {meta['base_url']}")
        return
    if len(args) == 1:
        print(f"  {args[0]} : {cfg.get(args[0])}")
        return
    key, value = args[0], " ".join(args[1:])
    parsed = value
    low = value.lower()
    if low in ("true", "yes", "on"):
        parsed = True
    elif low in ("false", "no", "off"):
        parsed = False
    elif value.isdigit():
        parsed = int(value)
    cfg.set(key, parsed)
    print(_c("seafoam", f"  set {key} = {parsed}", use_color))
    if key == "provider":
        meta = DEFAULT_PROVIDERS.get(parsed, {})
        if meta and cfg.base_url == DEFAULT_PROVIDERS.get("ollama", {}).get("base_url"):
            cfg.set("base_url", meta["base_url"])
            print(_c("seafoam", f"  base_url updated to {meta['base_url']}", use_color))


def cmd_build(cfg: KrakenConfig, spec_ref: str, use_color: bool = True):
    try:
        spec = build_spec(cfg, spec_ref)
    except SpecError as e:
        print(_c("coral", f"ERROR: {e}", use_color))
        sys.exit(1)
    print(_c("seafoam", f"[OK] parsed {spec.source_path}", use_color))
    print(spec.describe())
    print("\nsystem prompt preview:\n")
    print(spec.system_prompt[:800])


def cmd_models(cfg: KrakenConfig, use_color: bool = True):
    from apps.kraken.engine import local
    from apps.kraken.engine.config import NAUTILUS_MODELS

    naut = local.list_local_models()
    if naut:
        print("Nautilus from-scratch models (local, offline):")
        for m in naut:
            label = NAUTILUS_MODELS.get(m["id"], m["id"])
            print(f"  {'nautilus':<10} {m['id']:<8} ~{m['size_mb']}MB  {label}")
        print("\nLocal servers (downloaded / reachable):")
    else:
        print("Nautilus from-scratch models: (none trained yet) — see models/lm/train.py")
        print("\nLocal servers (downloaded / reachable):")
    local = find_local_models(cfg.base_url)
    by_provider: dict[str, list[str]] = {}
    for m in local:
        by_provider.setdefault(m["provider"], []).append(m["name"])
    if not local:
        print("  (none) — start Ollama/LM Studio/llama.cpp or drop .gguf files in a model dir")
    for provider in ("ollama", "lmstudio", "llamacpp"):
        names = by_provider.get(provider, [])
        if names:
            print(f"  {provider:<10} {', '.join(names[:12])}")
            if len(names) > 12:
                print(f"             … and {len(names) - 12} more")

    keys = load_keys(cfg.home_dir)
    cloud = [p for p in DEFAULT_PROVIDERS if p not in ("ollama", "lmstudio", "vllm", "llamacpp")]
    print("\nCloud providers (api key found?):")
    for p in cloud:
        key = keys.get(p)
        status = mask_key(key) if key else "no key"
        print(f"  {p:<10} {status}")
        if key:
            available = list_api_models(p, DEFAULT_PROVIDERS[p]["base_url"], key)
            if available:
                print(f"             models: {', '.join(available[:12])}")

    if not keys:
        print("\nNo API keys detected. Add one with:  kraken keys add openai sk-...")


def cmd_keys(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    keys = load_keys(cfg.home_dir)
    sub = args[0].lower() if args else "list"

    if sub in ("list", "show") or sub == "list":
        known = [p for p in DEFAULT_PROVIDERS if p not in ("ollama", "lmstudio", "vllm", "llamacpp")]
        print("API keys:")
        for p in known:
            key = keys.get(p)
            if key:
                print(f"  {p:<10} {mask_key(key)}")
            else:
                print(f"  {p:<10} -")
        print(f"\n  store : {os.path.join(cfg.home_dir, 'keys.json')}")
        return

    if sub in ("add", "set"):
        if len(args) < 3:
            print(_c("amber", "usage: kraken keys add <provider> <api-key>", use_color))
            return
        provider, key = args[1], args[2]
        if provider not in DEFAULT_PROVIDERS:
            print(_c("amber", f"unknown provider {provider!r} — known: {', '.join(DEFAULT_PROVIDERS)}", use_color))
            return
        keys[provider] = key
        save_keys(cfg.home_dir, keys)
        print(_c("seafoam", f"  stored {provider} key ({mask_key(key)}) → {os.path.join(cfg.home_dir, 'keys.json')}", use_color))
        return

    if sub in ("remove", "rm"):
        if len(args) < 2:
            print(_c("amber", "usage: kraken keys remove <provider>", use_color))
            return
        provider = args[1]
        if provider in keys:
            del keys[provider]
            save_keys(cfg.home_dir, keys)
            print(_c("seafoam", f"  removed {provider} key", use_color))
        else:
            print(_c("dim", f"  no {provider} key stored", use_color))
        return

    print(_c("coral", f"unknown keys subcommand: {sub}", use_color))
    print(_c("amber", "known: list | add <provider> <key> | remove <provider>", use_color))


def cmd_setup(cfg: KrakenConfig, use_color: bool = True):
    print(_banner(use_color))
    print("Kraken setup — auto-detect a working backend\n")
    rec = recommend_backend(cfg.home_dir, cfg.base_url)
    if rec is None:
        print(_c("coral", "nothing found: start a local model server (Ollama/LM Studio) or add an API key", use_color))
        print(_c("amber", "  kraken keys add openai sk-...", use_color))
        return
    cfg.update(provider=rec["provider"], base_url=rec["base_url"], model=rec["model"])
    if rec.get("api_key") and not cfg.get("api_key"):
        cfg.set("api_key", rec["api_key"])
    print(_c("seafoam", f"  configured: {rec['provider']} → {rec['base_url']}", use_color))
    print(f"  model     : {rec['model']}")
    print(f"  api key   : {mask_key(rec['api_key']) if rec.get('api_key') else 'none'}")
    print(f"  ({rec.get('hint', '')})")
    print(_c("dim", "\n  change anything with:  kraken config provider|base_url|model <value>", use_color))


def cmd_brain(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    from apps.kraken.engine.brain import ProjectBrain

    sub = args[0].lower() if args else "scan"
    path = args[1] if len(args) > 1 else cfg.workspace
    brain = ProjectBrain(path)
    if sub == "status":
        st = brain.status()
        print(f"  workspace : {st['workspace']}")
        print(f"  files     : {st['files']}")
        langs = ", ".join(f"{k}×{v}" for k, v in sorted(st['languages'].items(), key=lambda x: -x[1])[:10])
        print(f"  languages : {langs or '—'}")
        print(f"  db        : {st['db']}")
        return
    if sub == "context":
        query = args[1] if len(args) > 1 else ""
        if not query:
            print("  usage: kraken brain context \"question\" [path]")
            return
        print(brain.context(query, k=6))
        return
    print(f"  indexing {path} …")
    res = brain.scan()
    print(f"  done: +{res['added']} new, {res['updated']} updated, {res['removed']} removed, "
          f"{res['unchanged']} unchanged, {res['total']} files in brain")


def cmd_memory(cfg: KrakenConfig, use_color: bool = True):
    mem = build_memory(cfg)
    stats = mem.stats()
    print("Kraken memory (error learning loop):")
    print(f"  enabled : {stats['enabled']}")
    print(f"  entries : {stats['entries']}")
    for item in stats.get("top_resolved", []):
        print(f"  - {item['signature'][:70]}  (hits: {item['hits']})")



# ═══════════════════════════════════════════════════════════════
#  CUSTOM AGENT CATALOG  (kraken agent ...)
# ═══════════════════════════════════════════════════════════════

def cmd_agent_new(cfg: KrakenConfig, args: list[str], use_color: bool = True, force: bool = False):
    if not args:
        print(_c("amber", "usage: kraken agent new <name> [--model qwen2.5-coder:7b] [--tools a,b] [--role ...] [--desc ...]", use_color))
        return
    name = args[0]
    store = build_store(cfg)
    kwargs: dict = {}
    rest = args[1:]
    if "--model" in rest:
        kwargs["model"] = rest[rest.index("--model") + 1]
    if "--role" in rest:
        kwargs["role"] = rest[rest.index("--role") + 1]
    if "--desc" in rest:
        kwargs["description"] = rest[rest.index("--desc") + 1]
    if "--tools" in rest:
        kwargs["tools"] = [t.strip() for t in rest[rest.index("--tools") + 1].split(",") if t.strip()]
    try:
        spec = store.create(name, force=force, **kwargs)
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        sys.exit(1)
    print(_c("seafoam", f"[OK] agent created: {spec.name}", use_color))
    print(f"  path  : {spec.source_path}")
    print(f"  model : {spec.model}")
    print(f"  tools : {', '.join(spec.tools)}")
    print(_c("dim", "\nRun it:  kraken agent run " + spec.name + " \"your task\"", use_color))


def cmd_agent_list(cfg: KrakenConfig, use_color: bool = True):
    store = build_store(cfg)
    rows = store.list_agents()
    if not rows:
        print(_c("amber", "no custom agents in the library", use_color))
        print(_c("dim", "create one:  kraken agent new ReviewCritic --model qwen2.5-coder:7b", use_color))
        return
    width = max(len(r["name"]) for r in rows) + 2
    for row in rows:
        model = row["model"] or "—"
        desc = row["description"] or ""
        roles = f" [{', '.join(row['roles'])}]" if row.get("roles") else ""
        print(f"  {row['name']:<{width}}{model:<22}{desc[:60]}{roles}")
    print(_c("dim", f"\n{len(rows)} agent(s) in {store.agents_dir}", use_color))


def cmd_agent_show(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    if not args:
        print(_c("amber", "usage: kraken agent show <name>", use_color))
        return
    try:
        spec = build_spec(cfg, args[0])
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        sys.exit(1)
    print(spec.describe())
    print("\nsystem prompt preview:\n")
    print(spec.system_prompt[:800])


def cmd_agent_edit(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    if not args:
        print(_c("amber", "usage: kraken agent edit <name>", use_color))
        return
    store = build_store(cfg)
    name = args[0]
    try:
        spec = store.get_or_raise(name)
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        sys.exit(1)
    editor = os.environ.get("EDITOR") or os.environ.get("VISUAL") or ("notepad" if os.name == "nt" else "vi")
    before = spec.render()
    rc = os.system(f'"{editor}" "{spec.source_path}"')
    if rc != 0:
        print(_c("coral", f"[error] editor exited with code {rc}", use_color))
        sys.exit(1)
    try:
        updated = store.get_or_raise(name)
    except SpecError as e:
        print(_c("coral", f"[error] {name} is now invalid: {e}", use_color))
        print(_c("amber", "re-run `kraken agent edit " + name + "` to fix it", use_color))
        sys.exit(1)
    if updated.render() == before:
        print(_c("dim", f"no changes to {name}", use_color))
    else:
        print(_c("seafoam", f"[OK] updated {name} — validate+reloaded from {spec.source_path}", use_color))
        print(f"  model : {updated.model}  tools: {', '.join(updated.tools)}")


def cmd_agent_remove(cfg: KrakenConfig, args: list[str], use_color: bool = True, yes: bool = False):
    if not args:
        print(_c("amber", "usage: kraken agent remove <name>", use_color))
        return
    store = build_store(cfg)
    name = args[0]
    if store.get(name) is None:
        print(_c("coral", f"[error] no agent named {name!r} in the library", use_color))
        sys.exit(1)
    if not yes:
        try:
            answer = input(f"  remove agent {name}? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            answer = "n"
        if answer not in ("y", "yes"):
            print("  cancelled")
            return
    store.remove(name)
    print(_c("seafoam", f"[OK] removed {name}", use_color))

def cmd_agent_import(cfg: KrakenConfig, args: list[str], use_color: bool = True):
    if not args:
        print(_c("amber", "usage: kraken agent import <path-to-spec.md> [--name MyName]", use_color))
        return
    path = args[0]
    name = None
    if "--name" in args:
        name = args[args.index("--name") + 1]
    store = build_store(cfg)
    try:
        spec = store.import_file(path, name=name)
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        sys.exit(1)
    print(_c("seafoam", f"[OK] imported {spec.name} into the library", use_color))
    print(f"  path : {spec.source_path}")


def cmd_agent_run(cfg: KrakenConfig, args: list[str], use_color: bool = True,
                  auto_approve: bool = False, agent_mode: bool = False):
    if len(args) < 1:
        print(_c("amber", "usage: kraken agent run <name> \"task\" [--agent-mode] [--auto-approve]", use_color))
        return
    name = args[0]
    task = " ".join(args[1:]).strip() or "General task for " + name
    if agent_mode:
        cmd_agent_mode(cfg, task, use_color=use_color, auto_approve=auto_approve, spec_path=name)
    else:
        cmd_direct(cfg, task, use_color=use_color, auto_approve=auto_approve, spec_path=name)


def cmd_agent(cfg: KrakenConfig, args: list[str], use_color: bool = True,
              auto_approve: bool = False, agent_mode: bool = False, force: bool = False):
    if not args:
        cmd_agent_list(cfg, use_color)
        return
    sub = args[0].lower()
    control = ("--agent-mode", "--auto-approve", "--force", "--yes")
    rest = [t for t in args[1:] if t not in control]
    if sub == "new":
        cmd_agent_new(cfg, rest, use_color, force=force)
    elif sub == "list":
        cmd_agent_list(cfg, use_color)
    elif sub in ("show", "info"):
        cmd_agent_show(cfg, rest, use_color)
    elif sub == "edit":
        cmd_agent_edit(cfg, rest, use_color)
    elif sub in ("remove", "rm"):
        cmd_agent_remove(cfg, rest, use_color, yes=force)
    elif sub == "import":
        cmd_agent_import(cfg, rest, use_color)
    elif sub == "run":
        cmd_agent_run(cfg, rest, use_color, auto_approve=auto_approve, agent_mode=agent_mode)
    else:
        print(_c("coral", f"unknown agent subcommand: {sub}", use_color))
        print(_c("amber", "known: new | list | show | edit | remove | import | run", use_color))


def cmd_direct(cfg: KrakenConfig, task: str, use_color: bool = True, auto_approve: bool = False, spec_path: str | None = None):
    print(_banner(use_color))
    print(f"→ {task}\n")
    try:
        spec = build_spec(cfg, spec_path)
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        return
    client = build_client(cfg, spec)
    gate = _gate(cfg, auto_approve)
    memory = build_memory(cfg)

    def on_event(ev):
        pass

    from apps.kraken.engine.agent import run_agent

    agent = run_agent(
        task=task,
        spec=spec,
        client=client,
        workspace=cfg.workspace,
        gate=gate,
        memory=memory,
        callbacks=[on_event],
        max_rounds=int(cfg.get("max_agent_rounds", 12)),
    )
    if agent.result:
        print(agent.result)
    if agent.error:
        print(_c("coral", f"\n[error] {agent.error}", use_color))


def cmd_agent_mode(cfg: KrakenConfig, task: str, use_color: bool = True, auto_approve: bool = False, spec_path: str | None = None):
    print(_banner(use_color))
    print("⚙ AGENT MODE — orchestrator / worker workforce\n")
    print(f"→ {task}\n")
    try:
        spec = build_spec(cfg, spec_path)
    except SpecError as e:
        print(_c("coral", f"[error] {e}", use_color))
        return
    client = build_client(cfg, spec)
    gate = _gate(cfg, auto_approve)
    store = build_store(cfg)

    from apps.kraken.engine.orchestrator import Orchestrator

    orch = Orchestrator(
        client=client,
        workspace=cfg.workspace,
        gate=gate,
        spec=spec,
        max_parallel=int(cfg.get("max_parallel_workers", 3)),
        store=store,
    )
    report = orch.run(task)
    print(report)


# ═══════════════════════════════════════════════════════════════
#  INTERACTIVE REPL
# ═══════════════════════════════════════════════════════════════

def cmd_interactive(cfg: KrakenConfig, auto_approve: bool = False):
    use_color = sys.stdout.isatty()
    client = build_client(cfg)
    memory = build_memory(cfg)

    print(_banner(use_color))
    print(_c("dim", f"Kraken AI v{__version__} — local-first agentic engine", use_color))
    print(_c("dim", f"provider: {cfg.provider} · model: {cfg.model} · workspace: {cfg.workspace}", use_color))
    print(_c("dim", "type /help for commands, /quit to exit\n", use_color))

    try:
        import readline  # noqa: F401  (import for history side effect)
    except ImportError:
        pass

    while True:
        try:
            line = input(_c("seafoam", "kraken> ", use_color))
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line.strip():
            continue
        if line.strip().startswith("/"):
            if not handle_slash(cfg, line.strip(), memory, client):
                break
            continue

        spec_path = cfg.get("active_spec")
        if cfg.get("agent_mode", False):
            cmd_agent_mode(cfg, line, use_color=use_color, auto_approve=auto_approve, spec_path=spec_path)
        else:
            cmd_direct(cfg, line, use_color=use_color, auto_approve=auto_approve, spec_path=spec_path)


def handle_slash(cfg: KrakenConfig, line: str, memory: MemoryStore, client: ChatClient) -> bool:
    parts = shlex.split(line)
    command = parts[0].lower()
    if command in ("/help", "/h", "/?"):
        print("""  commands:
    /help, /?        show this help
    /quit, /q, /exit quit
    /agent-mode      toggle agent mode (multi-agent workforce)
    /agents          list custom agents in the library
    /spec <name>     load a custom agent by name or path (.md)
    /model <name>    switch model
    /models          list downloaded local models + detected api keys
    /provider <name> switch provider (ollama|lmstudio|vllm|llamacpp|openai|anthropic|gemini|...)
    /base-url <url>  set backend URL
    /keys            show detected API keys (masked)
    /setup           auto-detect a working backend
    /auto-approve    toggle automatic approval for state-changing tools
    /memory          show memory (learning loop) stats
    /config          show current config
    /clear           clear screen""")
    elif command in ("/quit", "/q", "/exit"):
        return False
    elif command == "/agent-mode":
        cfg.set("agent_mode", not cfg.get("agent_mode", False))
        state = "ON — workforce mode" if cfg.get("agent_mode") else "OFF — single agent"
        print(f"  agent mode {state}")
    elif command == "/agents":
        store = build_store(cfg)
        rows = store.list_agents()
        if not rows:
            print("  no custom agents in the library")
        for row in rows:
            desc = row["description"] or ""
            roles = f" [{', '.join(row['roles'])}]" if row.get("roles") else ""
            print(f"  {row['name']:<20}{row['model']:<22}{desc[:50]}{roles}")
    elif command == "/spec":
        ref = parts[1] if len(parts) > 1 else ""
        if not ref:
            print("  usage: /spec <agent-name-or-path.md>")
            return True
        try:
            spec = build_spec(cfg, ref)
        except SpecError as e:
            print(f"  {e}")
            return True
        print(f"  loaded agent: {spec.name} (model {spec.model}, tools: {', '.join(spec.tools)})")
        if spec.workforce_roles:
            print(f"  workforce roles: {', '.join(spec.workforce_roles)}")
        cfg.set("active_spec", spec.source_path)
        if spec.default_mode == "agent":
            cfg.set("agent_mode", True)
            print("  default_mode is 'agent' — agent mode ON")
    elif command == "/model":
        if len(parts) < 2:
            print(f"  current model: {cfg.model}")
        else:
            cfg.set("model", parts[1])
            print(f"  model set to {cfg.model}")
    elif command == "/models":
        cmd_models(cfg, use_color=False)
    elif command == "/keys":
        cmd_keys(cfg, [], use_color=False)
    elif command == "/setup":
        cmd_setup(cfg, use_color=False)
    elif command == "/provider":
        if len(parts) < 2:
            print(f"  current provider: {cfg.provider}")
        else:
            provider = parts[1]
            meta = DEFAULT_PROVIDERS.get(provider)
            if provider == "custom":
                print("  custom provider — set /base-url first")
                cfg.set("provider", "custom")
            elif meta:
                cfg.set("provider", provider)
                cfg.set("base_url", meta["base_url"])
                print(f"  provider set to {provider} → {meta['base_url']}")
            else:
                print(f"  unknown provider: {provider} (known: {', '.join(DEFAULT_PROVIDERS)})")
    elif command == "/base-url":
        if len(parts) < 2:
            print(f"  current base url: {cfg.base_url}")
        else:
            cfg.set("base_url", parts[1])
            print(f"  base url set to {cfg.base_url}")
    elif command == "/auto-approve":
        new = not bool(cfg.get("auto_approve", False))
        cfg.set("auto_approve", new)
        print(f"  auto-approve {'ON' if new else 'OFF'}")
    elif command == "/memory":
        stats = memory.stats()
        print(f"  memory entries: {stats['entries']} (enabled: {stats['enabled']})")
        for item in stats.get("top_resolved", []):
            print(f"    - {item['signature'][:70]} (hits {item['hits']})")
    elif command == "/config":
        for key in sorted(cfg.data):
            print(f"  {key:<16} : {cfg.data[key]}")
    elif command == "/clear":
        os.system("clear" if os.name == "posix" else "cls")
    else:
        print(f"  unknown command: {command} (try /help)")
    return True


# ═══════════════════════════════════════════════════════════════
#  ARG PARSING
# ═══════════════════════════════════════════════════════════════

_KNOWN_COMMANDS = ("build", "doctor", "models", "memory", "config", "agent", "keys", "setup", "brain")

_SINGLETON_COMMANDS = ("doctor", "models", "memory", "setup")

_AGENT_SUBCOMMANDS = ("new", "list", "show", "info", "edit", "remove", "rm", "import", "run")

_KEYS_SUBCOMMANDS = ("list", "show", "add", "set", "remove", "rm")

_BRAIN_SUBCOMMANDS = ("scan", "status", "context")


def _first_positional(argv_list: list[str]) -> str | None:
    """First token that is not a flag, so `kraken agent ...` is detectable."""
    for tok in argv_list:
        if not tok.startswith("-"):
            return tok
    return None


def _pick_flags(argv_list: list[str], names: tuple[str, ...]):
    """Extract the given flags (and their values) out of argv; returns (flags, rest).

    Flags that take no value (e.g. --no-color) map to True. Order is preserved.
    """
    out: dict[str, str | bool] = {}
    rest: list[str] = []
    value_free = {"--no-color"}
    i = 0
    while i < len(argv_list):
        tok = argv_list[i]
        if tok in names:
            if tok in value_free:
                out[tok] = True
                i += 1
                continue
            if i + 1 < len(argv_list):
                out[tok] = argv_list[i + 1]
                i += 2
                continue
        rest.append(tok)
        i += 1
    return out, rest


def _dispatch(tokens: list[str]) -> tuple[str | None, list[str]]:
    """Split argv into (subcommand, rest) without shadowing free-form tasks.

    `kraken "build a REST API"` must stay a task, so a token only counts as a
    subcommand when it matches the subcommand's expected arity exactly.
    """
    if not tokens:
        return None, []
    head = tokens[0].lower()
    if head == "build" and len(tokens) == 1:
        return "build", []
    if head in _SINGLETON_COMMANDS and len(tokens) == 1:
        return head, []
    if head == "config" and len(tokens) <= 3:
        return "config", tokens[1:]
    if head == "agent" and (len(tokens) == 1 or tokens[1].lower() in _AGENT_SUBCOMMANDS):
        return "agent", tokens[1:] if len(tokens) > 1 else []
    if head == "keys" and (len(tokens) == 1 or tokens[1].lower() in _KEYS_SUBCOMMANDS):
        return "keys", tokens[1:] if len(tokens) > 1 else []
    if head == "brain" and (len(tokens) == 1 or tokens[1].lower() in _BRAIN_SUBCOMMANDS):
        return "brain", tokens[1:] if len(tokens) > 1 else []
    return None, tokens


def main(argv: list[str] | None = None):
    argv_list = list(argv) if argv is not None else list(sys.argv[1:])

    # `kraken agent ...` owns its own flags (--model/--tools/--desc/...), so it
    # is intercepted before the global parser can reject them.
    if _first_positional(argv_list) == "agent":
        flags, rest = _pick_flags(argv_list, ("--home", "--no-color"))
        rest = [t for t in rest if t.lower() != "agent"]
        cfg = KrakenConfig.load(flags.get("--home"))
        use_color = not flags.get("--no-color") and sys.stdout.isatty()
        return cmd_agent(
            cfg,
            rest,
            use_color=use_color,
            auto_approve="--auto-approve" in rest,
            agent_mode="--agent-mode" in rest,
            force="--force" in rest,
        ) or 0

    parser = argparse.ArgumentParser(
        prog="kraken",
        description="Kraken AI — zero-cost, local-first agentic engine and multi-agent workforce.",
    )
    parser.add_argument(
        "task",
        nargs="*",
        help="task to run (direct command mode), or a subcommand: build|doctor|models|memory|config|agent|keys|setup",
    )
    parser.add_argument("--agent-mode", action="store_true", help="run as a multi-agent workforce")
    parser.add_argument("--auto-approve", action="store_true", help="skip confirmation for tool actions")
    parser.add_argument("--force", action="store_true", help="overwrite / skip confirmation (agent new, agent remove)")
    parser.add_argument("--provider", default=None, help="model backend (ollama|lmstudio|vllm|llamacpp|custom)")
    parser.add_argument("--model", default=None, help="model name, e.g. qwen2.5-coder:14b")
    parser.add_argument("--base-url", default=None, help="backend base URL")
    parser.add_argument("--spec", default=None, help="agent to use: a library name or a path to an .md spec")
    parser.add_argument("--workspace", default=None, help="working directory for file tools")
    parser.add_argument("--home", default=None, help="Kraken home dir (default ~/.kraken)")
    parser.add_argument("--version", action="store_true", help="print version")
    parser.add_argument("--no-color", action="store_true", help="disable ANSI color")

    args = parser.parse_args(argv)
    no_color = bool(args.no_color)
    use_color = not no_color and sys.stdout.isatty()

    cfg = KrakenConfig.load(args.home)
    if args.provider:
        meta = DEFAULT_PROVIDERS.get(args.provider)
        if meta:
            cfg.set("provider", args.provider)
            if "base_url" in meta:
                cfg.set("base_url", meta["base_url"])
        else:
            cfg.set("provider", args.provider)
    if args.model:
        cfg.set("model", args.model)
    if args.base_url:
        cfg.set("base_url", args.base_url)
    if args.workspace:
        cfg.set("workspace", os.path.abspath(args.workspace))

    if args.version:
        print(f"Kraken AI v{__version__}")
        return 0

    command, rest = _dispatch(args.task or [])

    if command == "doctor":
        cmd_doctor(cfg, use_color)
        return 0
    if command == "config":
        cmd_config(cfg, rest, use_color)
        return 0
    if command == "build":
        if not args.spec:
            parser.error("build requires --spec <agent-name-or-path>")
        cmd_build(cfg, args.spec, use_color)
        return 0
    if command == "models":
        cmd_models(cfg, use_color)
        return 0
    if command == "memory":
        cmd_memory(cfg, use_color)
        return 0
    if command == "agent":
        cmd_agent(cfg, rest, use_color=use_color, auto_approve=args.auto_approve, agent_mode=args.agent_mode, force=args.force)
        return 0
    if command == "keys":
        cmd_keys(cfg, rest, use_color)
        return 0
    if command == "setup":
        cmd_setup(cfg, use_color)
        return 0
    if command == "brain":
        cmd_brain(cfg, rest, use_color)
        return 0

    task = " ".join(rest).strip()
    spec_path = args.spec
    if spec_path:
        cfg.set("active_spec", os.path.abspath(spec_path))

    if args.agent_mode:
        cmd_agent_mode(cfg, task or "General code improvement task", use_color=use_color,
                       auto_approve=args.auto_approve, spec_path=spec_path)
        return 0

    if task:
        cmd_direct(cfg, task, use_color=use_color, auto_approve=args.auto_approve, spec_path=spec_path)
        return 0

    if spec_path:
        try:
            spec = build_spec(cfg, spec_path)
        except SpecError as e:
            print(_c("coral", f"ERROR: {e}", use_color))
            return 0
        print(_c("seafoam", f"[OK] agent built: {spec.source_path}", use_color))
        print(spec.describe())
        print(_c("dim", "\nUse it directly:  kraken --spec " + spec.name + " \"your task\"", use_color))
        return 0

    cmd_interactive(cfg, auto_approve=args.auto_approve)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("\n[interrupted]")
        raise SystemExit(130) from None
