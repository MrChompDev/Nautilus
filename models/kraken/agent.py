"""Kraken agent loop — run a turn, execute any tool calls via MCP, and continue.

Works for both provider styles:
  * local models emit [[tool:name {args}]] markers which the LocalProvider parses
  * remote OpenAI-compatible providers use native function-calling
"""

from __future__ import annotations

from models.kraken import mcp as mcp_mod
from models.kraken.providers import Assistant, ChatMsg, ChatResult, ModelRef, Provider, Tool

MAX_ROUNDS = 6


def tool_display_schema(tools: list[dict]) -> list[dict]:
    """Scalarize schemas for weak local models: strip $schema, defaults, examples."""
    out = []
    for t in tools:
        schema = t.get("inputSchema") or {"type": "object", "properties": {}}
        out.append({
            "name": t.get("name"),
            "description": (t.get("description") or "")[:240],
            "inputSchema": schema,
        })
    return out


def run_turn(provider: Provider, model: ModelRef, messages: list[ChatMsg],
             servers: list[mcp_mod.MCPServer], *,
             temperature: float = 0.7, max_tokens: int = 200, top_k: int = 40,
             on_token: object | None = None, max_rounds: int = MAX_ROUNDS,
             quiet: bool = False, transcript: list[ChatMsg] | None = None) -> ChatResult:
    """Chat with the model, executing any requested MCP tools, until it answers.

    When `transcript` is given, every assistant/tool message produced during the
    turn (including the final assistant answer) is appended to it so the caller
    can persist the full conversation.
    """
    tools = mcp_mod.all_tools(servers)
    schema = tool_display_schema(tools) if tools else None
    if not quiet and tools:
        names = ", ".join(f"{t.get('__server')}/{t['name']}" for t in tools[:5])
        more = "…" if len(tools) > 5 else ""
        print(f"\x1b[90m  [{len(tools)} MCP tools: {names}{more}]\x1b[0m")

    history = list(messages)
    final = ChatResult()
    tool_rounds: list[tuple[ChatMsg, ChatResult]] = []

    for _round in range(max_rounds + 1):
        result = provider.chat(model, history, tools=schema,
                               temperature=temperature, max_tokens=max_tokens, top_k=top_k,
                               on_token=on_token)
        if not result.tool_calls:
            final = result
            if transcript is not None:
                transcript.append(ChatMsg(role=Assistant, content=result.content))
            break

        history.append(ChatMsg(role=Assistant, content=result.content, tool_calls=result.tool_calls))
        if transcript is not None:
            transcript.append(ChatMsg(role=Assistant, content=result.content, tool_calls=result.tool_calls))
        for call in result.tool_calls:
            server = mcp_mod.server_for(servers, call.name.split("/")[0])
            if server is None and "/" in call.name:
                server = mcp_mod.server_for(servers, call.name)
            tool_req = {"name": call.name, "tool_call_id": f"call_{len(tool_rounds)}"}
            if server is None:
                result_text = f"Error: unknown tool '{call.name}'"
            else:
                tname = call.name.split("/")[1] if "/" in call.name else call.name
                try:
                    out = server.call_tool(tname, call.arguments)
                    result_text = _mcp_result_text(out)
                except mcp_mod.MCPError as e:
                    result_text = f"Error: {e}"
            if not quiet:
                src = server.name if server else "?"
                print(f"\n\x1b[36;1m  ⚙ {src}/{call.name}\x1b[0m")
                print(f"\x1b[90m  ↳ {result_text[:300]}\x1b[0m")
            history.append(ChatMsg(role=Tool, content=result_text, tool_call_id=tool_req["tool_call_id"]))
            if transcript is not None:
                transcript.append(ChatMsg(role=Tool, content=result_text, tool_call_id=tool_req["tool_call_id"]))
            tool_rounds.append((ChatMsg(role=Assistant, content=result.content, tool_calls=[call]),
                                ChatResult(content=f"{call.name} → {result_text[:200]}")))

    if final.content == "" and tool_rounds:
        tail = "\n".join(f"- {c[0].tool_calls[0].name}: {c[1].content}" for c in tool_rounds)
        final = ChatResult(content=f"(tool results) {tail}")
    return final


def _mcp_result_text(out: dict) -> str:
    if out.get("isError"):
        return f"Tool error: {out.get('content') or out}"
    content = out.get("content") or []
    if not content:
        return json_fallback(out)
    parts = []
    for block in content:
        if isinstance(block, dict) and block.get("type") == "text":
            parts.append(str(block.get("text", "")))
        else:
            parts.append(str(block))
    return "\n".join(parts)


def json_fallback(out: dict) -> str:
    import json as _json
    try:
        return _json.dumps(out, ensure_ascii=False)[:2000]
    except (TypeError, ValueError):
        return str(out)[:2000]


def summarize_tools(servers: list[mcp_mod.MCPServer]) -> str:
    rows = []
    for s in servers:
        mark = "✓" if s.connected else ("✗ " + (s.last_error or "disconnected"))
        rows.append(f"  {s.name:16} {mark}   {len(s.tools)} tools")
    return "\n".join(rows) or "  (no MCP servers configured — `kraken mcp list`)"


def tools_for_status(servers: list[mcp_mod.MCPServer]) -> str:
    lines = []
    for s in servers:
        if not s.connected:
            continue
        for t in s.tools:
            lines.append(f"  {s.name}/{t.get('name', '?')} — {(t.get('description') or '')[:80]}")
    return "\n".join(lines) or "  (none connected)"