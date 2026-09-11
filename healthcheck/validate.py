#!/usr/bin/env python3
# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌‌​‌​​​‌‌​​‌‌​​​‌‌‌​​‌​‌​‌‌​​‌​‌‌‌​​‌‌​‌‌​​​‌​​‌​​​‌​‌​‌‌‌​​​‌​‌​​‌​‌​​‌‌‌​​‌‌​‌‌​‌‌‌​​‌​​​‌‌‌​​‌‌​​‌‌​‌​​​‌‌‌​‌‌‌​‌​​​‌‌​​​‌​​‌​‌​‌‌‌​‌‌​​​‌‌​‌​‌​​‌‌​‌‌‌‌​​‌​​‌‌​​​​​‌​​​‌‌‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.tf9YsbEqJsnG3GtbWcSy0G
"""
Fail-fast validation framework: HTTP 200 checks, response-time thresholds,
and retry/backoff before declaring a deployment unhealthy — the same shape
as an Apache/NLB convergence check, generalized to any HTTP service.

Exit code 0 = healthy, 1 = unhealthy (caller uses this to trigger rollback).
"""
import argparse
import json
import sys
import time
import urllib.request
import urllib.error


def check_once(url: str, timeout: float) -> dict:
    start = time.time()
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            elapsed_ms = round((time.time() - start) * 1000, 1)
            body = json.loads(resp.read().decode())
            return {
                "ok": resp.status == 200 and body.get("status") == "healthy",
                "http_status": resp.status,
                "elapsed_ms": elapsed_ms,
                "body": body,
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "http_status": e.code, "elapsed_ms": None, "body": None, "error": str(e)}
    except Exception as e:
        return {"ok": False, "http_status": None, "elapsed_ms": None, "body": None, "error": str(e)}


def validate(
    url: str,
    retries: int,
    delay: float,
    timeout: float,
    max_ms: float,
    backoff: float = 1.0,
    max_delay: float = 10.0,
) -> dict:
    attempts = []
    wait = delay
    for attempt in range(1, retries + 1):
        result = check_once(url, timeout)
        result["attempt"] = attempt
        attempts.append(result)

        if result["ok"] and result["elapsed_ms"] is not None and result["elapsed_ms"] > max_ms:
            result["ok"] = False
            result["error"] = f"response time {result['elapsed_ms']}ms exceeded threshold {max_ms}ms"

        if result["ok"]:
            return {"healthy": True, "attempts": attempts}

        if attempt < retries:
            result["retry_in_seconds"] = round(wait, 2)
            time.sleep(wait)
            wait = min(wait * backoff, max_delay)

    return {"healthy": False, "attempts": attempts}


def main():
    parser = argparse.ArgumentParser(description="Deployment health validation gate")
    parser.add_argument("--url", required=True)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--delay", type=float, default=2.0)
    parser.add_argument("--timeout", type=float, default=3.0)
    parser.add_argument("--max-response-ms", type=float, default=1500.0)
    parser.add_argument(
        "--backoff",
        type=float,
        default=1.0,
        help="multiplier applied to --delay after each failed attempt (1.0 = fixed delay)",
    )
    parser.add_argument("--max-delay", type=float, default=10.0, help="cap on the backoff delay")
    args = parser.parse_args()

    result = validate(
        args.url,
        args.retries,
        args.delay,
        args.timeout,
        args.max_response_ms,
        backoff=args.backoff,
        max_delay=args.max_delay,
    )
    print(json.dumps(result, indent=2))

    sys.exit(0 if result["healthy"] else 1)


if __name__ == "__main__":
    main()
