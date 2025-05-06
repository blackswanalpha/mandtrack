import os
import sys
import django
import json
import random
import sqlite3
from datetime import datetime

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

def create_test_data():
    """Create test data for scoring functionality."""
    print("Creating test data...")

    # Connect to the database directly
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Check if we have any scoring systems
    cursor.execute("SELECT id, name FROM surveys_scoringsystem")
    scoring_systems = cursor.fetchall()

    if not scoring_systems:
        print("No scoring systems found. Creating a test scoring system...")

        # Create a test scoring system
        cursor.execute("""
            INSERT INTO surveys_scoringsystem (
                name, description, scoring_type, formula, created_at, updated_at, created_by_id, questionnaire_id
            ) VALUES (?, ?, ?, ?, ?, ?, NULL, ?)
        """, (
            "Test Scoring System",
            "A test scoring system",
            "weighted_sum",
            "sum(weights * scores)",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "00000000-0000-0000-0000-000000000001"  # Dummy UUID for questionnaire
        ))

        scoring_system_id = cursor.lastrowid
        print(f"Created scoring system with ID: {scoring_system_id}")
    else:
        print(f"Found {len(scoring_systems)} scoring systems:")
        for system_id, name in scoring_systems:
            print(f"  ID: {system_id}, Name: {name}")

        # Use the first scoring system
        scoring_system_id = scoring_systems[0][0]

    # Check if we have any score ranges
    cursor.execute("SELECT id, min_score, max_score FROM surveys_scorerange WHERE scoring_system_id = ?", (scoring_system_id,))
    score_ranges = cursor.fetchall()

    if not score_ranges:
        print("No score ranges found. Creating test score ranges...")

        # Create test score ranges
        ranges = [
            {'min_score': 0, 'max_score': 20, 'label': 'Very Low', 'color': '#FF0000'},
            {'min_score': 21, 'max_score': 40, 'label': 'Low', 'color': '#FFA500'},
            {'min_score': 41, 'max_score': 60, 'label': 'Medium', 'color': '#FFFF00'},
            {'min_score': 61, 'max_score': 80, 'label': 'High', 'color': '#00FF00'},
            {'min_score': 81, 'max_score': 100, 'label': 'Very High', 'color': '#008000'},
        ]

        for range_data in ranges:
            cursor.execute("""
                INSERT INTO surveys_scorerange (
                    scoring_system_id, name, min_score, max_score, color, description, interpretation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                scoring_system_id,
                range_data['label'],
                range_data['min_score'],
                range_data['max_score'],
                range_data['color'],
                f"Scores between {range_data['min_score']} and {range_data['max_score']}",
                f"This score indicates {range_data['label'].lower()} performance"
            ))

            print(f"Created score range: {range_data['label']}")
    else:
        print(f"Found {len(score_ranges)} score ranges")

    # Check if we have any responses
    cursor.execute("SELECT id FROM feedback_response LIMIT 1")
    response = cursor.fetchone()

    if not response:
        print("No responses found. Creating a test response...")

        # Create a test response
        cursor.execute("""
            INSERT INTO feedback_response (
                id, status, started_at, completed_at, ip_address, user_agent, survey_id, respondent_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, NULL)
        """, (
            "00000000-0000-0000-0000-000000000001",  # Dummy UUID for response
            "completed",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "127.0.0.1",
            "Test User Agent",
            "00000000-0000-0000-0000-000000000001"  # Dummy UUID for survey
        ))

        response_id = "00000000-0000-0000-0000-000000000001"
        print(f"Created response with ID: {response_id}")
    else:
        response_id = response[0]
        print(f"Using existing response with ID: {response_id}")

    # Create test response scores
    for i in range(5):
        raw_score = random.randint(0, 100)

        # Find the appropriate score range
        cursor.execute("""
            SELECT id FROM surveys_scorerange
            WHERE scoring_system_id = ? AND min_score <= ? AND max_score >= ?
        """, (scoring_system_id, raw_score, raw_score))

        score_range = cursor.fetchone()
        score_range_id = score_range[0] if score_range else None

        # Check if this response score already exists
        cursor.execute("""
            SELECT id FROM surveys_responsescore
            WHERE response_id = ? AND scoring_system_id = ?
        """, (response_id, scoring_system_id))

        existing_score = cursor.fetchone()

        if existing_score:
            print(f"Response score already exists for response {response_id} and scoring system {scoring_system_id}")
            continue

        # Create the response score
        cursor.execute("""
            INSERT INTO surveys_responsescore (
                raw_score, calculated_at, notes, response_id, score_range_id, scoring_system_id
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            raw_score,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            f"Test score {i+1}",
            response_id,
            score_range_id,
            scoring_system_id
        ))

        print(f"Created response score with raw_score: {raw_score}")

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()

if __name__ == "__main__":
    create_test_data()
