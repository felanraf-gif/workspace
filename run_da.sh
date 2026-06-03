#!/bin/bash
# Development Assistant V8 - Start script

SCRIPT_DIR="$(cd "$(dirname "${BASHOURCE[0]}")" && pwd)"
TOR_ENV="$SCRIPT_DIR/tor_env/bin/python"

echo "=== Development Assistant V8 ==="
echo "Uruchamianie agenta..."

# Sprawdź, czy Python z tor_env istnieje
if [ ! -f "$TOR_ENV" ]; then
    echo "BŁĄD: Nie znaleziono $TOR_ENV"
    echo "Upewnij się, że środowisko tor_env jest skonfigurowane."
    exit 1
fi

# Sprawdź, czy agent już działa
if pgrep -f "main.py" > /dev/null 2>&1; then
    echo "Agent jest już uruchomiony."
    exit 1
fi

# Utwórz/napraw daemon.log jeśli potrzeba
touch "$SCRIPT_DIR/daemon.log" 2>/dev/null || {
    echo "BŁĄD: Nie można utworzyć $SCRIPT_DIR/daemon.log"
    exit 1
}

# Uruchom agenta w tle z tor_env (bez buforowania stdout/stderr)
cd "$SCRIPT_DIR"
"$TOR_ENV" -u -B main.py > daemon.log 2>&1 &

# Sprawdź czy proces się uruchomił
sleep 2
if pgrep -f "main.py" > /dev/null 2>&1; then
    echo "Agent uruchomiony pomyślnie (PID: $!)"
    echo "Logi: $SCRIPT_DIR/daemon.log"
    echo "Aby zatrzymać: pkill -f 'main.py'"
else
    echo "BŁĄD: Agent nie uruchomił się. Sprawdź logi:"
    cat "$SCRIPT_DIR/daemon.log" | tail -20
    exit 1
fi
