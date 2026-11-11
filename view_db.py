import sqlite3
import os
import sys

# Ensure UTF-8 output on Windows terminal
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')

def view_data():
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 75)
    print("                CROSS-ECHO SQLITE DATABASE VIEWER")
    print("=" * 75)

    # 1. Show all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n[TABLES FOUND]: {', '.join(tables)}\n")

    # 2. Show Users
    print("-" * 75)
    print("[TABLE: users]")
    print("-" * 75)
    cursor.execute("SELECT id, username, email, created_at FROM users;")
    users = cursor.fetchall()
    if users:
        print(f"{'ID':<5} {'Username':<20} {'Email':<25} {'Created At'}")
        print("-" * 75)
        for u in users:
            print(f"{u[0]:<5} {u[1]:<20} {u[2]:<25} {str(u[3])}")
    else:
        print("No users found.")

    # 3. Show Navigation History (Detections)
    cursor.execute("SELECT COUNT(*) FROM navigation_history;")
    total_logs = cursor.fetchone()[0]
    print("\n" + "-" * 75)
    print(f"[TABLE: navigation_history] (Total Records: {total_logs})")
    print("Showing latest 15 detections:")
    print("-" * 75)
    cursor.execute("""
        SELECT id, object_name, confidence, distance, direction, timestamp 
        FROM navigation_history 
        ORDER BY id DESC 
        LIMIT 15;
    """)
    logs = cursor.fetchall()
    if logs:
        print(f"{'ID':<6} {'Object':<15} {'Confidence':<12} {'Distance':<12} {'Direction':<10} {'Timestamp'}")
        print("-" * 75)
        for log in logs:
            conf_str = f"{round(log[2] * 100, 1)}%"
            dist_str = f"{log[3]}m" if log[3] and log[3] > 0 else "N/A"
            dir_str = log[4] if log[4] else "Center"
            time_str = str(log[5]).split('.')[0] if log[5] else ""
            print(f"{log[0]:<6} {log[1]:<15} {conf_str:<12} {dist_str:<12} {dir_str:<10} {time_str}")
    else:
        print("No navigation logs found.")

    # 4. Obstacle Summary
    cursor.execute("""
        SELECT object_name, COUNT(*) as cnt 
        FROM navigation_history 
        GROUP BY object_name 
        ORDER BY cnt DESC;
    """)
    summary = cursor.fetchall()
    if summary:
        print("\n" + "-" * 75)
        print("[OBSTACLE SUMMARY COUNTS]")
        print("-" * 75)
        for obj, count in summary:
            print(f"  * {obj.capitalize():<15}: {count} times detected")

    print("\n" + "=" * 75)
    conn.close()

if __name__ == '__main__':
    view_data()

