#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${PROJECT_ROOT}/.venv"
REQUIREMENTS_FILE="${PROJECT_ROOT}/requirements.txt"

if [[ "$(uname -s)" == "Darwin" ]]; then
  PLATFORM="macOS"
  DEFAULT_BIN_DIR="${HOME}/.local/bin"
  [[ -d "${DEFAULT_BIN_DIR}" ]] || DEFAULT_BIN_DIR="${HOME}/bin"
else
  PLATFORM="Linux"
  DEFAULT_BIN_DIR="${HOME}/.local/bin"
fi

mkdir -p "${DEFAULT_BIN_DIR}"

print_step() {
  printf "\n\033[1;37m[%s]\033[0m %s\n" "$1" "$2"
}

print_ok() {
  printf "\033[0;32m%s\033[0m\n" "$1"
}

print_warn() {
  printf "\033[0;33m%s\033[0m\n" "$1"
}

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

can_prepare_linux_libmpv_compat() {
  if [[ "$(uname -s)" != "Linux" ]]; then
    return 0
  fi

  if has_linux_libmpv; then
    return 0
  fi

  local candidate
  for candidate in /usr/lib/libmpv.so /usr/lib/libmpv.so.2 /usr/local/lib/libmpv.so /usr/local/lib/libmpv.so.2; do
    [[ -e "${candidate}" ]] && return 0
  done

  return 1
}

print_linux_libmpv_help() {
  cat <<'EOF'

Linux desktop runtime dependency missing: libmpv.so.1

WorkPulse uses Flet desktop, and on Linux the runtime may require libmpv to be present.

Install hints:
  Ubuntu / Debian:
    sudo apt update
    sudo apt install libmpv-dev libmpv2 mpv

  Fedora:
    sudo dnf install mpv-libs mpv

  Arch Linux:
    sudo pacman -S mpv

If your system still reports "libmpv.so.1" after installing mpv, check the Flet docs for the
extra symlink workaround mentioned for some distributions.

Ubuntu / Debian fallback from Flet docs:
  sudo apt update
  sudo apt install libmpv-dev libmpv2
  sudo ln -s /usr/lib/x86_64-linux-gnu/libmpv.so /usr/lib/libmpv.so.1
EOF
}

print_step "WorkPulse" "Preparando entorno en ${PLATFORM}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Error: no se encontró python3 en PATH. Instala Python 3.11 o superior y vuelve a ejecutar ./init.sh."
  exit 1
fi

PYTHON_BIN="$(command -v python3)"
PYTHON_VERSION="$("${PYTHON_BIN}" -c 'import sys; print(".".join(map(str, sys.version_info[:3])))')"
PYTHON_OK="$("${PYTHON_BIN}" -c 'import sys; print(int(sys.version_info >= (3, 11)))')"

if [[ "${PYTHON_OK}" != "1" ]]; then
  echo "Error: WorkPulse requiere Python 3.11 o superior. Detectado: ${PYTHON_VERSION}"
  exit 1
fi

print_ok "Python ${PYTHON_VERSION} detectado"

if [[ ! -d "${VENV_DIR}" ]]; then
  print_step "Venv" "Creando entorno virtual en ${VENV_DIR}"
  "${PYTHON_BIN}" -m venv "${VENV_DIR}"
else
  print_ok "Entorno virtual ya existente"
fi

source "${VENV_DIR}/bin/activate"

print_step "Pip" "Actualizando pip"
python -m pip install --upgrade pip

print_step "Deps" "Instalando dependencias desde requirements.txt"
python -m pip install -r "${REQUIREMENTS_FILE}"

LAUNCHER_PATH="${DEFAULT_BIN_DIR}/workpulse"
print_step "Launcher" "Generando ${LAUNCHER_PATH}"

cat > "${LAUNCHER_PATH}" <<EOF
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="${PROJECT_ROOT}"
exec "\${PROJECT_ROOT}/run.sh" "\$@"
EOF

chmod +x "${LAUNCHER_PATH}"
chmod +x "${PROJECT_ROOT}/run.sh"
chmod +x "${PROJECT_ROOT}/init.sh"

print_ok "Launcher instalado en ${LAUNCHER_PATH}"

if [[ "${PLATFORM}" == "Linux" ]] && ! has_linux_libmpv; then
  if can_prepare_linux_libmpv_compat; then
    print_warn "No se ha detectado libmpv.so.1, pero run.sh intentará resolverlo con un shim local."
  else
    print_warn "No se ha detectado libmpv.so.1 en este sistema."
    print_linux_libmpv_help
  fi
fi

case ":${PATH}:" in
  *":${DEFAULT_BIN_DIR}:"*)
    print_ok "La ruta ${DEFAULT_BIN_DIR} ya está en PATH"
    ;;
  *)
    print_warn "Aviso: ${DEFAULT_BIN_DIR} no está en PATH."
    print_warn "Podrás lanzar la app con ${LAUNCHER_PATH} o añadiendo esa carpeta a tu PATH."
    ;;
esac

print_step "Listo" "Puedes arrancar WorkPulse con:"
echo "  workpulse"
echo "o bien:"
echo "  ./run.sh"
