#!/usr/bin/env python3
"""Show processes listening on network ports (macOS/Linux)."""

from __future__ import annotations

import argparse
import platform
import re
import subprocess
import sys


def run(cmd: list[str]) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.stdout
    except Exception:
        return ""


def parse_lsof(output: str) -> list[dict]:
    entries = []
    for line in output.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) < 9:
            continue
        name_field = parts[8] if len(parts) > 8 else ""
        # pattern: host:port or *:port
        m = re.search(r"[:\[](\d+)$", name_field)
        if not m:
            # try the NAME field for IPv6 like [::]:port
            m = re.search(r":(\d+)$", name_field)
        if not m:
            continue
        port = int(m.group(1))
        proto = parts[7].lower() if len(parts) > 7 else "tcp"
        entries.append({
            "pid": parts[1],
            "process": parts[0],
            "user": parts[2],
            "proto": proto.split("(")[0],
            "address": name_field,
            "port": port,
        })
    return entries


def parse_ss(output: str) -> list[dict]:
    entries = []
    for line in output.strip().splitlines()[1:]:
        parts = line.split()
        if len(parts) < 5:
            continue
        proto = parts[0].lower()
        local_addr = parts[3]
        m = re.search(r":(\d+)$", local_addr)
        if not m:
            continue
        port = int(m.group(1))
        proc_info = parts[5] if len(parts) > 5 else ""
        pid_match = re.search(r"pid=(\d+)", proc_info)
        name_match = re.search(r'"([^"]+)"', proc_info)
        entries.append({
            "pid": pid_match.group(1) if pid_match else "?",
            "process": name_match.group(1) if name_match else "?",
            "user": "",
            "proto": proto,
            "address": local_addr,
            "port": port,
        })
    return entries


def get_listeners() -> list[dict]:
    system = platform.system().lower()
    if system == "darwin":
        out = run(["lsof", "-iTCP", "-sTCP:LISTEN", "-nP"])
        out += run(["lsof", "-iUDP", "-nP"])
        return parse_lsof(out)
    else:
        out = run(["ss", "-tulnp"])
        return parse_ss(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Show listening ports and processes")
    parser.add_argument("-p", "--port", type=int, help="Filter by port number")
    parser.add_argument("--proto", choices=["tcp", "udp"], help="Filter by protocol")
    parser.add_argument("--sort", choices=["port", "pid", "process"],
                        default="port", help="Sort by (default: port)")
    args = parser.parse_args()

    entries = get_listeners()
    if not entries:
        print("No listening ports found (may need sudo for full results)")
        return 0

    if args.port:
        entries = [e for e in entries if e["port"] == args.port]
    if args.proto:
        entries = [e for e in entries if args.proto in e["proto"]]

    # deduplicate by (pid, port, proto)
    seen = set()
    unique = []
    for e in entries:
        key = (e["pid"], e["port"], e["proto"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    entries = unique

    sort_key = {"port": lambda e: e["port"], "pid": lambda e: e["pid"],
                "process": lambda e: e["process"].lower()}[args.sort]
    entries.sort(key=sort_key)

    header = f"{'PROTO':<8} {'PORT':>6} {'PID':>8}  {'PROCESS':<20} {'ADDRESS'}"
    print(header)
    print("-" * len(header))
    for e in entries:
        print(f"{e['proto']:<8} {e['port']:>6} {e['pid']:>8}  {e['process']:<20} {e['address']}")

    print(f"\nTotal: {len(entries)} listening")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
