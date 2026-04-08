#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONDA_ENV_NAME="${CONDA_ENV_NAME:-ksbody}"
PYTHON_CMD="python"
LOG_DIR="${ROOT_DIR}/logs"
PID_FILE="${LOG_DIR}/ksbody.pid"
LOG_FILE="${LOG_DIR}/ksbody-all.log"
APP_PORT="${APP_PORT:-12010}"

# ─── Resolve Python command ───────────────────────────────────────────────────

activate_env() {
  if [[ -n "${CONDA_PREFIX:-}" ]]; then
    PYTHON_CMD="python"
    return
  fi
  if command -v conda >/dev/null 2>&1; then
    eval "$(conda shell.bash hook)"
    conda activate "${CONDA_ENV_NAME}"
    PYTHON_CMD="python"
    return
  fi
  if [[ -f "${ROOT_DIR}/.venv/Scripts/python.exe" ]]; then
    PYTHON_CMD="${ROOT_DIR}/.venv/Scripts/python.exe"
    return
  fi
  if [[ -f "${ROOT_DIR}/.venv/bin/activate" ]]; then
    # shellcheck disable=SC1091
    source "${ROOT_DIR}/.venv/bin/activate"
    PYTHON_CMD="python"
    return
  fi
  echo "No conda env or .venv found. Run deploy.sh first." >&2
  exit 1
}

# ─── PID / port helpers ───────────────────────────────────────────────────────

read_pid() {
  [[ -f "${PID_FILE}" ]] && cat "${PID_FILE}" || echo ""
}

is_running() {
  local pid
  pid="$(read_pid)"
  [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null
}

release_port() {
  local pids
  pids="$(lsof -ti ":${APP_PORT}" 2>/dev/null || true)"
  if [[ -n "${pids}" ]]; then
    echo "Releasing port ${APP_PORT} (pid ${pids})..."
    kill -TERM ${pids} 2>/dev/null || true
    sleep 1
    pids="$(lsof -ti ":${APP_PORT}" 2>/dev/null || true)"
    [[ -n "${pids}" ]] && kill -KILL ${pids} 2>/dev/null || true
  fi
}

# ─── Commands ─────────────────────────────────────────────────────────────────

do_start() {
  if is_running; then
    echo "ksbody is already running (pid=$(read_pid))."
    return 0
  fi

  activate_env
  mkdir -p "${LOG_DIR}"
  release_port

  echo "Starting ksbody (pipeline + web)..."
  nohup "${PYTHON_CMD}" -m ksbody all >> "${LOG_FILE}" 2>&1 &
  echo $! > "${PID_FILE}"
  echo "ksbody started (pid=$(read_pid))."
  echo "  Web:  http://localhost:${APP_PORT}/"
  echo "  Logs: ${LOG_FILE}"
}

do_stop() {
  local pid
  pid="$(read_pid)"

  if [[ -z "${pid}" ]] || ! kill -0 "${pid}" 2>/dev/null; then
    echo "ksbody is not running."
    rm -f "${PID_FILE}"
    release_port
    return 0
  fi

  echo "Stopping ksbody (pid=${pid})..."
  kill -TERM "${pid}"

  local waited=0
  while kill -0 "${pid}" 2>/dev/null; do
    sleep 1
    (( waited++ ))
    if (( waited >= 15 )); then
      echo "Did not stop in time; force-killing."
      kill -KILL "${pid}" 2>/dev/null || true
      break
    fi
  done

  rm -f "${PID_FILE}"
  release_port
  echo "ksbody stopped."
}

do_restart() {
  do_stop
  do_start
}

do_status() {
  if is_running; then
    echo "ksbody is running (pid=$(read_pid))."
  else
    echo "ksbody is not running."
    rm -f "${PID_FILE}"
  fi
}

# ─── Main ─────────────────────────────────────────────────────────────────────

CMD="${1:-start}"

case "${CMD}" in
  start)   do_start   ;;
  stop)    do_stop    ;;
  restart) do_restart ;;
  status)  do_status  ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
    ;;
esac
