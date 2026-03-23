#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-base}"
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate "$CONDA_ENV_NAME"
fi

APP_HOST="${APP_HOST:-0.0.0.0}"
APP_PORT="${APP_PORT:-12010}"
APP_MODE="${APP_MODE:-dev}"

if [[ "$APP_MODE" == "dev" ]]; then
  exec uvicorn app:app --app-dir backend --host "$APP_HOST" --port "$APP_PORT" --reload
fi

exec uvicorn app:app --app-dir backend --host "$APP_HOST" --port "$APP_PORT"

