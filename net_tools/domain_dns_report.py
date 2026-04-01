#!/usr/bin/env python3
"""Generate DNS report for a domain."""

from __future__ import annotations

import argparse
import re
import shutil
import socket
import subprocess
import sys

DOMAIN_RE = re.compile(r"^(?=.{1,253}$)([a-zA-Z0-9-]{1,63}\.)+[a-zA-Z]{2,63}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Get DNS records summary")
    parser.add_argument("-d", "--domain", required=True, help="Domain name")
    parser.add_argument(
        "--types",
        default="A,AAAA,CNAME,MX,NS",
        help="Comma-separated record types",
    )
    parser.add_argument("--timeout", type=float, default=2.0, help="Timeout seconds")
    return parser.parse_args()


def query_with_dig(domain: str, rtype: str, timeout: float) -> list[str]:
    if not shutil.which("dig"):
        return []
    cmd = ["dig", "+short", f"+time={int(timeout)}", domain, rtype]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        return []
    return [x.strip() for x in proc.stdout.splitlines() if x.strip()]


def main() -> int:
    args = parse_args()
    domain = args.domain.strip().lower()
    if not DOMAIN_RE.match(domain):
        print(f"error: invalid domain: {domain}", file=sys.stderr)
        return 2

    socket.setdefaulttimeout(args.timeout)
    types = [t.strip().upper() for t in args.types.split(",") if t.strip()]
    print(f"domain: {domain}")
    print(f"types: {','.join(types)}")

    for rtype in types:
        rows: list[str] = []
        try:
            if rtype == "A":
                rows = sorted(set(socket.gethostbyname_ex(domain)[2]))
            else:
                rows = query_with_dig(domain, rtype, args.timeout)
        except Exception:
            rows = []

        print(f"\n[{rtype}]")
        if rows:
            for row in rows:
                print(f"- {row}")
        else:
            print("- (no data)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
