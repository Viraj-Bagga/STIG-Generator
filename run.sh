#!/bin/bash
# Script to run the STIG Authoring Pro app using the local virtual environment.

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

if [ -f "venv/bin/python" ]; then
    echo "Starting STIG Authoring Pro using virtual environment python..."
    ./venv/bin/python main.py
else
    echo "Virtual environment not found. Attempting to start with system python..."
    python3 main.py
fi
