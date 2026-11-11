import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash

DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'crossecho.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'schema.sql')

def get_db_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database using the schema.sql file if it doesn't already exist or if tables are missing."""
    if not os.path.exists(DATABASE_PATH):
        print("Database file not found, creating a new one...")
        
    conn = get_db_connection()
    try:
        with open(SCHEMA_PATH, 'r') as f:
            conn.executescript(f.read())
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        conn.close()

def register_user(username, email, password):
    """Registers a new user after hashing their password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        password_hash = generate_password_hash(password)
        cursor.execute(
            "INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)",
            (username, email, password_hash)
        )
        conn.commit()
        return True, "Registration successful!"
    except sqlite3.IntegrityError as e:
        error_msg = str(e)
        if 'users.username' in error_msg or 'username' in error_msg:
            return False, "Username is already taken."
        elif 'users.email' in error_msg or 'email' in error_msg:
            return False, "Email address is already registered."
        return False, "User with this username or email already exists."
    except Exception as e:
        return False, f"An error occurred: {e}"
    finally:
        conn.close()

def authenticate_user(username_or_email, password):
    """Authenticates a user via username or email and verifies their password."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Search by username or email
        cursor.execute(
            "SELECT * FROM users WHERE username = ? OR email = ?",
            (username_or_email, username_or_email)
        )
        user = cursor.fetchone()
        if user and check_password_hash(user['password_hash'], password):
            return {
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            }
        return None
    except Exception as e:
        print(f"Authentication error: {e}")
        return None
    finally:
        conn.close()

def log_detection(user_id, object_name, confidence):
    """Logs a successful object detection event."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO detections (user_id, object_name, confidence) VALUES (?, ?, ?)",
            (user_id, object_name, confidence)
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Error logging detection: {e}")
        return False
    finally:
        conn.close()

def get_recent_detections(user_id, limit=10):
    """Retrieves the most recent detections for a given user."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT object_name, confidence, timestamp FROM detections WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        print(f"Error retrieving recent detections: {e}")
        return []
    finally:
        conn.close()

def get_user_stats(user_id):
    """Calculates statistics for the user dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()
    stats = {
        'total_detections': 0,
        'today_detections': 0,
        'top_object': 'N/A',
        'object_counts': {}
    }
    try:
        # Total detections
        cursor.execute("SELECT COUNT(*) FROM detections WHERE user_id = ?", (user_id,))
        stats['total_detections'] = cursor.fetchone()[0]

        # Today's detections (SQLite uses datetime, so we filter by date)
        cursor.execute(
            "SELECT COUNT(*) FROM detections WHERE user_id = ? AND date(timestamp) = date('now', 'localtime')", 
            (user_id,)
        )
        stats['today_detections'] = cursor.fetchone()[0]

        # Top detected object
        cursor.execute(
            "SELECT object_name, COUNT(*) as cnt FROM detections WHERE user_id = ? GROUP BY object_name ORDER BY cnt DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        if row:
            stats['top_object'] = f"{row['object_name'].capitalize()} ({row['cnt']})"

        # Counts per object type for visual charts/breakdown
        cursor.execute(
            "SELECT object_name, COUNT(*) as cnt FROM detections WHERE user_id = ? GROUP BY object_name ORDER BY cnt DESC",
            (user_id,)
        )
        rows = cursor.fetchall()
        stats['object_counts'] = {r['object_name']: r['cnt'] for r in rows}

    except Exception as e:
        print(f"Error gathering stats: {e}")
    finally:
        conn.close()
    return stats
