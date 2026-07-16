"""
Name: Kezia Chacko
Program: Production-ready relational workout tracker database setup.
Upgraded to support non-destructive seeding, streak tracking, and analytical views.
"""

import sqlite3


def build_tracker_database():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # Enforce foreign key constraints at the SQLite engine level
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Create Core Schema Tables (IF NOT EXISTS protects existing user data)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            physique TEXT NOT NULL,
            equipment_id INTEGER NOT NULL,
            days_per_week INTEGER NOT NULL,
            duration_mins INTEGER NOT NULL,
            FOREIGN KEY (equipment_id) REFERENCES equipment_options(id),
            UNIQUE(physique, equipment_id) -- Prevents duplicate routine profiles
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            default_sets INTEGER NOT NULL DEFAULT 3,
            default_reps INTEGER NOT NULL DEFAULT 10,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE,
            UNIQUE(program_id, exercise_id) -- An exercise can only be in a program once
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            weight_lbs REAL,
            reps_performed INTEGER
        );
    """)

    # 2. FEATURE UPGRADE: Create User Streaks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_workout_date TEXT UNIQUE
        );
    """)

    # 3. FEATURE UPGRADE: Add Analytical Database Views for Progress Metrics
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_exercise_analytics AS
        SELECT 
            exercise_name,
            COUNT(DISTINCT DATE(log_date)) as total_days_performed,
            MAX(weight_lbs) as personal_record_weight,
            SUM(set_number) as total_sets_completed,
            AVG(reps_performed) as average_reps_per_set
        FROM workout_logs
        GROUP BY exercise_name;
    """)

    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_weekly_volume_trends AS
        SELECT 
            STRFTIME('%W', log_date) AS calendar_week,
            exercise_name,
            SUM(weight_lbs * reps_performed) AS total_weekly_volume_lbs,
            COUNT(id) AS total_reps_logged
        FROM workout_logs
        GROUP BY calendar_week, exercise_name;
    """)

    # --- SAFE SEEDING VIA TRANSACTIONS ---
    try:
        # INSERT OR IGNORE allows running this script anytime to add new data without crashing
        equipment = [("full_gym",), ("dumbbells_only",), ("bodyweight_only",)]
        cursor.executemany("INSERT OR IGNORE INTO equipment_options (name) VALUES (?);", equipment)

        master_exercises = [
            # Base Movements
            ("Barbell Bench Press", "Chest"), ("Incline Dumbbell Press", "Chest"),
            ("Dumbbell Floor Press", "Chest"), ("Push-Ups", "Chest"),
            ("Dumbbell Overhead Press", "Shoulders"), ("Barbell Military Press", "Shoulders"),
            ("Lat Pulldown", "Back"), ("Seated Cable Row", "Back"),
            ("Dumbbell One-Arm Row", "Back"), ("Pull-Ups", "Back"),
            ("Inverted Bodyweight Row", "Back"), ("Barbell Back Squat", "Legs"),
            ("Romanian Deadlift", "Legs"), ("Dumbbell Goblet Squat", "Legs"),
            ("Bodyweight Squats", "Legs"), ("Walking Lunges", "Legs"),
            ("Power Clean", "Explosive"), ("Box Jumps", "Plyo"),
            ("Medicine Ball Slam", "Core"), ("Barbell Deadlift", "Strength"),
            ("Farmer's Walk", "Full Body"), ("Sled Push", "Conditioning"),

            # --- EXTENDED EXERCISE ARCHETYPES ---
            # Barbell
            ("Barbell Romanian Deadlift", "Legs"), ("Overhead Barbell Press", "Shoulders"),
            ("Barbell Pendlay Row", "Back"), ("Close-Grip Barbell Bench Press", "Triceps"),
            ("Barbell Front Squat", "Legs"),
            # Dumbbell
            ("Dumbbell Bulgarian Split Squat", "Legs"), ("Incline Dumbbell Chest Fly", "Chest"),
            ("Dumbbell Lateral Raise", "Shoulders"), ("Dumbbell Hammer Curl", "Arms"),
            ("Chest-Supported Dumbbell Row", "Back"),
            # Bodyweight
            ("Deficit Push-Up", "Chest"), ("Hanging Leg Raise", "Core"),
            ("Bodyweight Bench Dip", "Triceps"), ("Walking Bodyweight Lunge", "Legs")
        ]
        cursor.executemany("INSERT OR IGNORE INTO exercises (name, category) VALUES (?, ?);", master_exercises)

        # Commit core lookup data so subqueries work properly
        conn.commit()

        # Helper function to dynamically establish programs and map their relative schedules
        def register_program_with_exercises(physique, eq_name, days, duration, exercise_list):
            cursor.execute("SELECT id FROM equipment_options WHERE name = ?;", (eq_name,))
            eq_id_row = cursor.fetchone()
            if not eq_id_row:
                return
            eq_id = eq_id_row[0]

            cursor.execute("""
                INSERT OR IGNORE INTO programs (physique, equipment_id, days_per_week, duration_mins)
                VALUES (?, ?, ?, ?);
            """, (physique, eq_id, days, duration))

            cursor.execute("SELECT id FROM programs WHERE physique = ? AND equipment_id = ?;", (physique, eq_id))
            program_id = cursor.fetchone()[0]

            for ex_name, default_sets, default_reps in exercise_list:
                cursor.execute("""
                    INSERT OR IGNORE INTO program_exercises (program_id, exercise_id, default_sets, default_reps)
                    SELECT ?, id, ?, ? FROM exercises WHERE name = ?;
                """, (program_id, default_sets, default_reps, ex_name))

        # ----------------------------------------------------
        # ASSIGN PATHWAYS DYNAMICALLY
        # ----------------------------------------------------
        register_program_with_exercises("bodybuilder", "full_gym", 4, 60, [
            ("Barbell Bench Press", 4, 8),
            ("Incline Dumbbell Press", 3, 12),
            ("Lat Pulldown", 4, 10),
            ("Seated Cable Row", 3, 12)
        ])

        register_program_with_exercises("bodybuilder", "dumbbells_only", 3, 60, [
            ("Dumbbell Goblet Squat", 4, 12),
            ("Dumbbell Floor Press", 4, 10),
            ("Dumbbell One-Arm Row", 3, 12),
            ("Dumbbell Overhead Press", 3, 10)
        ])

        register_program_with_exercises("athlete", "full_gym", 4, 60, [
            ("Power Clean", 4, 5),
            ("Barbell Back Squat", 4, 6),
            ("Pull-Ups", 3, 8),
            ("Box Jumps", 4, 6)
        ])

        register_program_with_exercises("athlete", "bodyweight_only", 3, 30, [
            ("Push-Ups", 4, 15),
            ("Inverted Bodyweight Row", 4, 12),
            ("Bodyweight Squats", 4, 20),
            ("Medicine Ball Slam", 3, 15)
        ])

        register_program_with_exercises("strongman", "full_gym", 5, 90, [
            ("Barbell Deadlift", 5, 3),
            ("Barbell Military Press", 4, 5),
            ("Farmer's Walk", 4, 4),
            ("Sled Push", 4, 4)
        ])

        conn.commit()
        print("🚀 Upgraded Database Infrastructure Constructed and Synchronized Safely!")

    except sqlite3.Error as e:
        conn.rollback()
        print(f"❌ Database Initialization Failed. Rolled back changes. Error: {e}")
    finally:
        conn.close()


def update_user_streak():
    """
    Optional standalone utility function to manage user habits.
    Can be imported and called inside your API row logger.
    """
    from datetime import date, timedelta

    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT current_streak, longest_streak, last_workout_date FROM user_streaks LIMIT 1;")
        streak_record = cursor.fetchone()

        if not streak_record:
            cursor.execute("""
                INSERT INTO user_streaks (current_streak, longest_streak, last_workout_date) 
                VALUES (1, 1, ?);
            """, (today,))
        else:
            current, longest, last_date = streak_record

            if last_date == today:
                return
            elif last_date == yesterday:
                new_current = current + 1
                new_longest = max(new_current, longest)
                cursor.execute("""
                    UPDATE user_streaks 
                    SET current_streak = ?, longest_streak = ?, last_workout_date = ?;
                """, (new_current, new_longest, today))
            else:
                cursor.execute("""
                    UPDATE user_streaks 
                    SET current_streak = 1, last_workout_date = ?;
                """, (today,))
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    build_tracker_database()