"""Kraken AI — multi-model CLI with opencode-style commands.

Subcommands:
    kraken                      interactive REPL (auto-routing, MCP tools)
    kraken run <msg...> [-m M]  non-interactive answer
    kraken models [provider]    list provider/model pairs
    kraken providers            list configured providers
    kraken auth login|list|logout
    kraken mcp add|list         manage MCP servers
    kraken config path|show|init
    kraken addmodel <id> <provider> [opts]
    kraken addprovider <name> <base_url> [opts]

Config:  ~/.config/kraken/config.json   (override: KRAKEN_CONFIG_DIR / KRAKEN_CONFIG)
Keys:    ~/.config/kraken/auth.json
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TRAINED_DIR = os.path.join(ROOT, "models", "trained")

from models.kraken.agent import run_turn, summarize_tools, tools_for_status  # noqa: E402
from models.kraken.commands import CommandRegistry, render_template  # noqa: E402
from models.kraken.config import EXAMPLES, Auth, Config, config_path  # noqa: E402
from models.kraken.mcp import connect_mcp  # noqa: E402
from models.kraken.providers import (  # noqa: E402
    ChatMsg,
    LocalProvider,
    UnknownModelError,
    bootstrap,
    get_provider,
    model_catalog,
    provider_ids,
    resolve_model,
)
from models.kraken.router import available_models, route  # noqa: E402
from models.kraken.session import Session  # noqa: E402

__version__ = "2.0.0"

# ── gradient palette (deep blue -> seafoam cyan) ───────────────────
DEF_BLUE = (32, 58, 108)
DEF_CYAN = (0, 242, 194)
WS_NAMES = {"coding": "C O D I N G", "writing": "W R I T I N G",
            "pentest": "P E N T E S T", "imggen": "I M G G E N"}


def _rgb(c):
    return f"\x1b[38;2;{c[0]};{c[1]};{c[2]}m"


def _blend(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def gradient_text(text, start=None, end=None):
    if not text:
        return ""
    a = tuple(start) if start else DEF_BLUE
    b = tuple(end) if end else DEF_CYAN
    n = max(len(text) - 1, 1)
    out = []
    for i, ch in enumerate(text):
        out.append(f"{_rgb(_blend(a, b, i / n))}{ch}")
    out.append("\x1b[0m")
    return "".join(out)


BANNER = (
    " _  ___   _____ _   _ _____ _   _ _   _\n"
    "| |/ / | / / ___| | | |  ___| | | | \\ | |\n"
    "| ' /| |/ / |  _| |_| | |_  | | | |  \\| |\n"
    "| . \\|   <| |_| |  _  |  _| | |_| | |\\  |\n"
    "|_|\\_\\_|\\_\\\\____|_| |_|_|   \\___/|_| \\_|\n"
)


def banner():
    return gradient_text(BANNER)


def status_line(model_label, tokens, seconds, tok_s, c=(24, 150, 170)):
    return f"{_rgb(c)}[{model_label}] {tokens} tok · {seconds:.1f}s · {tok_s:.1f} tok/s\x1b[0m"


def _emit(ch: str) -> None:
    sys.stdout.write(ch)
    sys.stdout.flush()


# ────────────────────────── context ───────────────────────────────
class Ctx:
    def __init__(self, config: Config, trained_dir: str = TRAINED_DIR):
        self.config = config
        self.trained_dir = trained_dir
        bootstrap(config, trained_dir)
        self.servers = connect_mcp(config)


# ────────────────────────── subcommands ───────────────────────────
def cmd_models(config: Config, args) -> int:
    catalog = model_catalog(config, TRAINED_DIR)
    if args.provider and args.provider not in {"local", *provider_ids()}:
        ids = ", ".join(provider_ids())
        print(f"  unknown provider '{args.provider}' — providers: {ids}")
        return 1
    shown = 0
    for mid in sorted(catalog):
        entry = catalog[mid]
        if args.provider and entry["provider"] != args.provider:
            continue
        spec = f"{entry['provider']}/{mid}"
        remote = f" → {entry['remote']}" if entry.get("remote") else ""
        print(f"  {gradient_text('  ' + spec):<38} {entry.get('kind', 'text')}{remote}")
        shown += 1
    if shown == 0:
        print(f"  no models for provider '{args.provider}'")
    return 0


def cmd_providers(config: Config, args) -> int:
    auth = Auth.load()
    names = sorted(set(list(config.providers) + provider_ids()))
    for name in names:
        entry = config.providers.get(name)
        r = get_provider(name)
        if name == "local":
            status = "✓ built-in"
            base = "local trained models"
        elif r is not None:
            status = "✓ connected"
            base = entry.get("base_url", "?") if entry else "?"
        else:
            status = "✗ not configured"
            base = (entry or {}).get("base_url", "?")
        key = ""
        if entry and entry.get("type") == "openai":
            has = bool(entry.get("api_key") or entry.get("env_key") or auth.get(name))
            key = "<key>" if has else "(no key)"
        print(f"  {gradient_text(name):<12} {status:<16} {base}  {key}")
    return 0


def cmd_auth(config: Config, args) -> int:
    auth = Auth.load()
    if args.sub in ("list", "ls"):
        if not auth.keys:
            print("  no stored API keys — `kraken auth login -p <provider>`")
            return 0
        for p, k in sorted(auth.keys.items()):
            masked = f"{k[:6]}…{k[-4:]}" if len(k) > 10 else "<short key>"
            print(f"  {p:12} {masked}")
        return 0
    if args.sub == "logout":
        if args.provider and auth.rm(args.provider):
            auth.save()
            print(f"  cleared key for '{args.provider}'")
        else:
            print("  nothing to clear")
        return 0
    # login
    if not args.provider:
        print("  usage: kraken auth login -p <provider> [--key VALUE]")
        return 1
    key = args.key or input("Paste API key: ").strip()
    if not key:
        print("  no key provided")
        return 1
    auth.set(args.provider, key)
    auth.save()
    print(f"  saved key for '{args.provider}' → auth.json")
    return 0


def cmd_mcp(config: Config, args) -> int:
    if args.sub in ("list", "ls"):
        servers = connect_mcp(config)
        print(summarize_tools(servers))
        tools = tools_for_status(servers)
        if tools and tools != "  (none connected)":
            print(tools)
        for s in servers:
            s.close()
        return 0
    # add
    if not args.name:
        print("  usage: kraken mcp add NAME --command CMD [--args ...] [-u URL] [--env K=V ...]")
        return 1
    env = {}
    for kv in args.env or []:
        k, _, v = kv.partition("=")
        env[k] = v
    config.add_mcp(args.name, command=args.command, args=args.args, url=args.url, env=env)
    config.save()
    print(f"  added MCP server '{args.name}' → {config_path()}")
    return 0


def cmd_config(config: Config, args) -> int:
    if args.sub == "path":
        print(config_path())
        return 0
    if args.sub == "init":
        path = config_path()
        if os.path.exists(path):
            print(f"  config already exists: {path}")
            return 1
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(EXAMPLES, f, indent=2)
            f.write("\n")
        print(f"  wrote example config → {path}")
        print("  providers: openai, ollama · models: gpt, llama3 · mcp: filesystem · commands: /tldr")
        return 0
    print(f"# {config_path()}")
    print(json.dumps(config.data, indent=2))
    return 0


def cmd_addmodel(config: Config, args) -> int:
    if not args.model_id or not args.provider:
        print("  usage: kraken addmodel <id> <provider> [--remote NAME] [--kind text|image] "
              "[--temp T] [--top-k K] [--max-tokens N]")
        return 1
    if args.provider != "local" and get_provider(args.provider) is None:
        print(f"  provider '{args.provider}' not registered — add it first: kraken addprovider ...")
        return 1
    config.add_model(args.model_id, args.provider, remote=args.remote, kind=args.kind,
                     temperature=args.temp, top_k=args.top_k, max_tokens=args.max_tokens)
    config.save()
    print(f"  registered model '{args.model_id}' on provider '{args.provider}' → {config_path()}")
    return 0


def cmd_addprovider(config: Config, args) -> int:
    if not args.name or not args.base_url:
        print("  usage: kraken addprovider <name> <base_url> [--api-key VALUE|env:VAR]")
        return 1
    api_key = None
    env_key = None
    if args.api_key:
        if args.api_key.startswith("env:"):
            env_key = args.api_key[4:]
        else:
            api_key = args.api_key
    config.add_provider(args.name, base_url=args.base_url, api_key=api_key, env_key=env_key)
    config.save()
    print(f"  registered provider '{args.name}' → {config_path()}")
    print(f"  add a model: kraken addmodel <id> {args.name} --remote <model-name>")
    return 0


# ────────────────────────── turn execution ────────────────────────
def _turn(ctx: Ctx, sess: Session, model_spec: str, user_text: str,
          temperature: float, max_tokens: int, top_k: int,
          stream: bool = True) -> None:
    if model_spec in ("auto", ""):
        model_spec = route(user_text)

    try:
        ref = resolve_model(model_spec, ctx.config, ctx.trained_dir)
    except UnknownModelError as e:
        print(f"\x1b[1;31m  {e}\x1b[0m")
        return

    provider = get_provider(ref.provider)
    if provider is None:
        print(f"\x1b[1;31m  provider '{ref.provider}' not available for '{model_spec}'\x1b[0m")
        return

    if ref.kind == "image":
        try:
            path = provider.image(ref, user_text)
            sess.add("assistant", f"[generated image: {path}]")
            print(gradient_text(f"\n  ── image rendered → {path}"))
        except Exception as e:
            print(f"\x1b[1;31m  image error: {e}\x1b[0m")
        return

    sess.add("user", user_text)
    msgs = sess.to_messages()
    transcript: list[ChatMsg] = []
    label = f"{provider.id}/{ref.model_id}" if provider.id != "local" else ref.model_id
    print(gradient_text(f"  [{label}] "))

    def sink(ch, _stream=stream):
        if _stream:
            _emit(ch)

    t0 = time.time()
    try:
        result = run_turn(provider, ref, msgs, ctx.servers, temperature=temperature,
                          max_tokens=max_tokens, top_k=top_k, on_token=sink,
                          transcript=transcript, quiet=not stream)
    except Exception as e:
        print(f"\n\x1b[1;31m  inference error: {e}\x1b[0m")
        return

    dt = time.time() - t0
    if transcript:
        sess.append_turns(transcript)
    if stream:
        print()
        print(status_line(label, result.tokens, dt, result.tok_s))
        if result.content and not transcript:
            sess.add("assistant", result.content)


# ────────────────────────── REPL ──────────────────────────────────
def model_tabs(config: Config) -> None:
    catalog = model_catalog(config, TRAINED_DIR)
    labels = [WS_NAMES.get(mid, mid.upper()) for mid in sorted(catalog)]
    if not labels:
        print(gradient_text("  [ no models yet ]"))
        return
    n = len(labels)
    row = "  " + " | ".join(
        f"{_rgb(_blend(DEF_BLUE, DEF_CYAN, i / max(n - 1, 1)))} {labels[i]} \x1b[0m"
        for i in range(n))
    print(row)


def interactive(ctx: Ctx, force_model: str | None) -> None:
    config = ctx.config
    sess = Session()
    reg = CommandRegistry(config)
    current = force_model or config.defaults.get("model") or "auto"

    print(banner())
    model_tabs(config)
    print(gradient_text("  type a prompt · /help for commands · MCP tools auto-available"))

    while True:
        try:
            line = input(gradient_text("\n  ❯ ", start=(24, 70, 140))).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        if line.startswith("/"):
            new_current, stop = _slash(ctx, sess, reg, line, current)
            if stop:
                break
            if isinstance(new_current, str):
                current = new_current
            continue

        model_spec = current if current != "auto" else route(line)
        _turn(ctx, sess, model_spec, line, 0.7, 180, 40)


def _slash(ctx: Ctx, sess: Session, reg: CommandRegistry, line: str, current: str):
    """Handle a slash line. Returns (new_model_or_None, stop)."""
    cmd, _, rest = line.partition(" ")

    if cmd in ("/quit", "/exit", "/q"):
        return None, True
    if cmd in ("/clear", "/new"):
        sess.reset()
        print("\x1b[2J\x1b[H", end="", flush=True)
        print(banner())
        model_tabs(ctx.config)
        return None, False
    if cmd == "/help":
        print(gradient_text("  built-in:"))
        for name in sorted(reg.names()):
            if name in ("q", "exit", "new"):
                continue
            desc = reg.get(name).description
            print(f"  \x1b[90m/{name:<12}\x1b[0m {desc}")
        custom = reg.custom_names()
        if custom:
            print(gradient_text("\n  custom:"))
            for name in custom:
                desc = reg.get(name).description or ""
                print(f"  \x1b[90m/{name:<12}\x1b[0m {desc}")
        return None, False
    if cmd == "/model":
        if rest:
            try:
                resolve_model(rest, ctx.config, TRAINED_DIR)
                print(gradient_text(f"  switched → {rest}"))
                return rest, False
            except UnknownModelError as e:
                print(f"  \x1b[1;31m{e}\x1b[0m")
        else:
            print(f"  current: {current}  |  `kraken models` for the list")
        return None, False
    if cmd == "/models":
        cmd_models(ctx.config, argparse.Namespace(provider=None))
        return None, False
    if cmd == "/providers":
        cmd_providers(ctx.config, argparse.Namespace())
        return None, False
    if cmd == "/history":
        print(gradient_text(sess.export(), start=(90, 140, 200)))
        return None, False
    if cmd in ("/image", "/img"):
        _turn(ctx, sess, "local/imggen", rest or "abyss waves", 0.7, 180, 40)
        return None, False
    if cmd == "/mcp":
        if rest.startswith("add "):
            try:
                tok = shlex.split(rest[4:])
                name = tok[0]
                argv = tok[1:]
                command = None
                args: list[str] = []
                url = None
                i = 0
                while i < len(argv):
                    if argv[i] in ("--command", "-c"):
                        command = argv[i + 1]
                        i += 2
                    elif argv[i] in ("-u", "--url"):
                        url = argv[i + 1]
                        i += 2
                    elif argv[i] == "--args":
                        j = i + 1
                        while j < len(argv) and not argv[j].startswith("--"):
                            args.append(argv[j])
                            j += 1
                        i = j
                    else:
                        args.append(argv[i])
                        i += 1
                if not command and not url:
                    print("  usage: /mcp add NAME --command CMD [--args ...] [-u URL]")
                    return None, False
                ctx.config.add_mcp(name, command=command, args=args or None, url=url)
                ctx.config.save()
                print(f"  added '{name}' — reconnecting…")
                ctx.servers = connect_mcp(ctx.config)
                print(summarize_tools(ctx.servers))
                return None, False
            except (IndexError, ValueError):
                print("  usage: /mcp add NAME --command CMD [--args ...] [-u URL]")
                return None, False
        else:
            print(summarize_tools(ctx.servers))
            tools = tools_for_status(ctx.servers)
            if tools and tools != "  (none connected)":
                print(tools)
            return None, False
    if cmd == "/status":
        print(f"  model : {current}")
        print(f"  turns : {sess.turn_count}")
        print(summarize_tools(ctx.servers))
        return None, False
    if cmd == "/config":
        cmd_config(ctx.config, argparse.Namespace(sub="show"))
        return None, False
    if cmd == "/addmodel":
        try:
            tok = shlex.split(rest)
            mid, prov = tok[0], tok[1]
            ns = argparse.Namespace(model_id=mid, provider=prov, remote=None, kind="text",
                                    temp=0.7, top_k=40, max_tokens=200)
            i = 2
            while i < len(tok):
                if tok[i] in ("--remote", "-r"):
                    ns.remote = tok[i + 1]
                    i += 2
                elif tok[i] in ("--kind", "-k"):
                    ns.kind = tok[i + 1]
                    i += 2
                elif tok[i] == "--temp":
                    ns.temp = float(tok[i + 1])
                    i += 2
                elif tok[i] == "--top-k":
                    ns.top_k = int(tok[i + 1])
                    i += 2
                elif tok[i] == "--max-tokens":
                    ns.max_tokens = int(tok[i + 1])
                    i += 2
                else:
                    i += 1
            if cmd_addmodel(ctx.config, ns) == 0:
                bootstrap(ctx.config, TRAINED_DIR)
        except (IndexError, ValueError):
            print("  usage: /addmodel <id> <provider> [--remote NAME] [--kind text|image] "
                  "[--temp T] [--top-k K] [--max-tokens N]")
        return None, False
    if cmd == "/addprovider":
        try:
            tok = shlex.split(rest)
            name, url = tok[0], tok[1]
            api_key = None
            if len(tok) >= 3 and tok[2] == "--api-key":
                api_key = tok[3]
            if cmd_addprovider(ctx.config, argparse.Namespace(name=name, base_url=url, api_key=api_key)) == 0:
                bootstrap(ctx.config, TRAINED_DIR)
        except (IndexError, ValueError):
            print("  usage: /addprovider <name> <base_url> [--api-key VALUE]")
        return None, False
    if cmd == "/auth":
        tok = rest.split()
        auth = Auth.load()
        if len(tok) == 2:
            auth.set(tok[0], tok[1])
            auth.save()
            print(f"  saved key for '{tok[0]}'")
        elif len(tok) == 1:
            print(f"  key for '{tok[0]}': {'<set>' if auth.get(tok[0]) else '<none>'}")
        else:
            print("  usage: /auth <provider> [KEY]")
        return None, False

    c = reg.get(cmd[1:])
    if c is not None and not c.builtin:
        rendered = render_template(c.template, rest, cwd=ROOT)
        model_spec = c.model or (current if current != "auto" else route(rendered))
        _turn(ctx, sess, model_spec, rendered, 0.7, 180, 40)
        return None, False
    return None, False


# ────────────────────────── run subcommand ────────────────────────
def cmd_run(ctx: Ctx, args) -> int:
    prompt = " ".join(args.message) if getattr(args, "message", None) else args.prompt_args or ""
    if not prompt:
        print("  usage: kraken run <message...> [-m model]")
        return 1
    sess = Session()
    _turn(ctx, sess, args.model or "auto", prompt,
          args.temperature, args.max_new_tokens, args.top_k, stream=True)
    return 0


# ────────────────────────── main ──────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="kraken", description="Kraken multi-model AI CLI")
    ap.add_argument("--version", action="version", version=f"kraken {__version__}")
    ap.add_argument("--model", default=None, help="model to use (id or provider/model)")
    ap.add_argument("--prompt", default=None, help="one-shot prompt (REPL mode)")
    ap.add_argument("--max-new-tokens", type=int, default=180)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-k", type=int, default=40)
    ap.add_argument("--image", action="store_true", help="route prompt to the image model")
    ap.add_argument("--list", action="store_true", help="list local trained models")
    ap.add_argument("--ping", action="store_true", help="verify local models load")

    sub = ap.add_subparsers(dest="subcommand")

    p_run = sub.add_parser("run", help="non-interactive answer")
    p_run.add_argument("message", nargs="*")
    p_run.add_argument("-m", "--model", default=None)
    p_run.add_argument("--max-new-tokens", type=int, default=180)
    p_run.add_argument("--temperature", type=float, default=0.7)
    p_run.add_argument("--top-k", type=int, default=40)

    p_models = sub.add_parser("models", help="list models (provider/model)")
    p_models.add_argument("provider", nargs="?")

    sub.add_parser("providers", help="list configured providers")

    p_auth = sub.add_parser("auth", help="manage API keys")
    p_auth.add_argument("sub", choices=["login", "list", "ls", "logout"], nargs="?",
                        default="list")
    p_auth.add_argument("-p", "--provider", default=None)
    p_auth.add_argument("--key", default=None)

    p_mcp = sub.add_parser("mcp", help="manage MCP servers")
    p_mcp.add_argument("sub", choices=["add", "list", "ls"], nargs="?", default="list")
    p_mcp.add_argument("name", nargs="?")
    p_mcp.add_argument("--command", "-c", default=None)
    p_mcp.add_argument("--args", nargs="+", default=None)
    p_mcp.add_argument("-u", "--url", default=None)
    p_mcp.add_argument("--env", nargs="+", default=None)

    p_cfg = sub.add_parser("config", help="manage configuration")
    p_cfg.add_argument("sub", choices=["path", "show", "init"], nargs="?", default="show")

    p_addmodel = sub.add_parser("addmodel", help="register a model")
    p_addmodel.add_argument("model_id", nargs="?")
    p_addmodel.add_argument("provider", nargs="?")
    p_addmodel.add_argument("--remote", "-r", default=None)
    p_addmodel.add_argument("--kind", "-k", default="text")
    p_addmodel.add_argument("--temp", type=float, default=None)
    p_addmodel.add_argument("--top-k", type=int, default=None)
    p_addmodel.add_argument("--max-tokens", type=int, default=None)

    p_addprov = sub.add_parser("addprovider", help="register an OpenAI-compatible provider")
    p_addprov.add_argument("name", nargs="?")
    p_addprov.add_argument("base_url", nargs="?")
    p_addprov.add_argument("--api-key", default=None)

    return ap


def main(argv: list[str] | None = None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)

    config = Config.load()
    bootstrap(config, TRAINED_DIR)

    if args.subcommand == "models":
        return cmd_models(config, args)
    if args.subcommand == "providers":
        return cmd_providers(config, args)
    if args.subcommand == "auth":
        return cmd_auth(config, args)
    if args.subcommand == "mcp":
        return cmd_mcp(config, args)
    if args.subcommand == "config":
        return cmd_config(config, args)
    if args.subcommand == "addmodel":
        return cmd_addmodel(config, args)
    if args.subcommand == "addprovider":
        return cmd_addprovider(config, args)
    if args.subcommand == "run":
        return cmd_run(Ctx(config), args)

    # ── default (REPL) with legacy flags ──────────────────────────
    local = available_models(TRAINED_DIR)
    if args.list:
        for m in local:
            print(gradient_text("  " + m))
        return 0
    if args.ping:
        prov = LocalProvider(TRAINED_DIR)
        mods = prov.models()
        ok = 0
        for m in mods:
            try:
                prov._lm(m)
                print(f"  {m:10} ok")
                ok += 1
            except Exception as e:
                print(f"  {m:10} FAIL: {e}")
        print(f"{ok}/{len(mods)} models load")
        return 0
    if not local and not config.models:
        print("no models available — train local ones (models/lm/train.py) or configure "
              "remotes (`kraken config init`)")
        return 1

    ctx = Ctx(config)
    if args.prompt:
        spec = "imggen" if args.image else (args.model or "auto")
        ns = argparse.Namespace(message=[], prompt_args=args.prompt, model=spec,
                                temperature=args.temperature,
                                max_new_tokens=args.max_new_tokens, top_k=args.top_k)
        return cmd_run(ctx, ns)

    interactive(ctx, force_model=args.model)
    for s in ctx.servers:
        s.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())