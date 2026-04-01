#!/usr/bin/env python3
"""Lightweight TCP port scanner for authorized diagnostics."""

from __future__ import annotations

import argparse
import ipaddress
import re
import socket
import sys

COMMON_PORTS = [22, 53, 80, 443, 3306, 5432, 6379, 8080]
HOST_RE = re.compile(r"^(?=.{1,253}$)([a-zA-Z0-9-]{1,63}\.)*[a-zA-Z0-9-]{1,63}$")


def parse_ports(text: str) -> list[int]:
    ports: list[int] = []
    for part in text.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            s, e = part.split("-", maxsplit=1)
            ports.extend(range(int(s), int(e) + 1))
        else:
            ports.append(int(part))
    valid = sorted({p for p in ports if 1 <= p <= 65535})
    return valid


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scan TCP ports")
    parser.add_argument("--host", required=True, help="Target host")
    parser.add_argument(
        "-p", "--ports", default="", help="Ports or ranges, e.g. 22,80,443,8000-8010"
    )
    parser.add_argument(
        "--timeout", type=float, default=0.5, help="Socket timeout seconds"
    )
    parser.add_argument(
        "--top-common", action="store_true", help="Use common ports preset"
    )
    return parser.parse_args()


def is_open(host: str, port: int, timeout: float) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((host, port)) == 0
    except Exception:
        return False
    finally:
        sock.close()


def main() -> int:
    args = parse_args()
    ports = COMMON_PORTS if args.top_common else parse_ports(args.ports)
    if not ports:
        print("error: no ports provided; use -p or --top-common", file=sys.stderr)
        return 2

    host = args.host.strip()
    try:
        ipaddress.ip_address(host)
        host_valid = True
    except ValueError:
        host_valid = bool(HOST_RE.match(host)) and "_" not in host
    if not host_valid:
        print(f"error: invalid host: {args.host}", file=sys.stderr)
        return 2

    try:
        socket.gethostbyname(host)
    except Exception:
        print(f"error: invalid host: {args.host}", file=sys.stderr)
        return 2

    print("warning: scan only hosts you are authorized to test")
    print(f"host: {host}")
    print(f"ports_to_scan: {len(ports)}")

    open_ports = [p for p in ports if is_open(host, p, args.timeout)]
    print(f"open_ports: {open_ports}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
