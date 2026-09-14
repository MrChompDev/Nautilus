"""Minimal Model Context Protocol (MCP) client — stdio transport.

Talks JSON-RPC over a child process's stdin/stdout (newline-delimited JSON),
enough for initialize, tools/list, resources/list and tools/call.
"""

from __future__ import annotations

import json
import os
import queue
import subprocess
import threading

PROTOCOL_VERSION = "2025-06-18"
INIT_TIMEOUT = 15.0
CALL_TIMEOUT = 120.0


class MCPError(Exception):
    pass


class MCPServer:
    def __init__(self, name: str, *, command: str | None = None, args: list[str] | None = None,
                 env: dict | None = None, url: str | None = None):
        self.name = name
        self.command = command
        self.args = args or []
        self.url = url
        self.raw_env = env or {}
        self.proc: subprocess.Popen | None = None
        self.tools: list[dict] = []
        self.resources: list[dict] = []
        self.last_error: str | None = None
        self.connected = False
        self._pending: dict[int, queue.Queue[dict]] = {}
        self._lock = threading.Lock()
        self._next_id = 0
        self._reader: threading.Thread | None = None

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MCPServer {self.name} conn={self.connected} tools={len(self.tools)}>"

    # ── transport ──────────────────────────────────────────────────
    def connect(self) -> MCPServer:
        if self.url:
            self.last_error = "only stdio transport is supported (use command/args)"
            return self
        if not self.command:
            self.last_error = "no command configured"
            return self
        try:
            env = dict(os.environ)
            env.update(self.raw_env)
            self.proc = subprocess.Popen(
                [self.command, *self.args], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, env=env, bufsize=1, text=True, encoding="utf-8",
            )
        except OSError as e:
            self.last_error = f"spawn failed: {e}"
            return self

        self._reader = threading.Thread(target=self._read_loop, daemon=True)
        self._reader.start()

        try:
            init = self._request("initialize", {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "kraken", "version": "1.0"},
            })
            if init is None:
                self.last_error = "initialize handshake failed/timed out"
                return self
            self._notify("notifications/initialized", {})
            self.connected = True
            try:
                tools_res = self._request("tools/list", {})
                self.tools = (tools_res or {}).get("tools") or []
            except MCPError as e:
                self.last_error = f"tools/list: {e}"
            try:
                res_res = self._request("resources/list", {})
                self.resources = (res_res or {}).get("resources") or []
            except MCPError:
                self.resources = []  # resources are optional per spec
        except MCPError as e:
            self.connected = False
            self.last_error = str(e)
        except Exception as e:  # noqa: BLE001 — servers can fail in arbitrary ways
            self.connected = False
            self.last_error = f"connect: {e}"
            try:
                self.close()
            except Exception:
                pass
        return self

    def _read_loop(self) -> None:
        assert self.proc is not None and self.proc.stdout is not None
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                rid = msg.get("id")
                if rid is not None and isinstance(rid, int):
                    with self._lock:
                        q = self._pending.pop(rid, None)
                    if q is not None:
                        q.put(msg)
        except (ValueError, OSError):
            pass

    def _next_request(self) -> tuple[int, queue.Queue[dict]]:
        with self._lock:
            self._next_id += 1
            rid = self._next_id
            q: queue.Queue[dict] = queue.Queue()
            self._pending[rid] = q
            return rid, q

    def _request(self, method: str, params: dict, timeout: float = INIT_TIMEOUT) -> dict | None:
        rid, q = self._next_request()
        frame = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params}) + "\n"
        assert self.proc is not None and self.proc.stdin is not None
        try:
            self.proc.stdin.write(frame)
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError) as e:
            raise MCPError(f"{self.name}: write failed: {e}") from e
        try:
            msg = q.get(timeout=timeout)
        except queue.Empty as e:
            raise MCPError(f"{self.name}: no response to '{method}' (timeout {timeout:.0f}s)") from e
        if "error" in msg and msg.get("error"):
            raise MCPError(f"{self.name}: {msg['error']}")
        return msg.get("result")

    def _notify(self, method: str, params: dict) -> None:
        if self.proc is None or self.proc.stdin is None:
            return
        try:
            self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method, "params": params}) + "\n")
            self.proc.stdin.flush()
        except (BrokenPipeError, OSError):
            pass

    # ── API ────────────────────────────────────────────────────────
    def list_tools(self) -> list[dict]:
        if not self.connected:
            return []
        return list(self.tools)

    def call_tool(self, name: str, arguments: dict | None = None) -> dict:
        if not self.connected:
            raise MCPError(f"{self.name}: server not connected")
        return self._request("tools/call", {"name": name, "arguments": arguments or {}}, timeout=CALL_TIMEOUT) or {}

    def close(self) -> None:
        if self.proc is None:
            return
        if self.proc.poll() is None:
            try:
                self._request("shutdown", {}, timeout=3.0)
            except MCPError:
                pass
        for stream in (self.proc.stdin, self.proc.stdout):
            if stream is None:
                continue
            try:
                stream.close()
            except (BrokenPipeError, OSError, ValueError):
                pass
        try:
            self.proc.terminate()
            self.proc.wait(timeout=3.0)
        except (OSError, subprocess.TimeoutExpired):
            self.proc.kill()
        self.connected = False


def connect_mcp(config) -> list[MCPServer]:
    """Connect every configured server; failures are recorded on the server, not raised."""
    servers = []
    for name, entry in (config.mcp or {}).items():
        server = MCPServer(name, command=entry.get("command"), args=entry.get("args"),
                           env=entry.get("env"), url=entry.get("url"))
        server.connect()
        servers.append(server)
    return servers


def all_tools(servers: list[MCPServer]) -> list[dict]:
    """Flatten every connected server's tools, tagged with the server name."""
    out = []
    for s in servers:
        if not s.connected:
            continue
        for t in s.tools:
            out.append({**t, "__server": s.name})
    return out


def server_for(servers: list[MCPServer], name: str) -> MCPServer | None:
    for s in servers:
        if s.connected and s.name == name:
            return s
    return None