import sys
import os
import datetime
import uuid

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from extensions import db
    import settings
    import psycopg2
    from werkzeug.security import generate_password_hash
    
    # User details
    FULL_NAME = "Super Admin"
    EMAIL = "admin@fmadmin.uz"
    PASSWORD = "admin_password_123" # User should change this after login
    HASHED_PASSWORD = generate_password_hash(PASSWORD)
    
    print(f"Attempting to create super admin: {EMAIL}")
    
    # Get connection from connector
    conn = db.conn
    cur = conn.cursor()
    
    # Check if user already exists
    cur.execute("SELECT id FROM users WHERE email = %s", (EMAIL,))
    user = cur.fetchone()
    
    if user:
        print(f"User {EMAIL} already exists. Updating password and role.")
        cur.execute("""
            UPDATE users 
            SET password = %s, rolename = %s, is_blocked = %s 
            WHERE email = %s
        """, (HASHED_PASSWORD, 'admin', False, EMAIL))
    else:
        print(f"Creating new user: {EMAIL}")
        now = int(datetime.datetime.now().timestamp())
        cur.execute("""
            INSERT INTO users (name, email, password, rolename, is_blocked, is_notify, created_at, register_time)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (FULL_NAME, EMAIL, HASHED_PASSWORD, 'admin', False, True, now, now))
        
    conn.commit()
    cur.close()
    
    print("Success: Super admin created/updated successfully.")
    print(f"Login: {EMAIL}")
    print(f"Password: {PASSWORD}")
    print(f"Hash: {HASHED_PASSWORD}")

except Exception as e:
    print(f"Error: {str(e)}")
    import traceback
    traceback.print_exc()
