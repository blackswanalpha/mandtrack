#!/bin/bash

# Run the MindTrack server with Render.com settings
# This script is a convenience wrapper around server.py

# Activate the virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "Virtual environment activated."
else
    echo "Warning: Virtual environment not found. Using system Python."
fi

# Run the server with Render.com settings
echo "Starting server with Render.com settings on http://0.0.0.0:8009/"
python server.py --host=0.0.0.0 --port=8009 --settings=mindtrack.render_settings

# Deactivate the virtual environment
if [ -d "venv" ]; then
    deactivate
fi
