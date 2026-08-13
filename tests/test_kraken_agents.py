#!/usr/bin/env python3
"""
Kraken AI — custom agent catalog + spec validation tests (no backend required).

Covers the richer Markdown spec format (workforce_roles, default_mode,
num_ctx, system_prompt override), the AgentStore catalog (CRUD, import,
resolve), workforce role lookup, orchestrator role priority, per-role
client selection, and CLI subcommand dispatch.

Usage:  python3 tests/test_kraken_agents.py
"""

import os
import sys
import tempfile

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from apps.kraken.cli import _dispatch  # noqa: E402
from apps.kraken.engine.agent_store import AgentStore  # noqa: E402
from apps.kraken.engine.orchestrator import Orchestrator  # noqa: E402
from apps.kraken.engine.providers import ChatClient  # noqa: E402
from apps.kraken.engine.spec import AgentSpec, SpecError  # noqa: E402
from apps.kraken.engine.tools import PermissionGate  # noqa: E402

PASS = 0


def check(name: str, condition: bool):
    global PASS
    if not condition:
        print(f"[FAIL] {name}")
        raise SystemExit(1)
    PASS += 1
    print(f"[ ok ] {name}")


def test_spec_validation():
    good = AgentSpec(name="QA_Reviewer", model="qwen2.5-coder:7b", tools=["file_read"])
    good.validate()
    check("valid spec passes", True)

    try:
        AgentSpec(name="9bad name!", model="x").validate()
        check("bad name rejected", False)
    except SpecError:
        check("bad name rejected", True)

    try:
        AgentSpec(name="X", model="x", tools=["rm_rf"]).validate()
        check("unknown tool rejected", False)
    except SpecError:
        check("unknown tool rejected", True)

    try:
        AgentSpec(name="X", model="x", workforce_roles=["boss"]).validate()
        check("unknown role rejected", False)
    except SpecError:
        check("unknown role rejected", True)

    try:
        AgentSpec(name="X", model="x", default_mode="frenzy").validate()
        check("bad default_mode rejected", False)
    except SpecError:
        check("bad default_mode rejected", True)


def test_spec_rich_roundtrip():
    text = """---
name: DevPlanner
model: qwen2.5-coder:32b
tools: [file_read, file_write, file_list]
workforce_roles: [planner, qa]
default_mode: agent
num_ctx: 32768
system_prompt: You are the planning brain. Output only a task list.
---

# DevPlanner

Coordinate the build.
"""
    spec = AgentSpec.from_text(text)
    check("workforce_roles parsed", spec.workforce_roles == ["planner", "qa"])
    check("default_mode parsed", spec.default_mode == "agent")
    check("num_ctx parsed", spec.num_ctx == 32768)
    check("system_prompt override", spec.system_prompt == "You are the planning brain. Output only a task list.")

    rendered = spec.render()
    again = AgentSpec.from_text(rendered)
    check("roles survive render", again.workforce_roles == ["planner", "qa"])
    check("mode survives render", again.default_mode == "agent")
    check("num_ctx survives render", again.num_ctx == 32768)
    check("prompt survives render", again.system_prompt == spec.system_prompt)
    check("role only in body (not frontmatter)", "role:" not in rendered)


def test_store_crud(tmp):
    store = AgentStore(tmp)
    check("empty store", store.names() == [])
    check("empty list", store.list_agents() == [])

    spec = store.create("ReviewCritic", model="qwen2.5-coder:7b", tools=["file_read"], description="nasty reviewer", role="You are harsh.")
    check("create returns spec", spec.name == "ReviewCritic")
    check("create sets source_path", os.path.dirname(spec.source_path) == tmp)
    check("created file exists", os.path.isfile(os.path.join(tmp, "ReviewCritic.md")))
    check("names lists it", store.names() == ["ReviewCritic"])
    check("list_agents row", store.list_agents()[0]["model"] == "qwen2.5-coder:7b")

    check("defaults default model", store.create("B", force=True).model == "qwen2.5-coder:14b")

    try:
        store.create("ReviewCritic")
        check("duplicate rejected", False)
    except SpecError as e:
        check("duplicate rejected", "already exists" in str(e))

    check("force overwrite ok", store.create("ReviewCritic", model="x", force=True).model == "x")

    check("get returns spec", store.get("ReviewCritic").name == "ReviewCritic")
    check("get missing is None", store.get("Nope") is None)

    try:
        store.create("bad name!")
        check("bad create name rejected", False)
    except SpecError:
        check("bad create name rejected", True)

    check("remove returns True", store.remove("ReviewCritic") is True)
    check("remove actually removed", "ReviewCritic" not in store.names())
    check("remove missing False", store.remove("ReviewCritic") is False)


