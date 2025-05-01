#!/bin/bash

# Run the MindTrack server with the correct settings
# This script is a convenience wrapper around server.py

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Run the server with development settings
python server.py --host=0.0.0.0 --port=8001 --reload --log-level=debug --settings=mindtrack.settings

# Deactivate the virtual environment
if [ -d "venv" ]; then
    deactivate
fi
