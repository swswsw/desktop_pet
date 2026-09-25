#!/bin/bash
# Desktop Sheep Pet Launcher Script
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"
export QT_QPA_PLATFORM="xcb"
exec python3 main.py "$@"
