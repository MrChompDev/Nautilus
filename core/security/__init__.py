"""
Nautilus OS — Security Tooling (Red & Blue Team)

Local, opt-in, educational tooling for authorized security work on THIS
machine only. Nothing here is remote, destructive, or stealthy:

  RED  (core.security.scanner)  -> host discovery, port scan, IP lookup
  BLUE (core.security.monitor)  -> active connections, process watch,
                                   suspicious-tool detection, file integrity,
                                   failed-login reporting

Network scanning is restricted to private/loopback ranges unless you pass
--force. Only scan systems you own or are explicitly authorized to test.
"""

from core.security.monitor import (
    active_connections,
    failed_login_report,
    integrity_check,
    integrity_init,
    running_processes,
    suspicious_process_check,
    write_security_event,
)
from core.security.scanner import (
    get_local_ips,
    ping_host,
    ping_sweep,
    port_scan,
    public_ip,
    resolve_host,
)

__all__ = [
    "active_connections",
    "failed_login_report",
    "get_local_ips",
    "integrity_check",
    "integrity_init",
    "ping_host",
    "ping_sweep",
    "port_scan",
    "public_ip",
    "resolve_host",
    "running_processes",
    "suspicious_process_check",
    "write_security_event",
]
