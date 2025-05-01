#!/bin/bash

# Run the MindTrack server with barberianspa.com settings on port 8009
# This script is a convenience wrapper around server.py

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Run the server with barberianspa.com settings
echo "Starting server with barberianspa.com settings on http://0.0.0.0:8009/"
echo "Press Ctrl+C to stop the server."
python server.py --host=0.0.0.0 --port=8009 --settings=mindtrack.barberianspa_settings

# Deactivate the virtual environment
if [ -d "venv" ]; then
    deactivate
fi
