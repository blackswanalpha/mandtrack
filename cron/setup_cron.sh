#!/bin/bash

# Setup script for MindTrack cron jobs

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_DIR="$PROJECT_DIR/.venv"
LOGS_DIR="$PROJECT_DIR/logs"

# Create logs directory if it doesn't exist
mkdir -p "$LOGS_DIR"

# Create a temporary crontab file
TMP_CRONTAB=$(mktemp)

# Read the template crontab file
cat "$PROJECT_DIR/cron/crontab" | \
    # Replace placeholders with actual paths
    sed "s|/path/to/mindtrack|$PROJECT_DIR|g" > "$TMP_CRONTAB"

# Display the crontab that will be installed
echo "The following crontab will be installed:"
echo "----------------------------------------"
cat "$TMP_CRONTAB"
echo "----------------------------------------"

# Ask for confirmation
read -p "Do you want to install this crontab? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Install the crontab
    crontab "$TMP_CRONTAB"
    echo "Crontab installed successfully."
    
    # Test the process_scheduled_emails command
    echo "Testing the process_scheduled_emails command..."
    cd "$PROJECT_DIR" && "$VENV_DIR/bin/python" manage.py process_scheduled_emails --dry-run
    
    echo "Cron jobs have been set up. Check the logs directory for output."
else
    echo "Crontab installation cancelled."
fi

# Clean up
rm "$TMP_CRONTAB"
