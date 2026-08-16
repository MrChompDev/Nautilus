# Kraken AI

**The local-first agentic engine and multi-agent workforce** at the heart of
Nautilus. Pure-stdlib engine, two surfaces: a CLI and a PySide6 desktop app.

- **Launch:** `python3 apps/kraken/main.py` (GUI), `python3 kraken.py` (CLI),
  or `Ctrl+Alt+K`
- **Memory target:** ~120 MB
- **Engine:** pure Python stdlib — zero mandatory dependencies, never touches Qt

## Overview

Kraken is a local-first AI assistant that runs against your own model server
(Ollama / LM Studio / vLLM / llama.cpp) or any OpenAI-compatible endpoint. The
engine is a separate, installable package (`pip install .` gives you the
`kraken` CLI; `.[gui]` adds `kraken-gui`). It ships with a `nautilus` provider
that runs the in-repo custom-trained models (`models/lm`, `models/imggen`).

## CLI

```sh
kraken models          # discovered local models + API keys
kraken doctor          # health check and backend recommendation
kraken setup           # auto-configure the best backend found
kraken chat            # interactive REPL (readline history, /slash commands)
kraken-gui             # PySide6 desktop app
```

Subcommands: `build`, `doctor`, `models`, `memory`, `config`, `agent`
(new/list/show/edit/remove/import/run), `brain` (scan/status/context
`--workspace <dir>`), `keys` (list/show/add/set/remove), `setup`.

## Engine Architecture

| Module | Role |
| :--- | :--- |
| `engine/spec.py` | Markdown **Agent Builder**: frontmatter (name, model, tools, workforce roles, mode, system prompt) + body → `AgentSpec`. |
| `engine/agent_store.py` | Catalog of `.md` agents in `~/.kraken/agents/`; CRUD, import, role lookup. |
| `engine/providers.py` | Streaming `ChatClient` over plain HTTP — OpenAI-compatible SSE, Ollama native, Anthropic native. |
| `engine/local.py` | `nautilus` provider bridge to the bundled local models + brain context; model fallback coding → writing → pentest. |
| `engine/brain.py` | Persistent "project brain" — scans a workspace (sha1 hashes via ThreadPool) into SQLite (`~/.nautilus/brain.db`), returns top-k file contexts for prompts. |
| `engine/memory.py` | SQLite memory store (`~/.kraken/memory.db`) with token-based pseudo-embedding cosine recall. |
| `engine/agent.py` | Single-agent loop with a **Self-Correction Loop** (recall → re-issue → remember), max 12 rounds, `<tool name="...">{json}</tool>` parsing. |
| `engine/orchestrator.py` | **Workforce ("Agent Mode")**: Planner → parallel exec agents (max 3) → QA/Review → synthesized `=== KRAKEN WORKFORCE REPORT ===`. |
| `engine/tools.py` | Tool registry: `file_read` (512 KB cap), `file_write`, `file_delete`, `file_list`, `terminal_exec` (300 s timeout). **PermissionGate is fail-closed** — no approver wired = tools denied. |
| `engine/discovery.py` | Finds local models (Ollama server + disk, LM Studio GGUF caches, llama.cpp dirs), recommends backends. |
| `engine/keys.py` | Key resolution: `~/.kraken/keys.json` > `~/.env` > env vars; files written `0600`, never logged. |

## Security Model

- **Tool sandboxing** — `ToolContext.resolve_path` confines all file tools to
  the workspace; absolute-path, `..`, and symlink escapes raise `ToolError`.
- **Danger patterns** — `rm -rf /`, fork bombs, `mkfs`, `dd` are rejected.
- **Fail-closed** — until a `confirm_fn` approver is wired in, tool calls are
  denied by default.

## GUI

`KrakenWindow` has a chat panel, a workforce tree, and an agent library
manager. An `EngineWorker` thread runs the engine and marshals events through a
`queue.Queue` drained by a 120 ms `QTimer` — no cross-thread Qt calls.

## Data

All under `~/.kraken/`: `config.json`, `memory.db`, `keys.json`, `agents/*.md`.
Engine code itself is pure stdlib and runs standalone, headless.
