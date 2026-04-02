#!/usr/bin/env python3
"""Check HTTP endpoint health: status code, response time, redirects."""

from __future__ import annotations

import argparse
import sys
import time
import urllib.request
import urllib.error
from urllib.parse import urlparse


def check_url(url: str, timeout: float, method: str = "GET",
              follow_redirects: bool = True) -> dict:
    result: dict = {
        "url": url,
        "status": None,
        "reason": None,
        "time_ms": None,
        "content_type": None,
        "content_length": None,
        "redirects": [],
        "error": None,
    }

    class RedirectRecorder(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            result["redirects"].append({"code": code, "location": newurl})
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    if follow_redirects:
        opener = urllib.request.build_opener(RedirectRecorder)
    else:
        opener = urllib.request.build_opener(urllib.request.HTTPHandler)

    req = urllib.request.Request(url, method=method)
    req.add_header("User-Agent", "wukong-health-check/1.0")

    start = time.monotonic()
    try:
        resp = opener.open(req, timeout=timeout)
        elapsed = (time.monotonic() - start) * 1000
        result["status"] = resp.status
        result["reason"] = resp.reason
        result["time_ms"] = round(elapsed, 1)
        result["content_type"] = resp.headers.get("Content-Type", "n/a")
        cl = resp.headers.get("Content-Length")
        result["content_length"] = int(cl) if cl else None
        resp.close()
    except urllib.error.HTTPError as exc:
        elapsed = (time.monotonic() - start) * 1000
        result["status"] = exc.code
        result["reason"] = exc.reason
        result["time_ms"] = round(elapsed, 1)
    except Exception as exc:
        elapsed = (time.monotonic() - start) * 1000
        result["time_ms"] = round(elapsed, 1)
        result["error"] = str(exc)

    return result


def print_result(r: dict) -> bool:
    ok = r["status"] is not None and 200 <= r["status"] < 400

    tag = "OK" if ok else "FAIL"
    status_str = f"{r['status']} {r['reason']}" if r["status"] else "no response"
    print(f"\n[{tag}] {r['url']}")
    print(f"  Status:         {status_str}")
    print(f"  Response Time:  {r['time_ms']} ms")

    if r["content_type"]:
        print(f"  Content-Type:   {r['content_type']}")
    if r["content_length"] is not None:
        print(f"  Content-Length: {r['content_length']} bytes")
    if r["redirects"]:
        print(f"  Redirects ({len(r['redirects'])}):")
        for rd in r["redirects"]:
            print(f"    {rd['code']} -> {rd['location']}")
    if r["error"]:
        print(f"  Error:          {r['error']}")

    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description="Check HTTP endpoint health")
    parser.add_argument("urls", nargs="+", help="URL(s) to check")
    parser.add_argument("--timeout", type=float, default=10.0, help="Timeout seconds")
    parser.add_argument("--method", default="GET", help="HTTP method (default: GET)")
    parser.add_argument(
        "--no-follow", action="store_true", help="Do not follow redirects"
    )
    args = parser.parse_args()

    failures = 0
    for url in args.urls:
        url = url.strip()
        if not urlparse(url).scheme:
            url = "https://" + url
        result = check_url(url, args.timeout, args.method, not args.no_follow)
        if not print_result(result):
            failures += 1

    print(f"\n--- {len(args.urls)} checked, {len(args.urls) - failures} ok, {failures} failed ---")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
