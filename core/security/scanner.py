"""
RED TEAM — local network discovery & scanning (authorized use only).

Everything here targets loopback/private ranges by default. Public/global
addresses require an explicit ``force=True`` because scanning anything you
do not own without permission is illegal in most jurisdictions.
"""
import ipaddress
import socket
import subprocess
import sys
import urllib.request
from concurrent.futures import ThreadPoolExecutor

# Loopback + RFC1918 + link-local + IPv6 equivalents
_PRIVATE_NETS = [
    ipaddress.ip_network(n)
    for n in ("127.0.0.0/8", "10.0.0.0/8", "172.16.0.0/12",
              "192.168.0.0/16", "169.254.0.0/16", "::1/128", "fc00::/7")
]


def _is_private(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host.split("%")[0])
        return any(ip in net for net in _PRIVATE_NETS)
    except ValueError:
        return False


def _require_private(host: str, force: bool):
    if force:
        return
    if not _is_private(host):
        raise ValueError(
            f"Refusing to scan {host!r}: not a loopback/private address. "
            "Pass force=True only if you own this host and are authorized."
        )


def get_local_ips() -> list:
    """All local IPv4 addresses (excludes 127.0.0.1 duplicates)."""
    ips = set()
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            ips.add(info[4][0])
    except OSError:
        pass
    # UDP trick to find the outbound interface IP without sending packets
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass
    return sorted(ips)


def resolve_host(host: str) -> str:
    return socket.gethostbyname(host)


def ping_host(host: str, timeout: int = 2) -> bool:
    """ICMP ping (falls back to TCP connect on platforms without ping)."""
    try:
        if sys.platform == "win32":
            cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), host]
        else:
            cmd = ["ping", "-c", "1", "-W", str(timeout), host]
        result = subprocess.run(cmd, capture_output=True, timeout=timeout + 5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        # Fallback: TCP connect to common admin ports (ICMP often blocked)
        for port in (22, 80, 443, 445, 3389):
            try:
                with socket.create_connection((host, port), timeout=timeout):
                    return True
            except OSError:
                continue
        return False


def ping_sweep(network: str, timeout: int = 2, force: bool = False,
               max_workers: int = 32) -> list:
    """Discover live hosts in a CIDR (e.g. '192.168.1.0/24')."""
    net = ipaddress.ip_network(network, strict=False)
    if net.is_global and not force:
        raise ValueError(
            f"{network} is a public range — refusing sweep. Use force=True only "
            "with explicit authorization."
        )
    hosts = [str(ip) for ip in net.hosts()][:254]
    live = []

    def _probe(h):
        return h if ping_host(h, timeout) else None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        for result in ex.map(_probe, hosts):
            if result:
                live.append(result)
    return sorted(live, key=lambda h: [int(p) for p in h.split(".")])


def port_scan(host: str, ports=None, timeout: float = 1.0, force: bool = False) -> list:
    """TCP connect scan. ports: iterable of ints (default: common set)."""
    _require_private(host, force)
    if ports is None:
        ports = [21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445,
                 993, 995, 1433, 3306, 3389, 5432, 5900, 6379, 8080, 8443,
                 8888, 9090, 27017]
    open_ports = []

    def _check(port):
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return port
        except OSError:
            return None

    with ThreadPoolExecutor(max_workers=64) as ex:
        for result in ex.map(_check, ports):
            if result:
                open_ports.append(result)
    return sorted(open_ports)


def public_ip(timeout: int = 8) -> str:
    """Outbound public IP (used by Anchor to verify VPN/proxy state)."""
    req = urllib.request.Request(
        "https://api.ipify.org", headers={"User-Agent": "Nautilus-Security/1.0"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "replace").strip()
