#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

CONDA_ENV_NAME="${CONDA_ENV_NAME:-ksbody}"
RUN_NPM_CI="${RUN_NPM_CI:-auto}"
PYTHON_CMD="python"

if [[ -n "${CONDA_PREFIX:-}" ]]; then
  PYTHON_CMD="python"
elif command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate "$CONDA_ENV_NAME"
  PYTHON_CMD="python"
elif [[ -f "${ROOT_DIR}/.venv/Scripts/activate" ]]; then
  PYTHON_CMD="${ROOT_DIR}/.venv/Scripts/python.exe"
elif [[ -f "${ROOT_DIR}/.venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${ROOT_DIR}/.venv/bin/activate"
  PYTHON_CMD="python"
else
  echo "No active conda env and ${ROOT_DIR}/.venv is missing." >&2
  exit 1
fi

echo "Building frontend..."
cd ksbody/web/frontend
if [[ "${RUN_NPM_CI}" == "1" || "${RUN_NPM_CI}" == "true" || ! -d node_modules ]]; then
  npm ci
fi
npm run build
cd "$ROOT_DIR"

echo ""
echo "  KS Body Analysis Web"
echo "  http://localhost:12010/"
echo ""

exec "${PYTHON_CMD}" -m ksbody web
