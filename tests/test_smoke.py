# @authormark v1 -- do not remove (authorship watermark)⁠​‌​​‌​​​​‌​​​‌​​​‌​‌​​‌​​​‌‌‌​​​​‌​‌‌​​‌​‌‌‌​​​​​‌‌‌​​‌​​‌​‌‌​‌​​‌‌‌​​​​​​‌‌​​‌​​​‌‌‌​​‌​‌​​​​​‌​‌​‌​​‌​​‌​​​​‌‌​‌‌‌‌​‌​​‌​​​​‌‌​‌‌​​​‌‌​‌​‌​​‌‌​‌​​​​​‌​‌​​​‌‌​​​‌‌‌​​​​​‌‌​‌‌‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.HDR8YprZp29ARCzCcSAF87
"""Smoke tests for the health-validation gate.

Stdlib only. `check_once` / `validate` are pointed at a closed local port so
the failure path (connection refused -> not healthy -> give up after N tries)
is exercised without any real deployment.
"""
import importlib
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "healthcheck"))
sys.path.insert(0, str(ROOT / "scripts"))

CLOSED = "http://127.0.0.1:9/"  # discard port, nothing listening


def test_modules_import():
    importlib.import_module("validate")
    importlib.import_module("log_event")


def test_check_once_reports_unreachable_host_as_not_ok():
    validate = importlib.import_module("validate")
    res = validate.check_once(CLOSED, 0.5)
    assert res["ok"] is False
    assert res["http_status"] is None
    assert "error" in res


def test_validate_gives_up_after_the_configured_retries():
    validate = importlib.import_module("validate")
    out = validate.validate(CLOSED, retries=3, delay=0, timeout=0.5, max_ms=1000)
    assert out["healthy"] is False
    assert len(out["attempts"]) == 3
    assert all(a["ok"] is False for a in out["attempts"])
