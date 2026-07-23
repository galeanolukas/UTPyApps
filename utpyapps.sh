#!/bin/bash
# UTPyApps Launcher - Compatible con Linux y Ubuntu Touch
# Uso:
#   ./utpyapps.sh          -> Inicia servidor y abre home
#   ./utpyapps.sh app1     -> Inicia servidor y abre app1
#   ./utpyapps.sh --stop   -> Detiene el servidor

# Detectar directorio del proyecto
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Si main.py existe en el directorio del script, usar ese (modo desktop)
if [ -f "$SCRIPT_DIR/main.py" ]; then
    BASE_DIR="$SCRIPT_DIR"
else
    # Si no, usar ~/utpyapps (modo dispositivo)
    BASE_DIR="$HOME/utpyapps"
fi

VENV_DIR="$BASE_DIR/venv"
PYTHON="$VENV_DIR/bin/python3"
MAIN_PY="$BASE_DIR/main.py"
PID_FILE="$BASE_DIR/.utpyapps.pid"
PORT=8080

# --- Funciones ---

detect_platform() {
    if [ -f /etc/ubuntu-touch ] || [ -d /usr/share/lomiri ]; then
        echo "ut"
    else
        echo "linux"
    fi
}

open_url() {
    local url="$1"
    local platform
    platform=$(detect_platform)

    if [ "$platform" = "ut" ]; then
        # Ubuntu Touch - usar lomiri-app-launch
        su - phablet -c "lomiri-app-launch --desktop-file-hint=/usr/share/morph-browser/morph-browser.desktop $url" 2>/dev/null \
        || su - phablet -c "morph-browser $url" 2>/dev/null \
        || echo "No se pudo abrir el navegador en Ubuntu Touch"
    else
        # Linux - usar xdg-open
        xdg-open "$url" 2>/dev/null \
        || sensible-browser "$url" 2>/dev/null \
        || echo "No se pudo abrir el navegador"
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

stop_server() {
    if is_running; then
        local pid
        pid=$(cat "$PID_FILE")
        echo "Deteniendo UTPyApps (PID: $pid)..."
        kill "$pid" 2>/dev/null
        sleep 1
        kill -9 "$pid" 2>/dev/null
        rm -f "$PID_FILE"
        echo "UTPyApps detenido."
    else
        echo "UTPyApps no está corriendo."
    fi
}

start_server() {
    if is_running; then
        echo "UTPyApps ya está corriendo (PID: $(cat "$PID_FILE"))"
        return 0
    fi

    # Verificar que el entorno existe
    if [ ! -f "$MAIN_PY" ]; then
        echo "Error: No se encontró $MAIN_PY"
        echo "Ejecuta la configuración del entorno desde ADB Manager primero."
        exit 1
    fi

    if [ ! -f "$PYTHON" ]; then
        echo "Advertencia: No se encontró Python en $VENV_DIR, usando Python del sistema"
        PYTHON="python3"
    fi

    echo "Iniciando UTPyApps..."
    cd "$BASE_DIR"
    "$PYTHON" "$MAIN_PY" &
    local pid=$!
    echo "$pid" > "$PID_FILE"
    echo "UTPyApps iniciado (PID: $pid) en http://localhost:$PORT"

    # Esperar a que el servidor esté listo
    sleep 2
}

# --- Lógica principal ---

case "$1" in
    --stop)
        stop_server
        exit 0
        ;;
    --status)
        if is_running; then
            echo "UTPyApps está corriendo (PID: $(cat "$PID_FILE"))"
        else
            echo "UTPyApps no está corriendo."
        fi
        exit 0
        ;;
    --help|-h)
        echo "UTPyApps Launcher"
        echo ""
        echo "Uso:"
        echo "  utpyapps.sh              Inicia servidor y abre home"
        echo "  utpyapps.sh <app_name>   Inicia servidor y abre app específica"
        echo "  utpyapps.sh --stop       Detiene el servidor"
        echo "  utpyapps.sh --status     Muestra el estado del servidor"
        echo "  utpyapps.sh --help       Muestra esta ayuda"
        exit 0
        ;;
esac

# Iniciar servidor
start_server

# Construir URL
if [ -n "$1" ]; then
    URL="http://localhost:$PORT/_app/$1/"
    echo "Abriendo app: $1"
else
    URL="http://localhost:$PORT"
    echo "Abriendo home"
fi

# Abrir navegador
open_url "$URL"
