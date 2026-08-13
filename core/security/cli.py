"""
Nautilus OS — Security Toolkit CLI

Usage:
  py -3.13 -m core.security.cli connections          # blue: active connections
  py -3.13 -m core.security.cli processes            # blue: running processes
  py -3.13 -m core.security.cli suspicious           # blue: flag known offensive tools
  py -3.13 -m core.security.cli logins               # blue: failed-login / lockout report
  py -3.13 -m core.security.cli integrity init       # blue: baseline file hashes
  py -3.13 -m core.security.cli integrity check      # blue: verify integrity
  py -3.13 -m core.security.cli scan --target 127.0.0.1 --ports 22,80,443   # red
  py -3.13 -m core.security.cli sweep --network 192.168.1.0/24              # red
  py -3.13 -m core.security.cli myip                 # red: public IP

Authorized-use-only: scanning public ranges requires --force and explicit
permission to test the target.
"""
import argparse
import sys


def _print_conns(conns):
    if not conns:
        print("No active connections found.")
        return
    # UDP first so it is never hidden behind the 60-row display cap
    conns = sorted(conns, key=lambda c: (0 if c["proto"] == "UDP" else 1, c["state"]))
    print(f"Total active connections: {len(conns)}")
    print(f"{'PROTO':<6}{'LOCAL':<26}{'REMOTE':<26}{'STATE':<12}PID")
    for c in conns[:60]:
        print(f"{c['proto']:<6}{c['local']:<26}{c['remote']:<26}{c['state']:<12}{c['pid']}")
    if len(conns) > 60:
        print(f"... and {len(conns) - 60} more (showing first 60)")


def cmd_connections(args):
    from core.security.monitor import active_connections
    _print_conns(active_connections())


def cmd_processes(args):
    from core.security.monitor import running_processes
    for p in running_processes():
        print(f"{p['pid']:<8}{p['name']}")


def cmd_suspicious(args):
    from core.security.monitor import suspicious_process_check
    flagged = suspicious_process_check()
    if not flagged:
        print("No known offensive/suspicious tool signatures detected.")
        return
    print("[!] POTENTIAL SUSPICIOUS PROCESSES:")
    for f in flagged:
        print(f"  {f['name']} (pid {f['pid']}) - matches '{f['match']}'")


def cmd_logins(args):
    from core.security.monitor import failed_login_report
    report = failed_login_report()
    print("Locked accounts:", report["locked_accounts"] or "none")
    print("\nRecent security events:")
    for e in report["recent_events"][-10:]:
        print(f"  [{e.get('ts')}] {e.get('event')} {e.get('username','')} {e.get('detail','')}")


def cmd_integrity(args):
    from core.security.monitor import integrity_check, integrity_init
    if args.action == "init":
        data = integrity_init()
        print(f"Baseline saved: {len(data)} files hashed (SHA-256)")
    else:
        result = integrity_check()
        if "error" in result:
            print(result["error"])
            return
        if not result["changed"] and not result["missing"]:
            print("Integrity OK — no changes detected.")
        else:
            if result["changed"]:
                print(f"[!] CHANGED files ({len(result['changed'])}):")
                for f in result["changed"]:
                    print(f"  {f}")
            if result["missing"]:
                print(f"[!] MISSING files ({len(result['missing'])}):")
                for f in result["missing"]:
                    print(f"  {f}")


def cmd_scan(args):
    from core.security.scanner import port_scan
    try:
        ports = [int(p) for p in args.ports.split(",")] if args.ports else None
        open_ports = port_scan(args.target, ports=ports, force=args.force)
    except ValueError as e:
        print(f"Refused: {e}")
        return
    if not open_ports:
        print(f"{args.target}: no open ports found in the scanned set.")
    else:
        print(f"{args.target}: open ports -> {', '.join(map(str, open_ports))}")


def cmd_sweep(args):
    from core.security.scanner import ping_sweep
    try:
        live = ping_sweep(args.network, force=args.force)
    except ValueError as e:
        print(f"Refused: {e}")
        return
    print(f"Live hosts in {args.network}: {len(live)}")
    for h in live:
        print(f"  {h}")


def cmd_myip(args):
    from core.security.scanner import get_local_ips, public_ip
    print("Local IPs:", ", ".join(get_local_ips()) or "unknown")
    try:
        print(f"Public IP : {public_ip()}")
    except Exception as e:
        print(f"Public IP : could not be determined ({e})")


def main(argv=None):
    # Windows ANSI consoles choke on some Unicode; degrade gracefully
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
    parser = argparse.ArgumentParser(
        prog="core.security", description="Nautilus OS red/blue team toolkit (local, authorized use only)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("connections", help="blue: show active network connections").set_defaults(func=cmd_connections)
    sub.add_parser("processes", help="blue: list running processes").set_defaults(func=cmd_processes)
    sub.add_parser("suspicious", help="blue: detect known offensive tool signatures").set_defaults(func=cmd_suspicious)
    sub.add_parser("logins", help="blue: failed-login / lockout report").set_defaults(func=cmd_logins)

    p_integrity = sub.add_parser("integrity", help="blue: file integrity baseline & check")
    p_integrity.add_argument("action", choices=["init", "check"])
    p_integrity.set_defaults(func=cmd_integrity)

    p_scan = sub.add_parser("scan", help="red: TCP port scan (private ranges only unless --force)")
    p_scan.add_argument("--target", required=True)
    p_scan.add_argument("--ports", default="")
    p_scan.add_argument("--force", action="store_true")
    p_scan.set_defaults(func=cmd_scan)

    p_sweep = sub.add_parser("sweep", help="red: ping sweep a CIDR (private ranges only unless --force)")
    p_sweep.add_argument("--network", required=True)
    p_sweep.add_argument("--force", action="store_true")
    p_sweep.set_defaults(func=cmd_sweep)

    sub.add_parser("myip", help="red: show local + public IP").set_defaults(func=cmd_myip)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    sys.exit(main())
