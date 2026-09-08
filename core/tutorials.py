"""Nautilus OS - Tutorial Engine

Step-by-step guided tutorials for tools, with progress tracking
and coin/XP rewards on completion.
"""

from core.profile import Profile

TUTORIALS = {
    "port_scanner": {
        "name": "Port Scanning 101",
        "tool": "port_scanner",
        "category": "Recon",
        "difficulty": "Beginner",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "What is a Port Scan?",
                "text": (
                    "A port scanner checks which ports on a target computer "
                    "are open and accepting connections. Think of it like "
                    "knocking on every door of a ship to see which ones are unlocked."
                ),
            },
            {
                "title": "Common Ports",
                "text": (
                    "Ports 0-1023 are 'well-known' ports:\n"
                    "  21 = FTP (file transfer)\n"
                    "  22 = SSH (secure shell)\n"
                    "  80 = HTTP (web server)\n"
                    "  443 = HTTPS (secure web)\n"
                    "  3306 = MySQL (database)"
                ),
            },
            {
                "title": "TCP Connect Scan",
                "text": (
                    "The simplest scan type tries to complete a TCP handshake "
                    "with each port. If the handshake succeeds, the port is open. "
                    "This is loud but reliable."
                ),
            },
            {
                "title": "Scanning Localhost",
                "text": (
                    "For practice, we'll scan your own machine (localhost/127.0.0.1). "
                    "This is safe and legal since you're scanning yourself. "
                    "Enter 127.0.0.1 as the target."
                ),
            },
            {
                "title": "Reading Results",
                "text": (
                    "Open ports mean services are listening. Each result shows:\n"
                    "  PORT: The port number\n"
                    "  STATE: open, closed, or filtered\n"
                    "  SERVICE: The likely service name\n\n"
                    "Congratulations! You've completed your first port scan tutorial."
                ),
            },
        ],
    },
    "network_map": {
        "name": "Mapping Your Waters",
        "tool": "network_map",
        "category": "Recon",
        "difficulty": "Beginner",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Network Discovery",
                "text": (
                    "Network mapping finds all devices on your local network. "
                    "This is like sonar pings in the ocean - you send out signals "
                    "and see what responds."
                ),
            },
            {
                "title": "ARP Requests",
                "text": (
                    "ARP (Address Resolution Protocol) maps IP addresses to MAC "
                    "addresses. By sending ARP requests to every IP in your subnet, "
                    "we can discover which devices are online."
                ),
            },
            {
                "title": "Your Subnet",
                "text": (
                    "Your local network is typically 192.168.1.x or 10.0.0.x. "
                    "The tool will auto-detect your subnet. Each device that responds "
                    "gets added to the map."
                ),
            },
            {
                "title": "Building the Map",
                "text": (
                    "As devices respond, the map builds a visual topology. "
                    "Your router/gateway appears at the center, with devices "
                    "branching out. This helps you understand your network."
                ),
            },
        ],
    },
    "whois_lookup": {
        "name": "Domain Detective",
        "tool": "whois_lookup",
        "category": "Recon",
        "difficulty": "Beginner",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "What is WHOIS?",
                "text": (
                    "WHOIS queries public registration databases for domain names. "
                    "It reveals who owns a domain, when it was registered, "
                    "and when it expires."
                ),
            },
            {
                "title": "Running a Lookup",
                "text": (
                    "Enter any domain name (e.g., example.com) and the tool "
                    "queries the WHOIS database. Results include registrar, "
                    "creation date, registrant info, and name servers."
                ),
            },
            {
                "title": "OSINT Value",
                "text": (
                    "WHOIS data is a cornerstone of OSINT (Open Source Intelligence). "
                    "It can reveal email addresses, phone numbers, and organizational "
                    "details that help map a target's digital footprint."
                ),
            },
        ],
    },
    "dns_enum": {
        "name": "DNS Depths",
        "tool": "dns_enum",
        "category": "Recon",
        "difficulty": "Intermediate",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "DNS Records",
                "text": (
                    "DNS translates domain names to IP addresses. Different record "
                    "types serve different purposes:\n"
                    "  A = IPv4 address\n"
                    "  AAAA = IPv6 address\n"
                    "  MX = Mail server\n"
                    "  NS = Name server\n"
                    "  TXT = Text records (SPF, DKIM, etc.)"
                ),
            },
            {
                "title": "Enumeration",
                "text": (
                    "DNS enumeration queries all record types for a domain. "
                    "This reveals mail servers, subdomains, text records with "
                    "verification keys, and more."
                ),
            },
            {
                "title": "Security Implications",
                "text": (
                    "TXT records often contain SPF/DKIM data for email security. "
                    "MX records reveal mail infrastructure. NS records show which "
                    "DNS provider hosts the domain."
                ),
            },
        ],
    },
    "vuln_scanner": {
        "name": "Finding Cracks",
        "tool": "vuln_scanner",
        "category": "Red Team",
        "difficulty": "Intermediate",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Vulnerability Scanning",
                "text": (
                    "Vulnerability scanners check targets for known security flaws. "
                    "They compare service versions against databases of known CVEs "
                    "(Common Vulnerabilities and Exposures)."
                ),
            },
            {
                "title": "Scan Types",
                "text": (
                    "  Quick scan: Top 100 common ports\n"
                    "  Standard: Top 1000 ports with version detection\n"
                    "  Deep: All 65535 ports with full service enumeration"
                ),
            },
            {
                "title": "Interpreting Results",
                "text": (
                    "Each finding has a severity:\n"
                    "  CRITICAL: Remote code execution possible\n"
                    "  HIGH: Significant data exposure risk\n"
                    "  MEDIUM: Limited impact\n"
                    "  LOW: Information disclosure\n"
                    "  INFO: Configuration note"
                ),
            },
        ],
    },
    "password_cracker": {
        "name": "Breaking the Lock",
        "tool": "password_cracker",
        "category": "Red Team",
        "difficulty": "Intermediate",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Password Cracking",
                "text": (
                    "Password cracking attempts to recover passwords from hashes. "
                    "We don't attack the system directly - we work with captured "
                    "hashes offline."
                ),
            },
            {
                "title": "Hash Types",
                "text": (
                    "Common hash formats:\n"
                    "  MD5: 32 hex chars (weak, fast to crack)\n"
                    "  SHA-256: 64 hex chars\n"
                    "  bcrypt: starts with $2b$ (slow by design)\n"
                    "  NTLM: Windows password hashes"
                ),
            },
            {
                "title": "Attack Methods",
                "text": (
                    "  Dictionary: Try words from a wordlist\n"
                    "  Brute force: Try all combinations\n"
                    "  Rainbow table: Pre-computed hash lookups\n"
                    "  Rule-based: Dictionary with mutations (add numbers, etc.)"
                ),
            },
        ],
    },
    "log_analyzer": {
        "name": "Reading the Wake",
        "tool": "log_analyzer",
        "category": "Blue Team",
        "difficulty": "Beginner",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Log Analysis",
                "text": (
                    "System logs record every significant event. Analyzing them "
                    "helps detect intrusions, troubleshoot issues, and understand "
                    "system behavior."
                ),
            },
            {
                "title": "Suspicious Patterns",
                "text": (
                    "Watch for:\n"
                    "  Failed login bursts (brute force)\n"
                    "  Logins at unusual hours\n"
                    "  Privilege escalation attempts\n"
                    "  Unusual outbound connections\n"
                    "  Repeated access denied events"
                ),
            },
            {
                "title": "Timeline Construction",
                "text": (
                    "By ordering events chronologically, you can reconstruct "
                    "an attack chain: initial access, lateral movement, "
                    "privilege escalation, and data exfiltration."
                ),
            },
        ],
    },
    "firewall_manager": {
        "name": "Building the Hull",
        "tool": "firewall_manager",
        "category": "Blue Team",
        "difficulty": "Intermediate",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Firewall Rules",
                "text": (
                    "Firewalls control network traffic by allowing or blocking "
                    "connections based on rules. Each rule specifies:\n"
                    "  Source/Destination IP\n"
                    "  Port number\n"
                    "  Protocol (TCP/UDP)\n"
                    "  Action (ALLOW/DENY)"
                ),
            },
            {
                "title": "Rule Order",
                "text": (
                    "Rules are evaluated top-to-bottom. The first matching rule "
                    "applies. Put specific rules before general ones. "
                    "An explicit DENY ALL at the end catches everything else."
                ),
            },
            {
                "title": "Default Deny",
                "text": (
                    "The safest policy is 'default deny' - block everything, "
                    "then explicitly allow only what's needed. This minimizes "
                    "the attack surface."
                ),
            },
        ],
    },
    "cipher_challenges": {
        "name": "The Codebook",
        "tool": "cipher_challenges",
        "category": "Crypto",
        "difficulty": "Beginner",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "Classical Ciphers",
                "text": (
                    "Cryptography has existed for millennia. Classical ciphers "
                    "like Caesar, Atbash, and Vigenere were once used for "
                    "military communications."
                ),
            },
            {
                "title": "Caesar Cipher",
                "text": (
                    "The Caesar cipher shifts each letter by a fixed number. "
                    "With shift 3: A->D, B->E, Z->C. There are only 25 possible "
                    "shifts, making it trivially breakable by brute force."
                ),
            },
            {
                "title": "Base64",
                "text": (
                    "Base64 encodes binary data as ASCII text. It's not encryption "
                    "(it's reversible by design), but it's often confused with it. "
                    "Encoded text uses A-Z, a-z, 0-9, +, and /."
                ),
            },
            {
                "title": "XOR Cipher",
                "text": (
                    "XOR is a fundamental crypto operation. When you XOR a byte "
                    "with a key byte, you get the encrypted byte. XOR again with "
                    "the same key to decrypt. Security depends entirely on key secrecy."
                ),
            },
        ],
    },
    "steganography": {
        "name": "Message in a Bottle",
        "tool": "steganography",
        "category": "Forensics",
        "difficulty": "Advanced",
        "reward_xp": 50,
        "reward_coins": 25,
        "steps": [
            {
                "title": "What is Steganography?",
                "text": (
                    "Steganography hides messages within other data - typically "
                    "images, audio, or video. Unlike encryption, the existence "
                    "of the message itself is hidden."
                ),
            },
            {
                "title": "LSB Steganography",
                "text": (
                    "The most common technique modifies the Least Significant "
                    "Bit of each pixel color channel. Changing the last bit of "
                    "a color value is visually imperceptible but encodes data."
                ),
            },
            {
                "title": "Detection",
                "text": (
                    "Detection methods include:\n"
                    "  Visual analysis (color artifacts)\n"
                    "  Statistical analysis (entropy changes)\n"
                    "  File size anomalies\n"
                    "  Bit plane analysis"
                ),
            },
        ],
    },
}