def test_store_import(tmp):
    src = os.path.join(tmp, "External.md")
    with open(src, "w", encoding="utf-8") as f:
        f.write("""---
name: ExternalAgent
model: qwen2.5-coder:7b
tools: [file_read]
---

# ExternalAgent

Do a thing.
""")
    store = AgentStore(os.path.join(tmp, "lib"))
    spec = store.import_file(src)
    check("import copies into library", store.get("ExternalAgent") is not None)
    check("import source_path in library", spec.source_path == store.path_for("ExternalAgent"))

    renamed = store.import_file(src, name="RenamedAgent")
    check("import renames", renamed.name == "RenamedAgent" and store.get("RenamedAgent") is not None)

    try:
        store.import_file(os.path.join(tmp, "Missing.md"))
        check("import missing raises", False)
    except (SpecError, FileNotFoundError):
        check("import missing raises", True)


def test_store_resolve(tmp):
    store = AgentStore(tmp)
    store.create("ReviewCritic", model="m")

    check("resolve by name", store.resolve("ReviewCritic").name == "ReviewCritic")

    src = os.path.join(tmp, "PathAgent.md")
    with open(src, "w", encoding="utf-8") as f:
        f.write("---\nname: PathAgent\nmodel: m\n---\n\n# PathAgent\n\nhi\n")
    check("resolve by path", store.resolve(src).name == "PathAgent")

    try:
        store.resolve("MissingAgent")
        check("resolve missing name raises", False)
    except SpecError as e:
        check("resolve missing name raises", "no agent named" in str(e))

    try:
        store.resolve(os.path.join(tmp, "nope.md"))
        check("resolve missing path raises", False)
    except SpecError as e:
        check("resolve missing path raises", "not found" in str(e))


def test_role_lookup(tmp):
    store = AgentStore(tmp)
    check("no match returns None", store.role_spec("planner") is None)

    store.create("PlannerBrain", model="m", role="")
    spec = store.get("PlannerBrain")
    spec.workforce_roles = ["planner"]
    store.save(spec)

    found = store.role_spec("planner")
    check("role_spec finds agent", found is not None and found.name == "PlannerBrain")
    check("role_spec other role None", store.role_spec("qa") is None)


def test_orchestrator_role_priority(tmp):
    client = ChatClient(provider="ollama", base_url="http://x:11434", model="base-model")
    base = AgentSpec(name="Base", model="base-model", workforce_roles=["planner"])
    store = AgentStore(os.path.join(tmp, "lib"))
    store.create("QaAgent", model="base-model", role="")
    qa = store.get("QaAgent")
    qa.workforce_roles = ["qa"]
    store.save(qa)

    orch = Orchestrator(client=client, workspace=tmp, gate=PermissionGate(), spec=base, store=store)

    got = orch._resolve_role_spec("planner")
    check("base declares role -> base used", got.name == "Base")

    got = orch._resolve_role_spec("qa")
    check("store agent used for role", got is not None and got.name == "QaAgent")

    got = orch._resolve_role_spec("exec")
    check("fallback role-tagged copy", got.name == "Base::exec")

    same = orch._client_for(base)
    check("same model reuses client", same is client)

    custom = AgentSpec(name="Big", model="qwen2.5-coder:32b")
    other = orch._client_for(custom)
    check("different model gets new client", other is not client and other.model == "qwen2.5-coder:32b")


def test_dispatch():
    check("agent list routes", _dispatch(["agent", "list"]) == ("agent", ["list"]))
    check("bare agent routes", _dispatch(["agent"]) == ("agent", []))
    check("agent new routes", _dispatch(["agent", "new", "X"]) == ("agent", ["new", "X"]))
    check("agent remove routes", _dispatch(["agent", "rm", "X"]) == ("agent", ["rm", "X"]))
    check("agent run routes", _dispatch(["agent", "run", "X", "do it"]) == ("agent", ["run", "X", "do it"]))
    check("agent as task stays task", _dispatch(["agent", "mode", "is", "broken"]) == (None, ["agent", "mode", "is", "broken"]))
    check("free-form build stays task", _dispatch(["build", "a", "REST", "API"]) == (None, ["build", "a", "REST", "API"]))
    check("plain build command", _dispatch(["build"]) == ("build", []))
    check("plain doctor", _dispatch(["doctor"]) == ("doctor", []))
    check("free-form doctor stays task", _dispatch(["doctor", "my", "head"]) == (None, ["doctor", "my", "head"]))


def main():
    import argparse

    tmp = tempfile.mkdtemp(prefix="kraken-agents-")
    test_spec_validation()
    test_spec_rich_roundtrip()
    test_store_crud(tmp)
    test_store_import(tmp)
    test_store_resolve(tmp)
    test_role_lookup(tmp)
    test_orchestrator_role_priority(tmp)
    test_dispatch()
    print(f"\n{PASS} checks passed.")


if __name__ == "__main__":
    main()
