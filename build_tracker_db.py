"""
Name: Kezia Chacko
Program: Builds tracker database to split exercises and sets so user can
input their own data and track their workouts.
"""

import sqlite3


def build_tracker_database():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # 1. TEMPORARILY TURN OFF FOREIGN KEYS SO WE CAN CLEAN UP
    cursor.execute("PRAGMA foreign_keys = OFF;")

    # Clear out old layout completely to avoid conflicts
    cursor.execute("DROP TABLE IF EXISTS program_exercises;")
    cursor.execute("DROP TABLE IF EXISTS programs;")
    cursor.execute("DROP TABLE IF EXISTS equipment_options;")
    cursor.execute("DROP TABLE IF EXISTS exercises;")
    cursor.execute("DROP TABLE IF EXISTS workout_logs;")

    # 2. TURN IT BACK ON NOW THAT THE CANVAS IS CLEAN
    cursor.execute("PRAGMA foreign_keys = ON;")

    # Re-create Equipment Table
    # ... (rest of your table creation code stays exactly the same)
    #Re-create Equipment Table
    cursor.execute("""
        CREATE TABLE equipment_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    #Create Programs Table (Stripped of the text block column)
    cursor.execute("""
        CREATE TABLE programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            physique TEXT NOT NULL,
            equipment_id INTEGER NOT NULL,
            days_per_week INTEGER NOT NULL,
            duration_mins INTEGER NOT NULL,
            FOREIGN KEY (equipment_id) REFERENCES equipment_options(id)
        );
    """)

    #Create Master Exercises Table
    cursor.execute("""
        CREATE TABLE exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL -- e.g., Chest, Back, Legs, Plyo
        );
    """)

    #Create Program-Exercises Junction Table (Connects templates to exercises)
    cursor.execute("""
        CREATE TABLE program_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER NOT NULL,
            exercise_id INTEGER NOT NULL,
            default_sets INTEGER NOT NULL DEFAULT 3,
            default_reps INTEGER NOT NULL DEFAULT 10,
            FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE,
            FOREIGN KEY (exercise_id) REFERENCES exercises(id) ON DELETE CASCADE
        );
    """)

    #Create Workout Logs Table (This captures user-entered tracking data)
    cursor.execute("""
        CREATE TABLE workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            exercise_name TEXT NOT NULL,
            set_number INTEGER NOT NULL,
            weight_lbs REAL,
            reps_performed INTEGER
        );
    """)

    # --- INJECT DATA ---

    #Insert Equipment Options
    equipment = [("full_gym",), ("dumbbells_only",), ("bodyweight_only",)]
    cursor.executemany("INSERT INTO equipment_options (name) VALUES (?);", equipment)
    conn.commit()

    #Get Equipment IDs
    cursor.execute("SELECT id, name FROM equipment_options;")
    eq_map = {name: id for id, name in cursor.fetchall()}

    #Insert Master Exercise List
    master_exercises = [
        ("Barbell Bench Press", "Chest"),
        ("Incline Dumbbell Press", "Chest"),
        ("Lat Pulldown", "Back"),
        ("Seated Cable Row", "Back"),
        ("Barbell Back Squat", "Legs"),
        ("Romanian Deadlift", "Legs"),
        ("Dumbbell Goblet Squat", "Legs"),
        ("Dumbbell Floor Press", "Chest"),
        ("Dumbbell One-Arm Row", "Back")
    ]
    cursor.executemany("INSERT INTO exercises (name, category) VALUES (?, ?);", master_exercises)
    conn.commit()

    #Get Exercise IDs
    cursor.execute("SELECT id, name FROM exercises;")
    ex_map = {name: id for id, name in cursor.fetchall()}

    #Insert a 4-Day Full Gym Bodybuilder Program Template
    cursor.execute("""
        INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins)
        VALUES ('bodybuilder', ?, 4, 60);
    """, (eq_map["full_gym"],))
    bodybuilder_program_id = cursor.lastrowid

    #Link exercises specifically to that Bodybuilder Template
    #Format: (program_id, exercise_id, sets, reps)
    bodybuilder_exercises = [
        (bodybuilder_program_id, ex_map["Barbell Bench Press"], 4, 8),
        (bodybuilder_program_id, ex_map["Incline Dumbbell Press"], 3, 12),
        (bodybuilder_program_id, ex_map["Lat Pulldown"], 4, 10),
        (bodybuilder_program_id, ex_map["Seated Cable Row"], 3, 12)
    ]
    cursor.executemany("""
        INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps)
        VALUES (?, ?, ?, ?);
    """, bodybuilder_exercises)

    #Insert a 3-Day Dumbbell Only Bodybuilder Program Template
    cursor.execute("""
        INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins)
        VALUES ('bodybuilder', ?, 3, 60);
    """, (eq_map["dumbbells_only"],))
    db_program_id = cursor.lastrowid

    db_exercises = [
        (db_program_id, ex_map["Dumbbell Goblet Squat"], 4, 12),
        (db_program_id, ex_map["Dumbbell Floor Press"], 4, 10),
        (db_program_id, ex_map["Dumbbell One-Arm Row"], 3, 12)
    ]
    cursor.executemany("""
        INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps)
        VALUES (?, ?, ?, ?);
    """, db_exercises)

    # --- ADD AN ATHLETE TEMPLATE ---
    cursor.execute("""
            INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins)
            VALUES ('athlete', ?, 3, 30);
        """, (eq_map["dumbbells_only"],))
    athlete_program_id = cursor.lastrowid

    # Link some of your master exercises to this Athlete template
    athlete_exercises = [
        (athlete_program_id, ex_map["Dumbbell Goblet Squat"], 3, 12),
        (athlete_program_id, ex_map["Dumbbell One-Arm Row"], 3, 10)
    ]
    cursor.executemany("""
            INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps)
            VALUES (?, ?, ?, ?);
        """, athlete_exercises)


    conn.commit()
    conn.close()
    print("🚀 Advanced Relational Tracker Database Configured Perfectly!")


if __name__ == "__main__":
    build_tracker_database()
