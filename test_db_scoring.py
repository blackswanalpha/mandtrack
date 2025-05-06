#!/usr/bin/env python
"""
Test script for enhanced scoring functionality using direct database queries.

This script tests the enhanced scoring functionality by:
1. Connecting to the database directly
2. Querying the tables to verify the new fields
3. Displaying the results
"""
import os
import sys
import sqlite3
import json

def print_separator(title=None):
    """Print a separator line with optional title"""
    width = 80
    if title:
        print(f"\n{'-' * 10} {title} {'-' * (width - 12 - len(title))}")
    else:
        print(f"\n{'-' * width}")

def connect_to_database():
    """Connect to the SQLite database"""
    try:
        # Connect to the database
        conn = sqlite3.connect('db.sqlite3')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        return conn, cursor
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None, None

def check_response_score_fields(cursor):
    """Check if the ResponseScore table has the new fields"""
    print_separator("Checking ResponseScore Fields")
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info(surveys_responsescore)")
        columns = cursor.fetchall()
        
        # Check for new fields
        field_names = [column['name'] for column in columns]
        print(f"Fields in ResponseScore table: {', '.join(field_names)}")
        
        # Check for specific fields
        new_fields = ['z_score', 'percentile', 'additional_data']
        for field in new_fields:
            if field in field_names:
                print(f"✓ Field '{field}' exists")
            else:
                print(f"✗ Field '{field}' does not exist")
        
        return all(field in field_names for field in new_fields)
    
    except Exception as e:
        print(f"Error checking ResponseScore fields: {str(e)}")
        return False

def check_score_rule_fields(cursor):
    """Check if the ScoreRule table has the new fields"""
    print_separator("Checking ScoreRule Fields")
    
    try:
        # Get table info
        cursor.execute("PRAGMA table_info(surveys_scorerule)")
        columns = cursor.fetchall()
        
        # Check for new fields
        field_names = [column['name'] for column in columns]
        print(f"Fields in ScoreRule table: {', '.join(field_names)}")
        
        # Check for specific fields
        new_fields = ['conditional_logic']
        for field in new_fields:
            if field in field_names:
                print(f"✓ Field '{field}' exists")
            else:
                print(f"✗ Field '{field}' does not exist")
        
        return all(field in field_names for field in new_fields)
    
    except Exception as e:
        print(f"Error checking ScoreRule fields: {str(e)}")
        return False

def check_test_data(cursor):
    """Check if test data exists"""
    print_separator("Checking Test Data")
    
    try:
        # Check ResponseScore data
        cursor.execute("SELECT * FROM surveys_responsescore WHERE z_score IS NOT NULL OR percentile IS NOT NULL OR additional_data IS NOT NULL")
        response_scores = cursor.fetchall()
        
        if response_scores:
            print(f"Found {len(response_scores)} ResponseScore records with enhanced data:")
            for score in response_scores:
                print(f"  ID: {score['id']}")
                print(f"  Raw Score: {score['raw_score']}")
                print(f"  Z-Score: {score['z_score']}")
                print(f"  Percentile: {score['percentile']}")
                
                if score['additional_data']:
                    try:
                        additional_data = json.loads(score['additional_data'])
                        print(f"  Additional Data: {json.dumps(additional_data, indent=2)}")
                    except:
                        print(f"  Additional Data: {score['additional_data']}")
                
                print()
        else:
            print("No ResponseScore records with enhanced data found")
        
        # Check ScoreRule data
        cursor.execute("SELECT * FROM surveys_scorerule WHERE conditional_logic IS NOT NULL")
        score_rules = cursor.fetchall()
        
        if score_rules:
            print(f"Found {len(score_rules)} ScoreRule records with conditional logic:")
            for rule in score_rules:
                print(f"  ID: {rule['id']}")
                
                if rule['conditional_logic']:
                    try:
                        conditional_logic = json.loads(rule['conditional_logic'])
                        print(f"  Conditional Logic: {json.dumps(conditional_logic, indent=2)}")
                    except:
                        print(f"  Conditional Logic: {rule['conditional_logic']}")
                
                print()
        else:
            print("No ScoreRule records with conditional logic found")
        
        return len(response_scores) > 0 or len(score_rules) > 0
    
    except Exception as e:
        print(f"Error checking test data: {str(e)}")
        return False

def main():
    """Main function"""
    print_separator("Database Changes Test")
    
    # Connect to the database
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        return
    
    try:
        # Check ResponseScore fields
        response_score_fields_ok = check_response_score_fields(cursor)
        
        # Check ScoreRule fields
        score_rule_fields_ok = check_score_rule_fields(cursor)
        
        # Check test data
        test_data_ok = check_test_data(cursor)
        
        # Print summary
        print_separator("Summary")
        print(f"ResponseScore Fields: {'✓' if response_score_fields_ok else '✗'}")
        print(f"ScoreRule Fields: {'✓' if score_rule_fields_ok else '✗'}")
        print(f"Test Data: {'✓' if test_data_ok else '✗'}")
        
        if response_score_fields_ok and score_rule_fields_ok:
            print("\nDatabase changes have been successfully applied!")
        else:
            print("\nSome database changes are missing.")
    
    finally:
        # Close the connection
        conn.close()

if __name__ == "__main__":
    main()
