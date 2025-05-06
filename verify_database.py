import sqlite3

def verify_database():
    """Verify that the database has the correct tables and columns"""
    print("Verifying database...")
    
    # Connect to the database
    conn = sqlite3.connect('db.sqlite3')
    cursor = conn.cursor()
    
    # Check if the ResponseScore table has the new fields
    cursor.execute("PRAGMA table_info(surveys_responsescore)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    print("ResponseScore columns:", column_names)
    
    # Check if the z_score, percentile, and additional_data fields exist
    if 'z_score' in column_names and 'percentile' in column_names and 'additional_data' in column_names:
        print("✅ ResponseScore has the new fields")
    else:
        print("❌ ResponseScore is missing some fields")
        
    # Check if the ScoreRule table has the conditional_logic field
    cursor.execute("PRAGMA table_info(surveys_scorerule)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    print("ScoreRule columns:", column_names)
    
    # Check if the conditional_logic field exists
    if 'conditional_logic' in column_names:
        print("✅ ScoreRule has the conditional_logic field")
    else:
        print("❌ ScoreRule is missing the conditional_logic field")
    
    # Check the data in the ResponseScore table
    cursor.execute("SELECT id, raw_score, z_score, percentile, additional_data FROM surveys_responsescore")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} ResponseScore records:")
    for row in rows:
        print(f"  ID: {row[0]}")
        print(f"  Raw Score: {row[1]}")
        print(f"  Z-Score: {row[2]}")
        print(f"  Percentile: {row[3]}")
        print(f"  Additional Data: {row[4]}")
        print()
    
    # Check the data in the ScoreRule table
    cursor.execute("SELECT id, weight, conditional_logic FROM surveys_scorerule")
    rows = cursor.fetchall()
    
    print(f"Found {len(rows)} ScoreRule records:")
    for row in rows:
        print(f"  ID: {row[0]}")
        print(f"  Weight: {row[1]}")
        print(f"  Conditional Logic: {row[2]}")
        print()
    
    # Close the connection
    conn.close()

if __name__ == "__main__":
    verify_database()
