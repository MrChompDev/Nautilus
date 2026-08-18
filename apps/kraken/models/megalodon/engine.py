"""Megalodon — security/pentest engine.

Rule-based vulnerability scanner + neural analysis + tool-augmented
security assistant. Pure Python, no external dependencies.
"""

from __future__ import annotations

import os
import re
import socket
from collections.abc import Callable

from apps.kraken.core.engine import BaseEngine, EngineResponse
from apps.kraken.core.tools import file_read

# ── Vulnerability database (rule-based) ───────────────────────────

VULN_PATTERNS = [
    {"id": "V001", "name": "Hardcoded secret", "severity": "high",
     "pattern": r"(api_key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]",
     "fix": "Move secrets to environment variables or a .env file."},
    {"id": "V002", "name": "SQL injection risk", "severity": "critical",
     "pattern": r"(execute|cursor\.execute)\s*\(\s*['\"].*%s|\.format\(|f['\"].*\{",
     "fix": "Use parameterized queries instead of string formatting."},
    {"id": "V003", "name": "Shell injection risk", "severity": "critical",
     "pattern": r"os\.system\(|subprocess\.call\(.*shell\s*=\s*True",
     "fix": "Use subprocess.run() with shell=False and a list of arguments."},
    {"id": "V004", "name": "Unsafe YAML load", "severity": "high",
     "pattern": r"yaml\.load\((?!.*Loader)",
     "fix": "Use yaml.safe_load() or yaml.load(data, Loader=yaml.SafeLoader)."},
    {"id": "V005", "name": "Weak hash algorithm", "severity": "medium",
     "pattern": r"hashlib\.(md5|sha1)\(",
     "fix": "Use hashlib.sha256() or stronger for security-sensitive hashing."},
    {"id": "V006", "name": "Predictable random", "severity": "medium",
     "pattern": r"random\.(random|randint|choice|randrange)\(",
     "fix": "Use secrets module for security-sensitive randomness."},
    {"id": "V007", "name": "Debug mode in production", "severity": "high",
     "pattern": r"debug\s*=\s*True|DEBUG\s*=\s*True",
     "fix": "Set debug=False in production. Use environment variables for debug flags."},
    {"id": "V008", "name": "Bind to all interfaces", "severity": "medium",
     "pattern": r"0\.0\.0\.0|bind.*INADDR_ANY",
     "fix": "Bind to 127.0.0.1 or a specific interface in production."},
    {"id": "V009", "name": "Path traversal risk", "severity": "high",
     "pattern": r"open\(.*\+|os\.path\.join\(.*input",
     "fix": "Validate and sanitize file paths. Use os.path.abspath + startswith check."},
    {"id": "V010", "name": "Insecure deserialization", "severity": "critical",
     "pattern": r"pickle\.loads?\(|marshal\.loads?\(",
     "fix": "Avoid unpickling untrusted data. Use JSON or msgpack instead."},
    {"id": "V011", "name": "CORS wildcard", "severity": "medium",
     "pattern": r"Access-Control-Allow-Origin.*\*",
     "fix": "Restrict CORS to specific trusted origins."},
    {"id": "V012", "name": "XML parsing (XXE risk)", "severity": "medium",
     "pattern": r"xml\.etree\.ElementTree\.parse|xml\.dom\.minidom\.parse",
     "fix": "Use defusedxml library to prevent XXE attacks."},
    {"id": "V013", "name": "Eval/exec usage", "severity": "critical",
     "pattern": r"\beval\s*\(|\bexec\s*\(",
     "fix": "Avoid eval/exec. Use ast.literal_eval() for safe evaluation."},
    {"id": "V014", "name": "Insecure temp file", "severity": "medium",
     "pattern": r"tempfile\.mktemp\(|open\('/tmp/",
     "fix": "Use tempfile.mkstemp() or tempfile.NamedTemporaryFile() instead."},
    {"id": "V015", "name": "HTTP without TLS", "severity": "medium",
     "pattern": r"http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)",
     "fix": "Use HTTPS for external connections."},
    {"id": "V016", "name": "Hardcoded IP/hostname", "severity": "low",
     "pattern": r"(?:192\.168|10\.0|172\.(?:1[6-9]|2[0-9]|3[01]))\.\d+\.\d+",
     "fix": "Use environment variables or configuration files for hostnames."},
    {"id": "V017", "name": " Disabled SSL verify", "severity": "high",
     "pattern": r"verify\s*=\s*False|CERT_NONE|check_hostname\s*=\s*False",
     "fix": "Enable SSL certificate verification in production."},
    {"id": "V018", "name": "Unvalidated redirect", "severity": "medium",
     "pattern": r"redirect\(|Redirect\(.*request\.(args|form)",
     "fix": "Validate redirect URLs against a whitelist of allowed domains."},
]

PORT_SCAN_COMMON = [21, 22, 25, 53, 80, 110, 143, 443, 993, 995, 3306, 3389, 5432, 8080, 8443]


# ── Scanners ──────────────────────────────────────────────────────

