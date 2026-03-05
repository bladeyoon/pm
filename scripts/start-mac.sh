#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

docker compose up --build -d
APP_PORT="${APP_PORT:-8010}"
echo "App started at http://127.0.0.1:${APP_PORT}"
