#!/usr/bin/env python
"""
Script to create an admin user directly in the Neon PostgreSQL database.
This script is designed to be run during the Vercel build process.
"""

import os
import sys
import psycopg2
import hashlib
import uuid
import datetime

# Database connection string
DATABASE_URL = "postgresql://mindtrack_db_owner:npg_AUV4r3qElnDN@ep-steep-base-a2xkorr1-pooler.eu-central-1.aws.neon.tech/mindtrack_db?sslmode=require"

# Admin user credentials
ADMIN_EMAIL = "admin12@example.com"
ADMIN_PASSWORD = "admin1234"
ADMIN_FIRST_NAME = "Admin"
ADMIN_LAST_NAME = "User"

def create_password_hash(password):
    """
    Create a Django-compatible password hash.
    This is a simplified version of Django's make_password function.
    """
    # Generate a random salt
    salt = uuid.uuid4().hex

    # Hash the password with the salt
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        150000,  # Django's default iterations
        dklen=32
    ).hex()

    # Format the hash in Django's format
    return f"pbkdf2_sha256$150000${salt}${hashed}"

def create_admin_user():
    """
    Create an admin user directly in the Neon PostgreSQL database.
    """
    try:
        # Connect to the database
        print(f"Connecting to database: {DATABASE_URL}")
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor()

        # Check if the users_user table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'users_user'
            );
        """)
        table_exists = cursor.fetchone()[0]

        if not table_exists:
            print("Error: The users_user table does not exist. Make sure migrations have been applied.")
            return False

        # Check if the user already exists
        cursor.execute("SELECT id FROM users_user WHERE email = %s", (ADMIN_EMAIL,))
        user = cursor.fetchone()

        if user:
            user_id = user[0]
            print(f"User with email {ADMIN_EMAIL} already exists (ID: {user_id}). Updating password...")

            # Generate a username from the email if needed
            username = ADMIN_EMAIL.split('@')[0]

            # Get current timestamp
            now = datetime.datetime.now()

            # Update the existing user
            cursor.execute("""
                UPDATE users_user
                SET password = %s,
                    username = %s,
                    first_name = %s,
                    last_name = %s,
                    is_active = TRUE,
                    is_staff = TRUE,
                    is_superuser = TRUE,
                    updated_at = %s,
                    date_joined = COALESCE(date_joined, %s),
                    role = COALESCE(role, 'admin'),
                    email_verified = TRUE,
                    failed_login_attempts = 0,
                    force_password_change = FALSE
                WHERE id = %s
            """, (
                create_password_hash(ADMIN_PASSWORD),
                username,
                ADMIN_FIRST_NAME,
                ADMIN_LAST_NAME,
                now,
                now,  # date_joined (only used if current value is NULL)
                user_id
            ))

            print(f"User {ADMIN_EMAIL} updated successfully!")
        else:
            # Create a new user
            print(f"Creating new admin user with email: {ADMIN_EMAIL}")

            # Generate a username from the email
            username = ADMIN_EMAIL.split('@')[0]

            # Get current timestamp
            now = datetime.datetime.now()

            # Generate a UUID for the user ID
            user_id = str(uuid.uuid4())

            # Insert the new user with a generated UUID
            cursor.execute("""
                INSERT INTO users_user (
                    id, email, username, password, first_name, last_name,
                    is_active, is_staff, is_superuser,
                    created_at, updated_at, date_joined, role, email_verified,
                    failed_login_attempts, force_password_change
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
            """, (
                user_id,
                ADMIN_EMAIL,
                username,
                create_password_hash(ADMIN_PASSWORD),
                ADMIN_FIRST_NAME,
                ADMIN_LAST_NAME,
                True,  # is_active
                True,  # is_staff
                True,  # is_superuser
                now,
                now,
                now,  # date_joined
                'admin',  # role
                True,  # email_verified
                0,  # failed_login_attempts
                False  # force_password_change
            ))

            # Get the generated ID
            next_id = cursor.fetchone()[0]

            print(f"Admin user {ADMIN_EMAIL} created successfully with ID: {next_id}!")

        # Commit the changes
        conn.commit()

        # Verify the user exists
        cursor.execute("SELECT id, email, is_superuser FROM users_user WHERE email = %s", (ADMIN_EMAIL,))
        user = cursor.fetchone()
        if user:
            print(f"Verified user exists: ID={user[0]}, Email={user[1]}, Is Superuser={user[2]}")
        else:
            print("Warning: Could not verify user after creation/update.")

        return True

    except Exception as e:
        print(f"Error creating admin user: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if 'conn' in locals():
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    success = create_admin_user()

    if success:
        print("Admin user creation/update completed successfully.")
        sys.exit(0)
    else:
        print("Admin user creation/update failed.")
        sys.exit(1)