def scan_code(filepath: str) -> list[dict]:
    """Scan a source file for vulnerability patterns."""
    result = file_read(filepath, limit=5000)
    if not result.ok:
        return []
    findings = []
    lines = result.output.split("\n")
    for i, line in enumerate(lines, 1):
        for vuln in VULN_PATTERNS:
            if re.search(vuln["pattern"], line):
                findings.append({
                    "vuln_id": vuln["id"],
                    "name": vuln["name"],
                    "severity": vuln["severity"],
                    "file": filepath,
                    "line": i,
                    "code": line.strip()[:120],
                    "fix": vuln["fix"],
                })
    return findings


def scan_directory(path: str) -> list[dict]:
    """Recursively scan a directory for vulnerabilities."""
    findings = []
    skip = {".git", "node_modules", "__pycache__", ".venv", "venv", "trained"}
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".yaml", ".yml", ".json", ".toml", ".cfg"}
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in skip]
        for f in files:
            if any(f.endswith(ext) for ext in extensions):
                fp = os.path.join(root, f)
                findings.extend(scan_code(fp))
    return findings


def check_password_strength(password: str) -> dict:
    """Analyze password strength and return score + feedback."""
    score = 0
    feedback = []

    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Use at least 8 characters")
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1

    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append("Add uppercase letters")
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append("Add lowercase letters")
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append("Add numbers")
    if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        score += 1
    else:
        feedback.append("Add special characters (!@#$%^&*)")

    # Check for common patterns
    common = ["password", "123456", "qwerty", "abc123", "letmein", "admin", "welcome"]
    if password.lower() in common:
        score = 0
        feedback = ["This is a commonly used password — avoid it!"]

    if not feedback:
        feedback.append("Strong password!")

    levels = {0: "Very Weak", 1: "Weak", 2: "Fair", 3: "Good", 4: "Strong", 5: "Very Strong", 6: "Excellent", 7: "Excellent"}
    return {
        "score": score,
        "max_score": 7,
        "level": levels.get(score, "Unknown"),
        "feedback": feedback,
        "length": len(password),
    }


def check_dependencies(path: str) -> list[dict]:
    """Check requirements files for unpinned versions."""
    findings = []
    req_files = ["requirements.txt", "requirements.in", "Pipfile"]
    for req in req_files:
        req_path = os.path.join(path, req)
        if os.path.isfile(req_path):
            result = file_read(req_path, limit=1000)
            if not result.ok:
                continue
            for i, line in enumerate(result.output.splitlines(), 1):
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("-"):
                    continue
                # Check for unpinned versions
                if "==" not in line and ">=" not in line and "<=" not in line:
                    findings.append({
                        "vuln_id": "VDEP1",
                        "name": "Unpinned dependency",
                        "severity": "medium",
                        "file": req,
                        "line": i,
                        "code": line,
                        "fix": f"Pin version: {line}==x.y.z",
                    })
    return findings