class TutorialEngine:
    def __init__(self, profile: Profile):
        self.profile = profile
        self._current_tutorial = None
        self._current_step = 0
        self._on_step_change = None
        self._on_complete = None

    def set_callbacks(self, on_step=None, on_complete=None):
        self._on_step_change = on_step
        self._on_complete = on_complete

    def get_available_tutorials(self) -> list[dict]:
        result = []
        for tid, tut in TUTORIALS.items():
            result.append({
                "id": tid,
                "name": tut["name"],
                "tool": tut["tool"],
                "category": tut["category"],
                "difficulty": tut["difficulty"],
                "completed": tid in self.profile.completed_tutorials,
                "steps_total": len(tut["steps"]),
            })
        return result

    def start_tutorial(self, tutorial_id: str) -> bool:
        if tutorial_id not in TUTORIALS:
            return False
        self._current_tutorial = tutorial_id
        self._current_step = 0
        if self._on_step_change:
            self._on_step_change(self.get_current_step())
        return True

    def get_current_step(self) -> dict | None:
        if self._current_tutorial is None:
            return None
        tut = TUTORIALS[self._current_tutorial]
        if self._current_step >= len(tut["steps"]):
            return None
        step = tut["steps"][self._current_step]
        return {
            "tutorial_name": tut["name"],
            "step_index": self._current_step + 1,
            "steps_total": len(tut["steps"]),
            "title": step["title"],
            "text": step["text"],
            "progress": (self._current_step + 1) / len(tut["steps"]),
        }

    def next_step(self) -> bool:
        if self._current_tutorial is None:
            return False
        tut = TUTORIALS[self._current_tutorial]
        self._current_step += 1
        if self._current_step >= len(tut["steps"]):
            self._complete_tutorial()
            return True
        if self._on_step_change:
            self._on_step_change(self.get_current_step())
        return False

    def previous_step(self) -> bool:
        if self._current_tutorial is None or self._current_step <= 0:
            return False
        self._current_step -= 1
        if self._on_step_change:
            self._on_step_change(self.get_current_step())
        return True

    def skip_tutorial(self):
        self._current_tutorial = None
        self._current_step = 0

    def _complete_tutorial(self):
        tid = self._current_tutorial
        tut = TUTORIALS[tid]
        self.profile.complete_tutorial(tid)
        self._current_tutorial = None
        self._current_step = 0
        if self._on_complete:
            self._on_complete({
                "tutorial_id": tid,
                "name": tut["name"],
                "reward_xp": tut["reward_xp"],
                "reward_coins": tut["reward_coins"],
            })
