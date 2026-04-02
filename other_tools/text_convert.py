#!/usr/bin/env python3
"""Swiss-army text converter: base64, URL, hex encode/decode, timestamp convert."""

from __future__ import annotations

import argparse
import base64
import sys
import urllib.parse
from datetime import datetime, timezone


def cmd_base64enc(text: str) -> str:
    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def cmd_base64dec(text: str) -> str:
    return base64.b64decode(text).decode("utf-8")


def cmd_urlenc(text: str) -> str:
    return urllib.parse.quote(text, safe="")


def cmd_urldec(text: str) -> str:
    return urllib.parse.unquote(text)


def cmd_hexenc(text: str) -> str:
    return text.encode("utf-8").hex()


def cmd_hexdec(text: str) -> str:
    return bytes.fromhex(text.replace(" ", "").replace("0x", "")).decode("utf-8")


def cmd_ts2date(text: str) -> str:
    ts = float(text)
    # auto-detect seconds vs milliseconds
    if ts > 1e12:
        ts = ts / 1000
    dt = datetime.fromtimestamp(ts, tz=timezone.utc)
    local_dt = datetime.fromtimestamp(ts)
    return f"UTC:   {dt.strftime('%Y-%m-%d %H:%M:%S %Z')}\nLocal: {local_dt.strftime('%Y-%m-%d %H:%M:%S')}"


def cmd_date2ts(text: str) -> str:
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%Y/%m/%d %H:%M:%S",
        "%Y/%m/%d %H:%M",
        "%Y/%m/%d",
    ]
    for fmt in formats:
        try:
            dt = datetime.strptime(text.strip(), fmt)
            ts = int(dt.timestamp())
            return f"Seconds:      {ts}\nMilliseconds: {ts * 1000}"
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {text}")


def cmd_jwt_decode(text: str) -> str:
    """Decode JWT payload (no verification, for inspection only)."""
    import json
    parts = text.strip().split(".")
    if len(parts) != 3:
        raise ValueError("Invalid JWT: expected 3 dot-separated parts")
    payload = parts[1]
    # fix padding
    payload += "=" * (4 - len(payload) % 4)
    decoded = base64.urlsafe_b64decode(payload)
    data = json.loads(decoded)
    return json.dumps(data, indent=2, ensure_ascii=False)


COMMANDS = {
    "b64enc":  ("Base64 encode", cmd_base64enc),
    "b64dec":  ("Base64 decode", cmd_base64dec),
    "urlenc":  ("URL encode", cmd_urlenc),
    "urldec":  ("URL decode", cmd_urldec),
    "hexenc":  ("Hex encode", cmd_hexenc),
    "hexdec":  ("Hex decode", cmd_hexdec),
    "ts2date": ("Timestamp -> date", cmd_ts2date),
    "date2ts": ("Date -> timestamp", cmd_date2ts),
    "jwt":     ("Decode JWT payload", cmd_jwt_decode),
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Text converter: base64, URL, hex, timestamp, JWT",
        epilog="Commands: " + ", ".join(COMMANDS.keys()),
    )
    parser.add_argument("command", choices=COMMANDS.keys(), help="Conversion command")
    parser.add_argument("input", nargs="?", help="Input text (or reads from stdin)")
    args = parser.parse_args()

    if args.input:
        text = args.input
    elif not sys.stdin.isatty():
        text = sys.stdin.read().strip()
    else:
        print("error: provide input as argument or via stdin", file=sys.stderr)
        return 2

    _, func = COMMANDS[args.command]
    try:
        result = func(text)
        print(result)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
