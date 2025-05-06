#!/bin/bash

# Set the path to the project directory
PROJECT_DIR="/path/to/mindtrack"

# Activate the virtual environment
source "$PROJECT_DIR/venv/bin/activate"

# Change to the project directory
cd "$PROJECT_DIR"

# Run the management command
python manage.py process_scheduled_emails

# Deactivate the virtual environment
deactivate
