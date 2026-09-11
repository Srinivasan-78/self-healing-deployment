#!/usr/bin/env python3
# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌​​‌​‌​‌​‌‌​​​‌‌​​‌​​‌‌​‌​​‌​​‌‌​‌‌‌​‌​‌​​‌‌​‌‌‌​‌​‌​‌​​‌​​‌​​‌‌​​‌​​‌​‌​​‌‌​‌​​‌​‌‌​‌​‌‌​‌​​‌​‌​​‌‌​‌​​​‌​‌​‌​‌​‌​‌​‌‌​‌‌​‌​​‌‌​‌‌‌​‌​‌​‌​‌​‌​​‌‌‌‌​‌‌​‌​​​​‌​​‌‌​‌​‌‌‌​‌‌​⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.iV2i7SuI2SKZSEUm7UOhMv
"""Appends a deployment/rollback event to a JSON log the dashboard reads."""
import argparse
import json
import os
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--status", required=True, choices=["success", "rollback", "failed"])
    parser.add_argument("--version", required=True)
    parser.add_argument("--log-path", required=True)
    parser.add_argument("--reason", default=None)
    args = parser.parse_args()

    log_dir = os.path.dirname(os.path.abspath(args.log_path))
    os.makedirs(log_dir, exist_ok=True)

    events = []
    if os.path.exists(args.log_path):
        with open(args.log_path) as f:
            try:
                events = json.load(f)
            except json.JSONDecodeError:
                events = []
    if not isinstance(events, list):
        events = []

    events.append(
        {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "version": args.version,
            "status": args.status,
            "reason": args.reason,
        }
    )

    # Write via a temp file + rename so an interrupted run cannot leave the
    # log truncated or half-written for the dashboard to read.
    tmp_path = args.log_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(events, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, args.log_path)


if __name__ == "__main__":
    main()
