"""
BLUE TEAM — local host monitoring & detection.

Consumes data that Nautilus OS already produces (security_log.jsonl from
core.auth) plus live OS telemetry. Detection is signature-based and
intentionally conservative; use it as a starting point, not a guarantee.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SECURITY_LOG = DATA_DIR / "security_log.jsonl"
INTEGRITY_BASELINE = DATA_DIR / "integrity_baseline.json"

# Known offensive/credential-dumping tool names (signature list, local only)
SUSPICIOUS_TOOLS = [
    "mimikatz", "xordump", "procdump", "secretsdump", "crackmapexec",
    "ncat", "nikto", "sqlmap", "hydra", "john the ripper", "hashcat",
    "wireshark", "ettercap", "bettercap", "metasploit", "msfconsole",
    "cobalt strike", "beacon", "xmrig", "miner", "keylogger", "spyware",
]


def _run(cmd: list, timeout: int = 15) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=timeout, errors="replace")
        return result.stdout or ""
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return ""


def write_security_event(event: str, username: str = "", detail: str = ""):
    """Append a security event to the local log (used by other modules too)."""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(SECURITY_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": datetime.now().isoformat(),
                "event": event,
                "username": username,
                "detail": detail,
            }) + "\n")
    except OSError:
        pass


def active_connections() -> list:
    """Parse netstat for ESTABLISHED/LISTENING connections with PIDs.

    Windows UDP rows have no state column (4 fields, not 5), so parsing is
    token-based rather than a fixed 5-column regex."""
    conns = []
    if sys.platform == "win32":
        out = _run(["netstat", "-ano"])
        for line in out.splitlines():
            tokens = line.split()
            if len(tokens) < 4 or tokens[0].upper() not in ("TCP", "UDP"):
                continue
            proto = tokens[0].upper()
            local, remote = tokens[1], tokens[2]
            if proto == "TCP" and len(tokens) >= 5:
                state, pid = tokens[3].upper(), tokens[4]
            else:  # UDP rows omit the state column
                state, pid = "UDP", tokens[3]
            if state in ("ESTABLISHED", "LISTENING", "LISTEN", "UDP"):
                conns.append({
                    "proto": proto,
                    "local": local,
                    "remote": remote,
                    "state": state,
                    "pid": pid,
                })
        return conns
    out = _run(["netstat", "-tunap"])
    pattern = re.compile(
        r"^\s*(tcp|udp)\s+\d+\s+\d+\s+(\S+)\s+(\S+)\s+(\S+)\s+(.+)$"
    )
    for line in out.splitlines():
        m = pattern.match(line)
        if not m:
            continue
        proto, local, remote, state, proc = m.groups()
        proc = proc.split("/")[-1] if "/" in proc else proc
        if state.upper() in ("ESTABLISHED", "LISTENING", "LISTEN"):
            conns.append({
                "proto": proto.upper(),
                "local": local,
                "remote": remote,
                "state": state.upper(),
                "pid": proc,
            })
    return conns


def running_processes() -> list:
    """Name + PID of every running process."""
    if sys.platform == "win32":
        out = _run(["tasklist", "/FO", "CSV", "/NH"])
        procs = []
        for line in out.splitlines():
            parts = [p.strip().strip('"') for p in line.split(",")]
            if len(parts) >= 2 and parts[0]:
                procs.append({"name": parts[0], "pid": parts[1]})
        return procs
    out = _run(["ps", "-eo", "pid,comm"])
    procs = []
    for line in out.splitlines()[1:]:
        parts = line.split(None, 1)
        if len(parts) == 2:
            procs.append({"pid": parts[0], "name": parts[1]})
    return procs


def suspicious_process_check() -> list:
    """Flag running processes whose names match known offensive tools."""
    flagged = []
    for proc in running_processes():
        name = proc["name"].lower()
        if any(tool in name for tool in SUSPICIOUS_TOOLS):
            flagged.append({"name": proc["name"], "pid": proc["pid"],
                            "match": next(t for t in SUSPICIOUS_TOOLS if t in name)})
    return flagged


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def integrity_init(paths=None, baseline: Path = INTEGRITY_BASELINE) -> dict:
    """Build a SHA-256 baseline for directories/files under project root."""
    if paths is None:
        paths = [PROJECT_ROOT / "core", PROJECT_ROOT / "apps"]
    baseline_data = {}
    for root in paths:
        root = Path(root)
        if not root.exists():
            continue
        if root.is_file():
            _walk_baseline(root.parent, [root], baseline_data)
        else:
            files = [p for p in root.rglob("*")
                     if p.is_file() and not any(
                         part in {".git", "__pycache__", "pipcache", "assets",
                                  "data", "logs", ".venv", "node_modules"}
                         for part in p.parts)]
            _walk_baseline(root, files, baseline_data)
    baseline.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline, "w", encoding="utf-8") as f:
        json.dump(baseline_data, f, indent=2, sort_keys=True)
    return baseline_data


def _walk_baseline(root: Path, files, out: dict):
    """Hash files using project-root-relative keys so integrity_check can
    resolve them back to the exact same paths."""
    for f in files:
        try:
            rel = os.path.relpath(f, PROJECT_ROOT).replace("\\", "/")
            out[rel] = _hash_file(f)
        except (OSError, PermissionError):
            continue


def integrity_check(baseline: Path = INTEGRITY_BASELINE) -> dict:
    """Compare current files against the stored baseline.

    Returns {"changed": [...], "missing": [...]}."""
    if not baseline.exists():
        return {"error": "No baseline found — run 'integrity init' first"}
    with open(baseline, encoding="utf-8") as f:
        saved = json.load(f)
    project = PROJECT_ROOT
    changed, missing = [], []
    for rel, expected in saved.items():
        p = project / rel
        if not p.exists():
            missing.append(rel)
            continue
        try:
            if _hash_file(p) != expected:
                changed.append(rel)
        except (OSError, PermissionError):
            changed.append(rel)
    return {"changed": changed, "missing": missing}


def failed_login_report() -> dict:
    """Aggregate lockout state from accounts.json + the security event log."""
    report = {"locked_accounts": [], "recent_events": []}
    try:
        with open(DATA_DIR / "accounts.json", encoding="utf-8") as f:
            accounts = json.load(f)
        now = datetime.now().timestamp()
        for name, acct in accounts.items():
            lockout = acct.get("lockout_until")
            if lockout:
                try:
                    if float(lockout) > now:
                        report["locked_accounts"].append({
                            "username": name,
                            "failed_attempts": acct.get("failed_attempts", 0),
                        })
                except (TypeError, ValueError):
                    pass
    except (OSError, json.JSONDecodeError):
        pass
    if SECURITY_LOG.exists():
        try:
            with open(SECURITY_LOG, encoding="utf-8") as f:
                for line in f.readlines()[-20:]:
                    line = line.strip()
                    if line:
                        try:
                            report["recent_events"].append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
        except OSError:
            pass
    return report
