import sqlite3
import json
import math
import random

def test_response_score():
    """Test the ResponseScore model with the new fields"""
    print("Testing ResponseScore model...")
    
    # Connect to the database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get the ResponseScore record
    cursor.execute("SELECT id, raw_score, z_score, percentile, additional_data FROM surveys_responsescore LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        id, raw_score, z_score, percentile, additional_data = row
        
        print(f"Found ResponseScore with ID: {id}")
        print(f"  Raw Score: {raw_score}")
        print(f"  Z-Score: {z_score}")
        print(f"  Percentile: {percentile}")
        print(f"  Additional Data: {additional_data}")
        
        # Parse the additional_data JSON
        if additional_data:
            data = json.loads(additional_data)
            if 'category_scores' in data:
                print("\nCategory Scores:")
                for category, score in data['category_scores'].items():
                    print(f"  {category.capitalize()}: {score}")
        
        # Update the ResponseScore with new values
        new_z_score = round(random.uniform(-2.0, 2.0), 2)
        new_percentile = round(100 * (0.5 + 0.5 * math.erf(new_z_score / math.sqrt(2))), 2)
        
        new_additional_data = {
            'category_scores': {
                'anxiety': random.randint(0, 10),
                'depression': random.randint(0, 10),
                'stress': random.randint(0, 10),
                'wellbeing': random.randint(0, 10)
            },
            'subscales': {
                'cognitive': random.randint(0, 10),
                'emotional': random.randint(0, 10),
                'physical': random.randint(0, 10),
                'behavioral': random.randint(0, 10)
            }
        }
        
        # Update the record
        cursor.execute("""
            UPDATE surveys_responsescore
            SET z_score = ?, percentile = ?, additional_data = ?
            WHERE id = ?
        """, (
            new_z_score,
            new_percentile,
            json.dumps(new_additional_data),
            id
        ))
        
        # Commit the changes
        conn.commit()
        
        print("\nUpdated ResponseScore:")
        print(f"  Z-Score: {new_z_score}")
        print(f"  Percentile: {new_percentile}")
        print(f"  Additional Data: {json.dumps(new_additional_data, indent=2)}")
    else:
        print("No ResponseScore records found")
    
    # Close the connection
    conn.close()

def test_score_rule():
    """Test the ScoreRule model with the conditional_logic field"""
    print("\nTesting ScoreRule model...")
    
    # Connect to the database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Get the ScoreRule record
    cursor.execute("SELECT id, weight, conditional_logic FROM surveys_scorerule LIMIT 1")
    row = cursor.fetchone()
    
    if row:
        id, weight, conditional_logic = row
        
        print(f"Found ScoreRule with ID: {id}")
        print(f"  Weight: {weight}")
        print(f"  Conditional Logic: {conditional_logic}")
        
        # Parse the conditional_logic JSON
        if conditional_logic:
            data = json.loads(conditional_logic)
            print("\nConditional Logic Structure:")
            print(f"  If: {data.get('if', {})}")
            print(f"  Then: {data.get('then', {})}")
            if 'else' in data:
                print(f"  Else: {data.get('else', {})}")
        
        # Update the ScoreRule with new conditional logic
        new_conditional_logic = {
            'if': {
                'answer': 'Yes',
                'question_id': 1
            },
            'then': {
                'score': 15,
                'message': 'Full points awarded'
            },
            'else': {
                'if': {
                    'answer': 'Maybe',
                    'question_id': 1
                },
                'then': {
                    'score': 7,
                    'message': 'Partial points awarded'
                },
                'else': {
                    'score': 0,
                    'message': 'No points awarded'
                }
            }
        }
        
        # Update the record
        cursor.execute("""
            UPDATE surveys_scorerule
            SET conditional_logic = ?
            WHERE id = ?
        """, (
            json.dumps(new_conditional_logic),
            id
        ))
        
        # Commit the changes
        conn.commit()
        
        print("\nUpdated ScoreRule:")
        print(f"  Conditional Logic: {json.dumps(new_conditional_logic, indent=2)}")
    else:
        print("No ScoreRule records found")
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    test_response_score()
    test_score_rule()
