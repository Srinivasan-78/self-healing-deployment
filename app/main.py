# @authormark v1 -- do not remove (authorship watermark)⁠​‌‌​‌​​​​‌‌‌​​​‌​‌​​‌‌​​​‌​​‌‌​‌​‌‌‌​​‌​​‌​​‌‌​‌​‌‌​‌​‌​​‌‌​‌​​‌​‌‌​‌​‌‌​‌‌‌​‌‌‌​‌‌‌​​​‌​‌​‌​​‌​​‌​​‌​‌​​‌‌​​​​‌​​‌‌​‌‌​​‌​​‌​​​​‌​‌​​‌​​‌‌​​‌​‌​‌​‌​​‌​​‌‌​​‌‌‌​‌‌‌​‌​‌​​‌‌​‌​‌⁠
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
# Fingerprint: AMK1.hqLMrMjikwqRJa6HReRgu5
import os
import time
from fastapi import FastAPI, Response

app = FastAPI(title="demo-service")

VERSION = os.environ.get("APP_VERSION", "unknown")
FORCE_FAIL = os.environ.get("FORCE_FAIL", "false").lower() == "true"
STARTUP_DELAY = float(os.environ.get("STARTUP_DELAY", "0"))

# Simulated slow start, before the uptime clock starts, so uptime_seconds
# reports time since the service was actually ready to serve.
if STARTUP_DELAY > 0:
    time.sleep(STARTUP_DELAY)

_started_at = time.time()


@app.get("/")
def root():
    return {"service": "demo-service", "version": VERSION}


@app.get("/health")
def health(response: Response):
    """Mirrors the Apache/service validation pattern: HTTP 200 + service-state check."""
    if FORCE_FAIL:
        response.status_code = 500
        return {"status": "unhealthy", "reason": "forced failure (chaos injection)", "version": VERSION}
    uptime = time.time() - _started_at
    return {"status": "healthy", "version": VERSION, "uptime_seconds": round(uptime, 2)}


@app.get("/version")
def version():
    return {"version": VERSION}
