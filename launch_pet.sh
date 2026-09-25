#!/bin/bash
# Desktop Sheep Pet Launcher Script
cd "$(dirname "$0")"
export PYTHONPATH="$(pwd):$PYTHONPATH"
exec python3 main.py "$@"
