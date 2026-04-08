#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-ksbody}"
PYTHON_VERSION="${PYTHON_VERSION:-3.11}"
VENV_DIR="${ROOT_DIR}/.venv"
RUN_NPM_CI="${RUN_NPM_CI:-auto}"
PYTHON_CMD="python"

# ─── Python env helpers ───────────────────────────────────────────────────────

python_bin() {
  if command -v python.exe >/dev/null 2>&1; then command -v python.exe; return; fi
  if command -v python3  >/dev/null 2>&1; then command -v python3;  return; fi
  command -v python
}

venv_activate_path() {
  [[ -f "${VENV_DIR}/Scripts/activate" ]] \
    && printf '%s\n' "${VENV_DIR}/Scripts/activate" \
    || printf '%s\n' "${VENV_DIR}/bin/activate"
}

create_venv() {
  local PYTHON_BIN
  PYTHON_BIN="$(python_bin)"
  if command -v wslpath >/dev/null 2>&1 && command -v powershell.exe >/dev/null 2>&1; then
    powershell.exe -NoProfile -Command "python -m venv '$(wslpath -w "${VENV_DIR}")'"
    return
  fi
  if [[ "${PYTHON_BIN}" == *.exe ]]; then
    "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    return
  fi
  "${PYTHON_BIN}" -m venv --copies "${VENV_DIR}"
}

activate_env() {
  if [[ -n "${CONDA_PREFIX:-}" ]]; then
    PYTHON_CMD="python"
    return
  fi

  if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    ENV_YML="${ROOT_DIR}/environment.yml"
    if ! conda env list | awk '{print $1}' | grep -Fxq "${CONDA_ENV_NAME}"; then
      if [[ -f "${ENV_YML}" ]]; then
        conda env create -n "${CONDA_ENV_NAME}" -f "${ENV_YML}"
      else
        conda create -y -n "${CONDA_ENV_NAME}" "python=${PYTHON_VERSION}"
      fi
    else
      if [[ -f "${ENV_YML}" ]]; then
        conda env update -n "${CONDA_ENV_NAME}" -f "${ENV_YML}" --prune
      fi
    fi
    conda activate "${CONDA_ENV_NAME}"
    PYTHON_CMD="python"
    return
  fi

  if [[ -d "${VENV_DIR}" && ! -f "${VENV_DIR}/bin/activate" && ! -f "${VENV_DIR}/Scripts/activate" ]]; then
    rm -rf "${VENV_DIR}"
  fi
  if [[ ! -d "${VENV_DIR}" ]]; then create_venv; fi

  if [[ -f "${VENV_DIR}/Scripts/python.exe" ]]; then
    PYTHON_CMD="${VENV_DIR}/Scripts/python.exe"
    return
  fi

  # shellcheck disable=SC1091
  source "$(venv_activate_path)"
  PYTHON_CMD="python"
}

# ─── Main ─────────────────────────────────────────────────────────────────────

activate_env

echo "Installing Python dependencies..."
"${PYTHON_CMD}" -m pip install --upgrade pip
"${PYTHON_CMD}" -m pip install -e .

echo "Building frontend..."
pushd "${ROOT_DIR}/ksbody/web/frontend" >/dev/null
if [[ "${RUN_NPM_CI}" == "1" || "${RUN_NPM_CI}" == "true" || ! -d node_modules/.bin ]]; then
  npm install
fi
npm run build
popd >/dev/null

echo "Deploy complete. Run './scripts/start.sh start' to launch services."
