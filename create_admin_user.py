#!/usr/bin/env python
"""
Standalone script to create an admin user in the Neon PostgreSQL database.
This script can be run locally to ensure the admin user exists.

Usage:
    python create_admin_user.py
"""

import os
import sys
import subprocess
import argparse

def main():
    """Main function to parse arguments and create the admin user."""
    parser = argparse.ArgumentParser(description='Create an admin user in the Neon PostgreSQL database.')
    parser.add_argument('--email', default='admin12@example.com', help='Admin email address')
    parser.add_argument('--password', default='admin1234', help='Admin password')
    parser.add_argument('--first-name', default='Admin', help='Admin first name')
    parser.add_argument('--last-name', default='User', help='Admin last name')
    
    args = parser.parse_args()
    
    # Check if psycopg2 is installed
    try:
        import psycopg2
    except ImportError:
        print("psycopg2 is not installed. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    
    # Import the upload_admin_to_neon module
    try:
        import upload_admin_to_neon
        
        # Create the admin user
        success = upload_admin_to_neon.create_admin_user(
            args.email, 
            args.password, 
            args.first_name, 
            args.last_name
        )
        
        if success:
            print("Admin user creation/update completed successfully.")
        else:
            print("Admin user creation/update failed.")
            sys.exit(1)
    
    except ImportError:
        print("Error: upload_admin_to_neon.py not found in the current directory.")
        sys.exit(1)

if __name__ == '__main__':
    main()
