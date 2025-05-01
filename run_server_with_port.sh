#!/bin/bash

# Run the MindTrack server with the specified port
# This script is a convenience wrapper around server.py

# Default values
HOST="0.0.0.0"
PORT="8009"
LOG_LEVEL="debug"
SETTINGS="mindtrack.settings"
RELOAD=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port=*)
            PORT="${1#*=}"
            shift
            ;;
        --host=*)
            HOST="${1#*=}"
            shift
            ;;
        --log-level=*)
            LOG_LEVEL="${1#*=}"
            shift
            ;;
        --settings=*)
            SETTINGS="${1#*=}"
            shift
            ;;
        --no-reload)
            RELOAD=false
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--port=PORT] [--host=HOST] [--log-level=LEVEL] [--settings=MODULE] [--no-reload]"
            exit 1
            ;;
    esac
done

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Build the command
CMD="python server.py --host=$HOST --port=$PORT --log-level=$LOG_LEVEL --settings=$SETTINGS"
if [ "$RELOAD" = true ]; then
    CMD="$CMD --reload"
fi

# Print the command
echo "Running: $CMD"

# Run the server
eval $CMD

# Deactivate the virtual environment
if [ -d "venv" ]; then
    deactivate
fi
