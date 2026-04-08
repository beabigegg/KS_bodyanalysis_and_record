#!/usr/bin/env bash
# Mount the recipe-traceability SMB share to a local path.
# Requires: sudo (or root), cifs-utils
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# ─── Load RECIPE_TRACE_SMB_* from .env ────────────────────────────────────────

load_smb_env() {
  local env_file="${ROOT_DIR}/.env"
  if [[ ! -f "${env_file}" ]]; then return 0; fi
  while IFS= read -r line; do
    if [[ "${line}" =~ ^[[:space:]]*# ]] || [[ -z "${line}" ]]; then continue; fi
    if [[ "${line}" =~ ^RECIPE_TRACE_SMB_ ]]; then export "${line?}"; fi
  done < "${env_file}"
}

# ─── Mount ────────────────────────────────────────────────────────────────────

mount_smb() {
  local smb_host="${RECIPE_TRACE_SMB_HOST:-}"
  local smb_share="${RECIPE_TRACE_SMB_SHARE:-}"
  local smb_user="${RECIPE_TRACE_SMB_USER:-}"
  local smb_pass="${RECIPE_TRACE_SMB_PASSWORD:-}"
  local mount_point="/mnt/eap_recipe"
  local creds_file="/tmp/.smb_creds_$$"
  trap 'rm -f "${creds_file}"' RETURN

  if ! command -v mount.cifs >/dev/null 2>&1; then
    echo "ERROR: cifs-utils is not installed. Run: sudo apt-get install cifs-utils" >&2
    exit 1
  fi

  if [[ -z "${smb_host}" || -z "${smb_share}" || -z "${smb_user}" || -z "${smb_pass}" ]]; then
    echo "WARNING: RECIPE_TRACE_SMB_* variables not fully set; skipping SMB mount." >&2
    return 0
  fi

  mkdir -p "${mount_point}"

  if mountpoint -q "${mount_point}" 2>/dev/null; then
    echo "SMB already mounted at ${mount_point}, skipping."
    return 0
  fi

  printf 'username=%s\npassword=%s\n' "${smb_user}" "${smb_pass}" > "${creds_file}"
  chmod 600 "${creds_file}"

  echo "Mounting //${smb_host}/${smb_share} → ${mount_point}..."
  mount.cifs "//${smb_host}/${smb_share}" "${mount_point}" \
    -o "credentials=${creds_file},vers=3.0,uid=$(id -u),gid=$(id -g),file_mode=0444,dir_mode=0555"

  echo "SMB mounted at ${mount_point}."
}

# ─── Main ─────────────────────────────────────────────────────────────────────

load_smb_env
mount_smb
