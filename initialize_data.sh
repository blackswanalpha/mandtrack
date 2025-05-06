#!/bin/bash

# Initialize selector data
echo "Initializing selector data..."
python manage.py initialize_selector_data

# Initialize question types
echo "Initializing question types..."
python manage.py initialize_question_types

echo "Data initialization complete!"
