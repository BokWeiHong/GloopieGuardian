#!/usr/bin/env bash
set -euo pipefail

# Absolute paths
LOG_DIR="/opt/gloopie/kismet"
VENV_ACTIVATE="/home/pi/GloopieGuardian/venv/bin/activate"
PID_FILE="/opt/gloopie/kismet.pid"

ELIGIBLE_IFACE="${1:-}"

if [[ -z "$ELIGIBLE_IFACE" ]]; then
  echo "Error: No interface specified."
  echo "Usage: $0 <interface>"
  exit 1
fi

# validate interface exists
if ! iw dev | awk '$1=="Interface"{print $2}' | grep -qx "$ELIGIBLE_IFACE"; then
  echo "Error: Interface '$ELIGIBLE_IFACE' not found."
  exit 1
fi

# ensure log dir exists
mkdir -p "$LOG_DIR"
chmod 770 "$LOG_DIR"

if [[ -f "$VENV_ACTIVATE" ]]; then
  source "$VENV_ACTIVATE"
fi

echo ">>> Starting Kismet on interface: $ELIGIBLE_IFACE"
kismet -c "$ELIGIBLE_IFACE" > "${LOG_DIR}/kismet_output.log" 2>&1 &
KISMET_PID=$!

echo "$KISMET_PID" > "$PID_FILE"
chmod 640 "$PID_FILE"
echo ">>> Kismet started with PID $KISMET_PID"
echo ">>> Logs: ${LOG_DIR}/kismet_output.log"
exit 0
