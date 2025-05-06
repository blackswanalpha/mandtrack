import os
import sys
import django
import json
import sqlite3

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mindtrack.settings')
django.setup()

def create_test_score_rule():
    """Create a test ScoreRule with conditional logic."""
    print("Creating test ScoreRule...")
    
    # Connect to the database directly
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if we have any scoring systems
    cursor.execute("SELECT id FROM surveys_scoringsystem LIMIT 1")
    scoring_system = cursor.fetchone()
    
    if not scoring_system:
        print("No scoring systems found. Please run create_test_scoring_data.py first.")
        return
    
    scoring_system_id = scoring_system[0]
    
    # Check if we have any questions
    cursor.execute("SELECT id FROM surveys_question LIMIT 1")
    question = cursor.fetchone()
    
    if not question:
        print("No questions found. Creating a test question...")
        
        # Create a test question
        cursor.execute("""
            INSERT INTO surveys_question (
                id, text, description, question_type, required, order_num, is_scored, is_visible, 
                options, conditional_logic, validation_rules, category, created_at, updated_at, 
                max_score, scoring_weight, survey_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            1,  # ID
            "Test Question",  # text
            "A test question",  # description
            "multiple_choice",  # question_type
            1,  # required
            1,  # order_num
            1,  # is_scored
            1,  # is_visible
            json.dumps({"choices": ["Yes", "No", "Maybe"]}),  # options
            "{}",  # conditional_logic
            "{}",  # validation_rules
            "general",  # category
            "2023-01-01 00:00:00",  # created_at
            "2023-01-01 00:00:00",  # updated_at
            10.0,  # max_score
            1.0,  # scoring_weight
            "00000000-0000-0000-0000-000000000001"  # survey_id
        ))
        
        question_id = 1
        print(f"Created question with ID: {question_id}")
    else:
        question_id = question[0]
        print(f"Using existing question with ID: {question_id}")
    
    # Check if this score rule already exists
    cursor.execute("""
        SELECT id FROM surveys_scorerule 
        WHERE scoring_system_id = ? AND question_id = ?
    """, (scoring_system_id, question_id))
    
    existing_rule = cursor.fetchone()
    
    if existing_rule:
        print(f"Score rule already exists for scoring system {scoring_system_id} and question {question_id}")
        
        # Update the existing rule with conditional logic
        conditional_logic = json.dumps({
            "if": {"answer": "Yes"},
            "then": {"score": 10},
            "else": {"if": {"answer": "Maybe"}, "then": {"score": 5}, "else": {"score": 0}}
        })
        
        cursor.execute("""
            UPDATE surveys_scorerule 
            SET conditional_logic = ? 
            WHERE scoring_system_id = ? AND question_id = ?
        """, (conditional_logic, scoring_system_id, question_id))
        
        print(f"Updated score rule with conditional logic")
    else:
        # Create a new score rule
        conditional_logic = json.dumps({
            "if": {"answer": "Yes"},
            "then": {"score": 10},
            "else": {"if": {"answer": "Maybe"}, "then": {"score": 5}, "else": {"score": 0}}
        })
        
        cursor.execute("""
            INSERT INTO surveys_scorerule (
                weight, text_score_enabled, text_score, notes, question_id, scoring_system_id, conditional_logic
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            1.0,  # weight
            0,  # text_score_enabled
            0.0,  # text_score
            "Test score rule",  # notes
            question_id,  # question_id
            scoring_system_id,  # scoring_system_id
            conditional_logic  # conditional_logic
        ))
        
        print(f"Created score rule with conditional logic")
    
    # Commit the changes
    conn.commit()
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    create_test_score_rule()
