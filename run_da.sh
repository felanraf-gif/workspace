#!/bin/bash
# Towarzysz V9 - Start script

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/towarzysz.pid"

if [ -x "$SCRIPT_DIR/.venv/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/.venv/bin/python"
elif [ -x "$SCRIPT_DIR/tor_env/bin/python" ]; then
    PYTHON_BIN="$SCRIPT_DIR/tor_env/bin/python"
else
    PYTHON_BIN="${PYTHON_BIN:-python3}"
fi

echo "=== Towarzysz V9 ==="
echo "Uruchamianie agenta..."

# Sprawdź, czy wybrany interpreter ma zależności agenta.
if ! "$PYTHON_BIN" -c "import dotenv, requests" 2>/dev/null; then
    echo "BŁĄD: Brak zależności dla $PYTHON_BIN"
    echo "Utwórz środowisko: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
    exit 1
fi

# Sprawdź, czy agent już działa
if [ -f "$PID_FILE" ]; then
    PID="$(cat "$PID_FILE")"
    if kill -0 "$PID" 2>/dev/null; then
        echo "Agent jest już uruchomiony (PID: $PID)."
        exit 1
    fi
    rm -f "$PID_FILE"
fi

# Utwórz/napraw daemon.log jeśli potrzeba
touch "$SCRIPT_DIR/daemon.log" 2>/dev/null || {
    echo "BŁĄD: Nie można utworzyć $SCRIPT_DIR/daemon.log"
    exit 1
}

# Uruchom agenta w tle bez buforowania stdout/stderr.
cd "$SCRIPT_DIR"
nohup "$PYTHON_BIN" -u -B main.py > daemon.log 2>&1 < /dev/null &
PID=$!
echo "$PID" > "$PID_FILE"

# Sprawdź czy proces się uruchomił
sleep 2
if kill -0 "$PID" 2>/dev/null; then
    echo "Agent uruchomiony pomyślnie (PID: $PID)"
    echo "Logi: $SCRIPT_DIR/daemon.log"
    echo "Aby zatrzymać: kill $PID"
else
    rm -f "$PID_FILE"
    echo "BŁĄD: Agent nie uruchomił się. Sprawdź logi:"
    cat "$SCRIPT_DIR/daemon.log" | tail -20
    exit 1
fi
