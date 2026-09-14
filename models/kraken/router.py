"""Kraken — task router. Distributes prompts to the right specialized model."""

from __future__ import annotations

import os


def available_models(trained_dir: str) -> list[str]:
    """Return trained model directory names that have weights."""
    names = []
    if os.path.isdir(trained_dir):
        for name in sorted(os.listdir(trained_dir)):
            path = os.path.join(trained_dir, name)
            if os.path.isfile(os.path.join(path, "weights.npz")):
                names.append(name)
    return names


# Keyword -> model routing table. Order matters: first match wins.
ROUTES = (
    ("coding", ("function", "def ", "class ", "import ", "code", "python", "javascript",
                 "typescript", "bash", "script", "program", "api", "endpoint", "sql",
                 "query", "algorithm", "debug", "refactor", "bug", "compile",
                 "variable", "array", "loop", "regex", "syntax", "error handling",
                 "implement", "write code", "generate code", "framework",
                 "library", "module", "package", "react", "vue", "django",
                 "flask", "fastapi", "rust", "golang", "java",
                 "git commit", "pip install", "npm install", "dependency",
                 "return ", "lambda", "binary search")),
    ("writing", ("write", "essay", "story", "poem", "poetry", "article", "blog",
                 "letter", "email", "novel", "fiction", "nonfiction", "prose",
                 "creative writing", "describe", "draft", "rewrite", "edit",
                 "explain", "summarize", "readme", "documentation", "guide",
                 "copywriting", "headline", "caption", "tweet", "speech", "script",
                 "dialogue", "metaphor", "analogy", "tone", "voice", "style",
                 "paragraph", "sentence", "grammar", "vocabulary", "synonym",
                 "haiku", "short story", "writing prompt")),
    ("pentest", ("nmap", "scan", "penetration", "pentest", "hack", "exploit",
                 "vulnerability", "vuln", "sql injection", "xss", "csrf", "ssrf",
                 "phishing", "malware", "payload", "shell", "privilege escalation",
                 "port scan", "enumeration", "recon", "network scan", "password attack",
                 "brute force", "hash cracking", "hashcat", "john", "hydra", "wireshark",
                 "tcpdump", "metasploit", "msf", "security", "firewall",
                 "iptables", "ssl", "tls", "https", "certificate", "cyber", "infosec",
                 "burp", "owasp", "cve", "exploit-db", "attack", "remote",
                 "server exploitation", "web app testing", "api security",
                 "threat model", "incident response", "forensics", "reverse engineering",
                 "buffer overflow", "zero-day", "ransomware", "botnet", "backdoor")),
)

# Model id -> pretty display name for the TUI
MODEL_TITLES = {
    "coding": "C O D I N G",
    "writing": "W R I T I N G",
    "pentest": "P E N T E S T",
    "imggen": "I M G G E N",
    "kraken": "GENERAL",
}


def score(text: str, keywords) -> int:
    low = text.lower()
    return sum(1 for k in keywords if k in low)


def route(prompt: str) -> str:
    """Pick the best model id for a prompt based on keyword scoring."""
    best = None
    best_s = 0
    for model, keywords in ROUTES:
        s = score(prompt, keywords)
        if s > best_s:
            best_s = s
            best = model
    return best if best else "kraken"