#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
RUNTIME_LIB_DIR="${PROJECT_ROOT}/.runtime/linux-libs"

has_linux_libmpv() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    return 0
  fi

  if command -v ldconfig >/dev/null 2>&1; then
    if ldconfig -p 2>/dev/null | grep -q "libmpv\\.so\\.1"; then
      return 0
    fi
  fi

  local candidate
  for candidate in \
    /usr/lib/libmpv.so.1 \
    /usr/lib64/libmpv.so.1 \
    /usr/lib/x86_64-linux-gnu/libmpv.so.1 \
    /lib/x86_64-linux-gnu/libmpv.so.1 \
    /usr/local/lib/libmpv.so.1
  do
    [[ -e "${candidate}" ]] && return 0
  done

  return 1
}

prepare_linux_libmpv_compat() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    return 0
  fi

  if has_linux_libmpv; then
    return 0
  fi

  local source_lib=""
  for candidate in /usr/lib/libmpv.so /usr/lib/libmpv.so.2 /usr/local/lib/libmpv.so /usr/local/lib/libmpv.so.2; do
    if [[ -e "${candidate}" ]]; then
      source_lib="${candidate}"
      break
    fi
  done

  if [[ -z "${source_lib}" ]]; then
    return 1
  fi

  mkdir -p "${RUNTIME_LIB_DIR}"
  ln -sfn "${source_lib}" "${RUNTIME_LIB_DIR}/libmpv.so.1"
  export LD_LIBRARY_PATH="${RUNTIME_LIB_DIR}${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
  return 0
}

print_linux_libmpv_help() {
  cat <<'EOF'
WorkPulse cannot start because the Linux desktop runtime dependency "libmpv.so.1" is missing.

Install one of the following, depending on your distro:
  Ubuntu / Debian:
    sudo apt update
    sudo apt install libmpv-dev libmpv2 mpv

  Fedora:
    sudo dnf install mpv-libs mpv

  Arch Linux:
    sudo pacman -S mpv

Reference:
  Flet docs mention libmpv for Linux and also note that some systems may require an additional symlink
  if "libmpv.so.1" is still not found after installation.

Ubuntu / Debian fallback from Flet docs:
  sudo apt update
  sudo apt install libmpv-dev libmpv2
  sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1
EOF
}

if [[ ! -d "${VENV_DIR}" ]]; then
  echo "No existe ${VENV_DIR}. Ejecuta primero ./init.sh"
  exit 1
fi

if [[ "$(uname -s)" == "Linux" ]] && ! prepare_linux_libmpv_compat; then
  print_linux_libmpv_help
  exit 1
fi

source "${VENV_DIR}/bin/activate"
exec python "${PROJECT_ROOT}/main.py" "$@"
