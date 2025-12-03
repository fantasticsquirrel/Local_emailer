#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${ROOT_DIR}/.venv"
ENV_FILE="${ROOT_DIR}/.env"
ENV_EXAMPLE="${ROOT_DIR}/.env.example"

if [[ "${1:-}" == "--reset" ]]; then
  echo "[setup] Removing existing virtual environment and .env file"
  rm -rf "${VENV_DIR}"
  rm -f "${ENV_FILE}"
fi

if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "[setup] Python is not installed or not on PATH" >&2
  exit 1
fi

if [[ -d "${VENV_DIR}" ]]; then
  echo "[setup] Reusing existing virtual environment at ${VENV_DIR}"
else
  echo "[setup] Creating virtual environment at ${VENV_DIR}" 
  "${PYTHON_CMD}" -m venv "${VENV_DIR}"
fi

if [[ -x "${VENV_DIR}/bin/python" ]]; then
  PY_BIN="${VENV_DIR}/bin/python"
  PIP_BIN="${VENV_DIR}/bin/pip"
elif [[ -x "${VENV_DIR}/Scripts/python.exe" ]]; then
  PY_BIN="${VENV_DIR}/Scripts/python.exe"
  PIP_BIN="${VENV_DIR}/Scripts/pip.exe"
else
  echo "[setup] Could not locate virtual environment python binary" >&2
  exit 1
fi

echo "[setup] Upgrading pip"
"${PY_BIN}" -m pip install --upgrade pip

echo "[setup] Installing dependencies from requirements.txt"
"${PIP_BIN}" install -r "${ROOT_DIR}/requirements.txt"

if [[ -f "${ENV_EXAMPLE}" && ! -f "${ENV_FILE}" ]]; then
  echo "[setup] Creating .env from .env.example"
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
fi

echo "[setup] Done. Activate the virtual environment and start the app:"
if [[ "${PY_BIN}" == *"Scripts"* ]]; then
  echo "  PowerShell: .venv\\Scripts\\Activate.ps1"
  echo "  CMD:        .venv\\Scripts\\activate.bat"
else
  echo "  macOS/Linux: source .venv/bin/activate"
fi

echo "[setup] Run the app with: uvicorn protonmailer.main:app --host 127.0.0.1 --port 8000 --reload"
