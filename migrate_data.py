import sqlite3
import psycopg2

# 1. LOCAL SQLITE DATABASE FILE
SQLITE_DB = "workout_app.db"

# 2. RENDER EXTERNAL DATABASE URL (Paste your copied URL here)
# Make sure it starts with "postgresql://"
POSTGRES_URL = "postgresql://workout_db_2yhe_user:4eiGJo57wEy65tuNome4r5ZQfJflZIoP@dpg-d9jvh3jm8hqs73b9894g-a.oregon-postgres.render.com/workout_db_2yhe"

def migrate():
    print("🚀 Starting data migration from SQLite to Render PostgreSQL...")

    # Connect to local SQLite
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    # Connect to Render PostgreSQL
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cursor = pg_conn.cursor()

    try:
        # --- MIGRATE USERS ---
        print("\n📦 Migrating 'users' table...")
        sqlite_cursor.execute("SELECT username, password_hash FROM users")
        users = sqlite_cursor.fetchall()

        user_count = 0
        for username, password_hash in users:
            clean_username = username.strip().lower()
            # ON CONFLICT DO NOTHING prevents errors if you already created the account on Render
            pg_cursor.execute("""
                INSERT INTO users (username, password_hash, created_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (username) DO NOTHING;
            """, (clean_username, password_hash))
            user_count += 1

        print(f"✅ Processed {user_count} user record(s).")

        # --- MIGRATE WORKOUT LOGS ---
        print("\n📦 Migrating 'workout_logs' table...")
        sqlite_cursor.execute("""
            SELECT username, exercise_name, set_number, weight_lbs, reps_performed, log_date 
            FROM workout_logs
        """)
        logs = sqlite_cursor.fetchall()

        log_count = 0
        for username, exercise_name, set_number, weight_lbs, reps_performed, log_date in logs:
            clean_username = username.strip().lower()
            pg_cursor.execute("""
                INSERT INTO workout_logs (username, exercise_name, set_number, weight_lbs, reps_performed, log_date, timestamp)
                VALUES (%s, %s, %s, %s, %s, %s, NOW());
            """, (clean_username, exercise_name, set_number, weight_lbs, reps_performed, log_date))
            log_count += 1

        print(f"✅ Processed {log_count} workout log record(s).")

        # Commit changes to PostgreSQL
        pg_conn.commit()
        print("\n🎉 MIGRATION COMPLETE! All data successfully transferred to Render.")

    except Exception as e:
        pg_conn.rollback()
        print(f"\n❌ Migration failed: {e}")

    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    migrate()