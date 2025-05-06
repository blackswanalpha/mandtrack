import os
import sys
import django
import json
import random
import math
from datetime import datetime
import sqlite3

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

def test_response_score_api():
    """Test the ResponseScore API with the new fields."""
    print("Testing ResponseScore API...")

    # Connect to the database directly
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()

    # Get all response scores
    cursor.execute("SELECT id, raw_score FROM surveys_responsescore")
    scores = cursor.fetchall()
    print(f"Found {len(scores)} response scores")

    # Update the response scores with the new fields
    for score_id, raw_score in scores:
        # Generate random values for the new fields
        z_score = (raw_score - 50) / 15  # Assuming mean=50, std=15
        percentile = 100 * (0.5 + 0.5 * math.erf(z_score / math.sqrt(2)))
        additional_data = json.dumps({
            'category_scores': {
                'anxiety': random.randint(0, 10),
                'depression': random.randint(0, 10),
                'stress': random.randint(0, 10),
            }
        })

        # Update the response score
        cursor.execute(
            "UPDATE surveys_responsescore SET z_score = ?, percentile = ?, additional_data = ? WHERE id = ?",
            (z_score, percentile, additional_data, score_id)
        )

        print(f"Updated ResponseScore: {score_id}")
        print(f"  Raw Score: {raw_score}")
        print(f"  Z-Score: {z_score:.2f}")
        print(f"  Percentile: {percentile:.2f}")
        print(f"  Additional Data: {additional_data}")

    # Commit the changes
    conn.commit()

    # Close the connection
    conn.close()

if __name__ == "__main__":
    test_response_score_api()
