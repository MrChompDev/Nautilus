# Kraken AI

**Kraken** is Nautilus OS's local-first agentic AI engine — designed as a
zero-cost, stdlib-only core that talks to any OpenAI-compatible model server:
Ollama, LM Studio, vLLM, or llama.cpp.

> **Restart note:** Kraken was fully implemented in v1 but its application code
> (`apps/kraken/`) was removed in the v2 restart. What survives is its
> *packaging* (`pyproject.toml`), an example *agent spec* (`agents/`), and the
> *training data* under `models/data/`. See [Roadmap](Roadmap.md).

## Packaging — pyproject.toml

Kraken is packaged independently from the OS so it can be installed anywhere:

```sh
pip install .          # installs the `kraken` CLI
pip install ".[gui]"   # + `kraken-gui` desktop app (needs PySide6)
```

Key facts:

- Package name `kraken-ai`, version 1.0.0, MIT, Python ≥ 3.11.
- Engine has **zero mandatory dependencies**; GUI extra pulls PySide6.
- Console scripts:
  - `kraken = apps.kraken.cli:main`
  - `kraken-gui = apps.kraken.main:main`
- Packages declared: `apps.kraken`, `apps.kraken.engine`, `apps.kraken.ui`.

## CLI surface (v1 behavior)

```
kraken models              # list discovered local models + API keys
kraken doctor              # health check + backend recommendation
kraken setup               # auto-configure best backend found
kraken chat                # interactive REPL
kraken keys                # manage API keys (~/.kraken/keys.json)
kraken agent list|new|run  # custom agents
```

## Agent specs

Custom agents are Markdown files with YAML front-matter. The surviving example,
[`agents/DatabaseArchitect.md`](../agents/DatabaseArchitect.md), shows the format:

```yaml
---
name: DatabaseArchitect
model: qwen2.5-coder:14b
tools: [file_read, file_write, terminal_exec]
auto_retry: true
max_retries: 2
description: Database specialist agent for the Nautilus OS stack
---
```

Followed by sections: `# Role`, `# Capabilities`, `# Constraints`. Notable
constraints in this spec reflect OS-level values: tune queries for low-RAM
targets (Pi 500 class), prefer `PRAGMA` tuning over external DB servers, always
write a rollback path before migrating.

At runtime, agent specs live in `~/.kraken/agents/`; the repo copy doubles as
packaging data (`[tool.setuptools.data-files]` → `share/kraken/agents`).

## Training assets — models/

~196 MB of kept training material (not imported by any current code):

- `models/lm/`, `models/imggen/`, `models/trained/` — model workspaces.
- `models/data/` — corpora per persona/domain: `kraken` (code examples),
  `leviathan`, `megalodon`, `charybdis` (corpus/raw JSONL/visual descriptions),
  plus `coding/`, `pentest/`, `writing/`, and a `download_datasets.py` script.