def port_check(host: str, port: int, timeout: float = 1.0) -> bool:
    """Quick TCP port check."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            return s.connect_ex((host, port)) == 0
    except Exception:
        return False


def scan_ports(host: str, ports: list[int] | None = None) -> list[dict]:
    """Scan common ports on a host."""
    ports = ports or PORT_SCAN_COMMON
    open_ports = []
    for port in ports:
        if port_check(host, port):
            open_ports.append({"port": port, "state": "open"})
    return open_ports


# ── Megalodon engine ──────────────────────────────────────────────

class MegalodonEngine(BaseEngine):
    model_id = "megalodon"

    def __init__(self, cfg):
        self.cfg = cfg

    def respond(
        self,
        messages: list[dict],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        stream: Callable[[str], None] | None = None,
        workspace: str | None = None,
    ) -> EngineResponse:
        t0 = self._tick()
        user_msg = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                user_msg = m.get("content", "")
                break

        lower = user_msg.lower()
        ws = workspace or self.cfg.workspace if hasattr(self.cfg, "workspace") else os.getcwd()

        # Route to appropriate scanner
        if any(k in lower for k in ("scan code", "scan file", "audit", "vulnerability", "vuln")):
            text = self._run_code_scan(user_msg, ws)
        elif any(k in lower for k in ("scan port", "port scan", "network", "open ports")):
            text = self._run_port_scan(user_msg)
        elif any(k in lower for k in ("dependency", "dependencies", "requirements", "packages")):
            text = self._run_dep_check(ws)
        elif any(k in lower for k in ("full scan", "full audit", "security audit", "pentest")):
            text = self._run_full_audit(ws)
        elif any(k in lower for k in ("password", "pass strength", "password strength")):
            text = self._run_password_check(user_msg)
        elif any(k in lower for k in ("help", "what can", "commands")):
            text = self._help_text()
        else:
            text = self._analyze_query(user_msg, ws)

        if stream:
            for ch in text:
                stream(ch)
            stream("\x00")

        return EngineResponse(text=text, elapsed=self._done(t0), model_id=self.model_id)

    def _run_code_scan(self, msg: str, ws: str) -> str:
        # Extract path if mentioned
        path = ws
        for word in msg.split():
            if os.path.exists(word):
                path = word
                break
        findings = scan_directory(path)
        return self._format_findings("Code Vulnerability Scan", findings, path)

    def _run_port_scan(self, msg: str) -> str:
        host = "127.0.0.1"
        for word in msg.split():
            if re.match(r"\d+\.\d+\.\d+\.\d+", word) or word == "localhost":
                host = word
                break
        ports = scan_ports(host)
        lines = ["[Megalodon — Port Scan]\n", f"Target: {host}\n"]
        if ports:
            lines.append("Open ports:")
            for p in ports:
                lines.append(f"  {p['port']:>5}  OPEN")
        else:
            lines.append("No open ports found on common ports.")
        lines.append(f"\nScanned {len(PORT_SCAN_COMMON)} common ports.")
        return "\n".join(lines)

    def _run_dep_check(self, ws: str) -> str:
        findings = check_dependencies(ws)
        return self._format_findings("Dependency Check", findings, ws)

    def _run_full_audit(self, ws: str) -> str:
        parts = []
        parts.append(self._run_code_scan("scan everything", ws))
        parts.append("\n" + "─" * 50 + "\n")
        parts.append(self._run_dep_check(ws))
        parts.append("\n" + "─" * 50 + "\n")
        parts.append(self._run_port_scan("port scan localhost"))
        total = len(scan_directory(ws)) + len(check_dependencies(ws))
        parts.append(f"\n{'═' * 50}")
        parts.append(f"Total findings: {total}")
        parts.append(f"{'═' * 50}")
        return "\n".join(parts)

    def _run_password_check(self, msg: str) -> str:
        # Extract password from message
        password = ""
        for word in msg.split():
            if word.startswith("password") and "=" in word:
                password = word.split("=", 1)[1]
            elif word.startswith("pass") and "=" in word:
                password = word.split("=", 1)[1]
        # Check for quoted password
        import re
        m = re.search(r'["\'](.+?)["\']', msg)
        if m:
            password = m.group(1)

        if not password:
            return (
                "[Megalodon — Password Strength Check]\n\n"
                "Usage: check password <your_password>\n"
                "Example: check password MyStr0ng!Pass\n\n"
                "I'll analyze the strength and provide feedback."
            )

        result = check_password_strength(password)
        lines = [
            "[Megalodon — Password Strength Check]\n",
            f"Password: {'*' * len(password)} (length: {result['length']})",
            f"Score: {result['score']}/{result['max_score']}",
            f"Strength: {result['level']}",
            "",
            "Feedback:",
        ]
        for fb in result['feedback']:
            lines.append(f"  - {fb}")
        return "\n".join(lines)

    def _analyze_query(self, msg: str, ws: str) -> str:
        return (
            f"[Megalodon — Security Analyst]\n\n"
            f"I can help with security analysis. Try:\n"
            f"  \"scan code {ws}\"\n"
            f"     — Scan source files for vulnerability patterns\n\n"
            f"  \"port scan 127.0.0.1\"\n"
            f"     — Check for open ports\n\n"
            f"  \"check dependencies\"\n"
            f"     — Review requirements for unpinned versions\n\n"
            f"  \"full audit\"\n"
            f"     — Run all scanners at once\n\n"
            f"Your query: {msg[:200]}"
        )

    def _format_findings(self, title: str, findings: list[dict], path: str) -> str:
        lines = [f"[Megalodon — {title}]\n", f"Target: {path}\n"]
        if not findings:
            lines.append("No vulnerabilities found. System looks clean.")
            return "\n".join(lines)

        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        findings.sort(key=lambda f: severity_order.get(f["severity"], 9))

        sev_colors = {"critical": "CRIT", "high": "HIGH", "medium": "MED ", "low": "LOW "}
        lines.append(f"Found {len(findings)} issue(s):\n")
        for f in findings:
            sev = sev_colors.get(f["severity"], "??? ")
            lines.append(f"  [{sev}] {f['vuln_id']}: {f['name']}")
            lines.append(f"         {f['file']}:{f['line']}")
            lines.append(f"         Code: {f['code'][:80]}")
            lines.append(f"         Fix:  {f['fix']}")
            lines.append("")

        counts = {}
        for f in findings:
            s = f["severity"]
            counts[s] = counts.get(s, 0) + 1
        summary = ", ".join(f"{v} {k}" for k, v in sorted(counts.items(), key=lambda x: severity_order.get(x[0], 9)))
        lines.append(f"Summary: {summary}")
        return "\n".join(lines)

    def _help_text(self) -> str:
        return (
            "[Megalodon — Security Commands]\n\n"
            "scan code <path>     — Scan source files for vulnerabilities\n"
            "scan port <host>     — Check open ports on a host\n"
            "check dependencies   — Review requirements for security issues\n"
            "full audit           — Run all scanners (code + deps + ports)\n"
            "help                 — Show this help\n\n"
            "Supported vulnerability patterns:\n"
            + "\n".join(f"  {v['id']}: {v['name']} ({v['severity']})" for v in VULN_PATTERNS)
        )
