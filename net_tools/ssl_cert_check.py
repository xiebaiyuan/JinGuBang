#!/usr/bin/env python3
"""Check SSL certificate info and expiry for one or more domains."""

from __future__ import annotations

import argparse
import socket
import ssl
import sys
from datetime import datetime, timezone


def get_cert_info(host: str, port: int = 443, timeout: float = 5.0) -> dict:
    ctx = ssl.create_default_context()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        with ctx.wrap_socket(sock, server_hostname=host) as ssock:
            cert = ssock.getpeercert()
    return cert


def parse_cert_time(t: str) -> datetime:
    return datetime.strptime(t, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)


def format_subject(sub: tuple) -> str:
    parts = []
    for rdn in sub:
        for attr, val in rdn:
            parts.append(f"{attr}={val}")
    return ", ".join(parts)


def get_sans(cert: dict) -> list[str]:
    san = cert.get("subjectAltName", ())
    return [v for t, v in san if t == "DNS"]


def check_one(host: str, port: int, timeout: float) -> int:
    try:
        cert = get_cert_info(host, port, timeout)
    except Exception as exc:
        print(f"\n[FAIL] {host}:{port} - {exc}")
        return 1

    subject = format_subject(cert.get("subject", ()))
    issuer = format_subject(cert.get("issuer", ()))
    not_before = parse_cert_time(cert["notBefore"])
    not_after = parse_cert_time(cert["notAfter"])
    now = datetime.now(timezone.utc)
    days_left = (not_after - now).days
    sans = get_sans(cert)
    serial = cert.get("serialNumber", "n/a")

    status = "OK" if days_left > 0 else "EXPIRED"
    if 0 < days_left <= 30:
        status = "EXPIRING_SOON"

    print(f"\n[{status}] {host}:{port}")
    print(f"  Subject:    {subject}")
    print(f"  Issuer:     {issuer}")
    print(f"  Serial:     {serial}")
    print(f"  Not Before: {not_before.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Not After:  {not_after.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"  Days Left:  {days_left}")
    if sans:
        print(f"  SANs:       {', '.join(sans[:10])}")
        if len(sans) > 10:
            print(f"              ... and {len(sans) - 10} more")

    return 0 if days_left > 0 else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Check SSL certificate info and expiry")
    parser.add_argument("domains", nargs="+", help="Domain(s) to check")
    parser.add_argument("-p", "--port", type=int, default=443, help="Port (default: 443)")
    parser.add_argument("--timeout", type=float, default=5.0, help="Timeout seconds")
    args = parser.parse_args()

    failures = 0
    for domain in args.domains:
        failures += check_one(domain.strip(), args.port, args.timeout)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
