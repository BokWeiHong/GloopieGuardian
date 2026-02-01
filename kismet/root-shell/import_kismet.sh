#!/usr/bin/env bash
set -euo pipefail

# Absolute paths
LOG_DIR="/home/pi/GloopieGuardian/kismet/logs"
PID_FILE="/opt/gloopie/kismet.pid"
SLEEP_AFTER_STOP=2
VENV_ACTIVATE="/home/pi/GloopieGuardian/venv/bin/activate"
PROJECT_DIR="/home/pi/GloopieGuardian"
MANAGE_PY="${PROJECT_DIR}/manage.py"

if [[ -f "$VENV_ACTIVATE" ]]; then
    # shellcheck disable=SC1090
    source "$VENV_ACTIVATE"
fi

echo ">>> Stopping Kismet..."
if [[ -f "$PID_FILE" ]]; then
    KPID=$(cat "$PID_FILE")
    if kill -0 "$KPID" 2>/dev/null; then
        kill "$KPID" || true
        echo ">>> Sent SIGTERM to PID $KPID"
        # wait for it to exit
        for i in {1..10}; do
        if kill -0 "$KPID" 2>/dev/null; then
            sleep 1
        else
            break
        fi
        done
        else
        echo ">>> PID $KPID not running, continuing..."
    fi
    rm -f "$PID_FILE"
else
    echo ">>> No PID file found, attempting pkill as fallback..."
    pkill -f kismet || true
fi

echo ">>> Waiting ${SLEEP_AFTER_STOP}s for logs to flush..."
sleep "$SLEEP_AFTER_STOP"

LATEST_DB=$(ls -t "${LOG_DIR}"/*.kismet 2>/dev/null | head -n1 || true)
if [[ -z "$LATEST_DB" ]]; then
    echo "Error: No .kismet files found in ${LOG_DIR}"
    exit 1
fi

echo ">>> Importing latest file: $LATEST_DB"

# ensure manage.py exists
if [[ ! -f "$MANAGE_PY" ]]; then
    echo "Error: manage.py not found at $MANAGE_PY. Please update PROJECT_DIR in this script."
    exit 1
fi

# run the Django import command from project dir
cd "$PROJECT_DIR"
python "$MANAGE_PY" import_kismet "$LATEST_DB"

echo ">>> Import completed successfully."
exit 0
