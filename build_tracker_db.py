"""
Name: Kezia Chacko
Program: Complete relational workout tracker database setup.
Maps out distinct routines for Bodybuilder, Athlete, and Strongman pathways.
"""


import sqlite3


def build_tracker_database():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # Temporarily bypass restrictions to ensure a clean wipe
    cursor.execute("PRAGMA foreign_keys = OFF;")
    cursor.execute("DROP TABLE IF EXISTS program_exercises;")
    cursor.execute("DROP TABLE IF EXISTS programs;")
    cursor.execute("DROP TABLE IF EXISTS equipment_options;")
    cursor.execute("DROP TABLE IF EXISTS exercises;")
    cursor.execute("DROP TABLE IF EXISTS workout_logs;")
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. Create Equipment Table
    cursor.execute("""
        CREATE TABLE equipment_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    # 2. Create Programs Table
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

    # 3. Create Master Exercises Table
    cursor.execute("""
        CREATE TABLE exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL
        );
    """)

    # 4. Create Junction Table
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

    # 5. Create Workout Logs Table
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

    # --- INJECT SEED DATA ---
    equipment = [("full_gym",), ("dumbbells_only",), ("bodyweight_only",)]
    cursor.executemany("INSERT INTO equipment_options (name) VALUES (?);", equipment)
    conn.commit()

    cursor.execute("SELECT id, name FROM equipment_options;")
    eq_map = {name: id for id, name in cursor.fetchall()}

    # Expanded robust list of unique movements
    master_exercises = [
        # Chest/Push
        ("Barbell Bench Press", "Chest"),
        ("Incline Dumbbell Press", "Chest"),
        ("Dumbbell Floor Press", "Chest"),
        ("Push-Ups", "Chest"),
        ("Dumbbell Overhead Press", "Shoulders"),
        ("Barbell Military Press", "Shoulders"),
        # Back/Pull
        ("Lat Pulldown", "Back"),
        ("Seated Cable Row", "Back"),
        ("Dumbbell One-Arm Row", "Back"),
        ("Pull-Ups", "Back"),
        ("Inverted Bodyweight Row", "Back"),
        # Legs/Lower
        ("Barbell Back Squat", "Legs"),
        ("Romanian Deadlift", "Legs"),
        ("Dumbbell Goblet Squat", "Legs"),
        ("Bodyweight Squats", "Legs"),
        ("Walking Lunges", "Legs"),
        # Explosive / Athletic / Strongman
        ("Power Clean", "Explosive"),
        ("Box Jumps", "Plyo"),
        ("Medicine Ball Slam", "Core"),
        ("Barbell Deadlift", "Strength"),
        ("Farmer's Walk", "Full Body"),
        ("Sled Push", "Conditioning")
    ]
    cursor.executemany("INSERT INTO exercises (name, category) VALUES (?, ?);", master_exercises)
    conn.commit()

    cursor.execute("SELECT id, name FROM exercises;")
    ex_map = {name: id for id, name in cursor.fetchall()}

    # ----------------------------------------------------
    # ROUTINE 1: BODYBUILDER + FULL GYM (4 Days, 60 Min)
    # ----------------------------------------------------
    cursor.execute(
        "INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins) VALUES ('bodybuilder', ?, 4, 60);",
        (eq_map["full_gym"],))
    p1_id = cursor.lastrowid
    cursor.executemany(
        "INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps) VALUES (?, ?, ?, ?);", [
            (p1_id, ex_map["Barbell Bench Press"], 4, 8),
            (p1_id, ex_map["Incline Dumbbell Press"], 3, 12),
            (p1_id, ex_map["Lat Pulldown"], 4, 10),
            (p1_id, ex_map["Seated Cable Row"], 3, 12)
        ])

    # ----------------------------------------------------
    # ROUTINE 2: BODYBUILDER + DUMBBELL ONLY (3 Days, 60 Min)
    # ----------------------------------------------------
    cursor.execute(
        "INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins) VALUES ('bodybuilder', ?, 3, 60);",
        (eq_map["dumbbells_only"],))
    p2_id = cursor.lastrowid
    cursor.executemany(
        "INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps) VALUES (?, ?, ?, ?);", [
            (p2_id, ex_map["Dumbbell Goblet Squat"], 4, 12),
            (p2_id, ex_map["Dumbbell Floor Press"], 4, 10),
            (p2_id, ex_map["Dumbbell One-Arm Row"], 3, 12),
            (p2_id, ex_map["Dumbbell Overhead Press"], 3, 10)
        ])

    # ----------------------------------------------------
    # ROUTINE 3: ATHLETE + FULL GYM (4 Days, 60 Min)
    # ----------------------------------------------------
    cursor.execute(
        "INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins) VALUES ('athlete', ?, 4, 60);",
        (eq_map["full_gym"],))
    p3_id = cursor.lastrowid
    cursor.executemany(
        "INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps) VALUES (?, ?, ?, ?);", [
            (p3_id, ex_map["Power Clean"], 4, 5),
            (p3_id, ex_map["Barbell Back Squat"], 4, 6),
            (p3_id, ex_map["Pull-Ups"], 3, 8),
            (p3_id, ex_map["Box Jumps"], 4, 6)
        ])

    # ----------------------------------------------------
    # ROUTINE 4: ATHLETE + BODYWEIGHT ONLY (3 Days, 30 Min)
    # ----------------------------------------------------
    cursor.execute(
        "INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins) VALUES ('athlete', ?, 3, 30);",
        (eq_map["bodyweight_only"],))
    p4_id = cursor.lastrowid
    cursor.executemany(
        "INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps) VALUES (?, ?, ?, ?);", [
            (p4_id, ex_map["Push-Ups"], 4, 15),
            (p4_id, ex_map["Inverted Bodyweight Row"], 4, 12),
            (p4_id, ex_map["Bodyweight Squats"], 4, 20),
            (p4_id, ex_map["Medicine Ball Slam"], 3, 15)
        ])

    # ----------------------------------------------------
    # ROUTINE 5: STRONGMAN + FULL GYM (5 Days, 90 Min)
    # ----------------------------------------------------
    cursor.execute(
        "INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins) VALUES ('strongman', ?, 5, 90);",
        (eq_map["full_gym"],))
    p5_id = cursor.lastrowid
    cursor.executemany(
        "INSERT INTO program_exercises (program_id, exercise_id, default_sets, default_reps) VALUES (?, ?, ?, ?);", [
            (p5_id, ex_map["Barbell Deadlift"], 5, 3),
            (p5_id, ex_map["Barbell Military Press"], 4, 5),
            (p5_id, ex_map["Farmer's Walk"], 4, 4),  # Reps act as distance sets here
            (p5_id, ex_map["Sled Push"], 4, 4)
        ])

    conn.commit()
    conn.close()
    print("🚀 Advanced Relational Tracker Database Completed and Ready for Action!")


if __name__ == "__main__":
    build_tracker_database()
