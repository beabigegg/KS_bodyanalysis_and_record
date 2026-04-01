#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-ksbody}"
if command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate "$CONDA_ENV_NAME"
fi

echo "Building frontend..."
cd frontend
npm run build
cd ..

echo ""
echo "  KS Recipe Analysis WebUI"
echo "  http://localhost:12010/"
echo ""

exec python app.py
