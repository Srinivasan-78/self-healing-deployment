#!/usr/bin/env bash
# @authormark v1 -- do not remove (authorship watermark)
# Copyright (c) 2026 Srinivasan Vijayaraghavan <srinivasan.shyam2000@gmail.com>
# Author: https://github.com/Srinivasan-78
# SPDX-License-Identifier: MIT
set -euo pipefail

# Configuration with sensible defaults
APP_NAME="${APP_NAME:-demo-service}"
IMAGE_NAME="${IMAGE_NAME:-demo-service}"
TARGET_VERSION="${TARGET_VERSION:-${1:-v1}}"
FORCE_FAIL="${FORCE_FAIL:-false}"
HOST_PORT="${HOST_PORT:-8080}"
CONTAINER_PORT="${CONTAINER_PORT:-8080}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
LOG_PATH="${LOG_PATH:-deployment_log/deployments.json}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Deploying $APP_NAME:$TARGET_VERSION ==="

# 1. Build new image
if ! docker build -t "$IMAGE_NAME:$TARGET_VERSION" "$ROOT_DIR/app"; then
  echo "Image build failed. Current deployment left untouched."
  exit 1
fi

# 2. Demote current active container to previous slot
docker rm -f "$APP_NAME-previous" 2>/dev/null || true
if docker ps -q --filter "name=^/${APP_NAME}-active$" | grep -q .; then
  echo "Demoting current active container to previous..."
  docker stop "$APP_NAME-active" >/dev/null
  docker rename "$APP_NAME-active" "$APP_NAME-previous"
fi

# 3. Run new container
echo "Starting new container on port $HOST_PORT..."
if ! docker run -d --name "$APP_NAME-active" -p "$HOST_PORT:$CONTAINER_PORT" \
  -e "APP_VERSION=$TARGET_VERSION" -e "FORCE_FAIL=$FORCE_FAIL" \
  "$IMAGE_NAME:$TARGET_VERSION" >/dev/null; then
  echo "Container start failed! Restoring previous version..."
  docker rm -f "$APP_NAME-active" 2>/dev/null || true
  docker rename "$APP_NAME-previous" "$APP_NAME-active" 2>/dev/null && docker start "$APP_NAME-active" >/dev/null || true
  python3 "$ROOT_DIR/scripts/log_event.py" --status rollback --version "$TARGET_VERSION" --log-path "$LOG_PATH" --reason "container_start_failed"
  exit 1
fi

# 4. Health check validation gate
echo "Validating health check at http://localhost:$HOST_PORT$HEALTH_ENDPOINT..."
if python3 "$ROOT_DIR/healthcheck/validate.py" \
  --url "http://localhost:$HOST_PORT$HEALTH_ENDPOINT" \
  --retries 5 --delay 2 --timeout 3 --backoff 1.5 --max-response-ms 1500; then
  echo "Health check succeeded. Discarding previous container."
  docker rm -f "$APP_NAME-previous" 2>/dev/null || true
  python3 "$ROOT_DIR/scripts/log_event.py" --status success --version "$TARGET_VERSION" --log-path "$LOG_PATH"
  echo "=== Deployment succeeded: $TARGET_VERSION ==="
else
  echo "Health check failed! Rolling back to last-known-good..."
  docker rm -f "$APP_NAME-active" 2>/dev/null || true
  if docker ps -aq --filter "name=^/${APP_NAME}-previous$" | grep -q .; then
    docker rename "$APP_NAME-previous" "$APP_NAME-active"
    docker start "$APP_NAME-active" >/dev/null
    python3 "$ROOT_DIR/scripts/log_event.py" --status rollback --version "$TARGET_VERSION" --log-path "$LOG_PATH" --reason "health_check_failed"
    echo "Rollback restored successfully."
  else
    python3 "$ROOT_DIR/scripts/log_event.py" --status failed --version "$TARGET_VERSION" --log-path "$LOG_PATH" --reason "health_check_failed; no last-known-good"
    echo "No last-known-good container to restore."
  fi
  exit 1
fi
