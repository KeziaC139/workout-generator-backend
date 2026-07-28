from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import bcrypt
from datetime import date, timedelta

app = FastAPI(title="Workout Path Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin (VS Code Live Server, Netlify, localhost, etc.)
    allow_credentials=False,  # Set to False when allow_origins is "*" to avoid browser security rejections
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATABASE INITIALIZATION & SEEDING ---
def init_auth_db():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # 1. Core Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    # 2. Multi-User Streaks Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_workout_date TEXT,
            FOREIGN KEY (username) REFERENCES users(username) ON DELETE CASCADE
        );
    """)

    # 3. Exercises Base Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL
        );
    """)

    # 4. Equipment Options Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_options (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );
    """)

    # 5. Programs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS programs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            physique TEXT NOT NULL,
            equipment_id INTEGER,
            FOREIGN KEY (equipment_id) REFERENCES equipment_options(id)
        );
    """)

    # 6. Program Exercises Link Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS program_exercises (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            program_id INTEGER,
            exercise_id INTEGER,
            default_sets INTEGER DEFAULT 3,
            default_reps INTEGER DEFAULT 10,
            FOREIGN KEY (program_id) REFERENCES programs(id),
            FOREIGN KEY (exercise_id) REFERENCES exercises(id)
        );
    """)

    # 7. Workout History Logs Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS workout_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            exercise_name TEXT,
            set_number INTEGER,
            weight_lbs REAL,
            reps_performed INTEGER,
            log_date TEXT DEFAULT CURRENT_DATE
        );
    """)

    # Migrations: Ensure username column exists in workout_logs
    try:
        cursor.execute("ALTER TABLE workout_logs ADD COLUMN username TEXT;")
    except sqlite3.OperationalError:
        pass  # Column already exists

    # --- SEED DEFAULT EXERCISES IF EMPTY ---
    cursor.execute("SELECT COUNT(*) FROM exercises;")
    if cursor.fetchone()[0] == 0:
        seed_exercises = [
            ("Push-Ups", "Chest"),
            ("Bench Press", "Chest"),
            ("Incline Dumbbell Press", "Chest"),
            ("Pull-Ups", "Back"),
            ("Lat Pulldown", "Back"),
            ("Dumbbell Row", "Back"),
            ("Bodyweight Squats", "Legs"),
            ("Barbell Squat", "Legs"),
            ("Goblet Squat", "Legs"),
            ("Dumbbell Shoulder Press", "Shoulders"),
            ("Lateral Raises", "Shoulders"),
            ("Overhead Press", "Shoulders"),
            ("Bicep Curls", "Arms"),
            ("Tricep Dips", "Arms"),
            ("Plank", "Core")
        ]
        cursor.executemany("INSERT INTO exercises (name, category) VALUES (?, ?);", seed_exercises)

    # --- SEED EQUIPMENT OPTIONS IF EMPTY ---
    cursor.execute("SELECT COUNT(*) FROM equipment_options;")
    if cursor.fetchone()[0] == 0:
        cursor.executemany("INSERT INTO equipment_options (name) VALUES (?);", [
            ("full_gym",),
            ("dumbbells_only",),
            ("bodyweight_only",)
        ])

    conn.commit()
    conn.close()


try:
    init_auth_db()
except Exception as err:
    print(f"Database initialization warning: {err}")


# --- ROOT API CHECK ENDPOINT ---
@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "Workout Path Architect API is running smoothly!",
        "docs_url": "/docs"
    }


# --- MULTI-USER STREAK ENGINE CORE LOGIC ---
def update_user_streak(username: str):
    """
    Calculates and updates consistency tracking metrics dynamically per individual user profile.
    Called automatically every time a workout log transaction successfully completes.
    """
    cleaned_username = username.lower().strip()
    today = str(date.today())
    yesterday = str(date.today() - timedelta(days=1))

    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT current_streak, longest_streak, last_workout_date FROM user_streaks WHERE username = ?;",
            (cleaned_username,)
        )
        streak_record = cursor.fetchone()

        if not streak_record:
            # First time this user has ever logged a workout
            cursor.execute("""
                INSERT INTO user_streaks (username, current_streak, longest_streak, last_workout_date) 
                VALUES (?, 1, 1, ?);
            """, (cleaned_username, today))
        else:
            current, longest, last_date = streak_record

            if last_date == today:
                # Workout already logged today, do nothing to avoid duplicate streak increments
                return
            elif last_date == yesterday:
                # Consecutive day workout! Increment streak counter
                new_current = current + 1
                new_longest = max(new_current, longest)
                cursor.execute("""
                    UPDATE user_streaks 
                    SET current_streak = ?, longest_streak = ?, last_workout_date = ?
                    WHERE username = ?;
                """, (new_current, new_longest, today, cleaned_username))
            else:
                # Streak broken! Reset current streak back down to 1 day
                cursor.execute("""
                    UPDATE user_streaks 
                    SET current_streak = 1, last_workout_date = ?
                    WHERE username = ?;
                """, (today, cleaned_username))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Streak Engine Failure: {e}")
    finally:
        conn.close()


# --- PYDANTIC SCHEMAS ---
class UserAuth(BaseModel):
    username: str
    password: str


class WorkoutRequest(BaseModel):
    physique: str
    equipment: str
    days_per_week: int = 3
    duration_mins: int = 45


class LogItem(BaseModel):
    username: str  # Associated with logged-in user
    exercise_name: str
    set_number: int
    weight_lbs: float
    reps_performed: int


# --- AUTH ENDPOINTS ---

@app.post("/signup")
@app.post("/signup/")
def signup(user: UserAuth):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        # Encrypt password using bcrypt
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(user.password.encode('utf-8'), salt)

        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?);",
            (user.username.lower().strip(), hashed_password)
        )
        conn.commit()
        return {"status": "success", "message": "User registered successfully!"}
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already exists!")
    finally:
        conn.close()


@app.post("/login")
@app.post("/login/")
def login(user: UserAuth):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT password_hash FROM users WHERE username = ?;", (user.username.lower().strip(),))
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid username or password.")

        stored_hash = result[0]

        # Verify the encrypted password
        if bcrypt.checkpw(user.password.encode('utf-8'), stored_hash):
            return {"status": "success", "username": user.username.lower().strip()}
        else:
            raise HTTPException(status_code=401, detail="Invalid username or password.")
    finally:
        conn.close()


# --- WORKOUT & HISTORY ENDPOINTS ---

@app.get("/exercises/")
@app.get("/exercises")
def get_all_exercises():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, category FROM exercises ORDER BY category, name;")
        rows = cursor.fetchall()
        return [{"name": r[0], "category": r[1]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/recommend-workout")
@app.post("/recommend-workout/")
def get_workout_recommendation(payload: WorkoutRequest):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        frontend_equipment = payload.equipment.lower().strip()
        if "gym" in frontend_equipment or "full" in frontend_equipment:
            db_equipment_name = "full_gym"
        elif "dumbbell" in frontend_equipment:
            db_equipment_name = "dumbbells_only"
        elif "bodyweight" in frontend_equipment or "body" in frontend_equipment:
            db_equipment_name = "bodyweight_only"
        else:
            db_equipment_name = frontend_equipment

        db_physique_name = payload.physique.lower().strip()

        cursor.execute("SELECT id FROM equipment_options WHERE name = ?;", (db_equipment_name,))
        eq_result = cursor.fetchone()
        eq_id = eq_result[0] if eq_result else 1

        cursor.execute("SELECT id FROM programs WHERE physique = ? AND equipment_id = ? LIMIT 1;",
                       (db_physique_name, eq_id))
        program_result = cursor.fetchone()

        if not program_result:
            cursor.execute("SELECT id FROM programs WHERE equipment_id = ? LIMIT 1;", (eq_id,))
            program_result = cursor.fetchone()

        raw_exercises = []
        if program_result:
            program_id = program_result[0]
            cursor.execute("""
                SELECT e.name, e.category, pe.default_sets, pe.default_reps
                FROM program_exercises pe
                JOIN exercises e ON pe.exercise_id = e.id
                WHERE pe.program_id = ?;
            """, (program_id,))
            raw_exercises = cursor.fetchall()

        # Fallback: if no program exists in DB, fetch standard base exercises cleanly
        if not raw_exercises:
            cursor.execute("SELECT name, category FROM exercises LIMIT 5;")
            base_rows = cursor.fetchall()
            raw_exercises = [(r[0], r[1], 3, 10) for r in base_rows]

        return {
            "status": "success",
            "exercises": [
                {
                    "name": r[0],
                    "category": r[1],
                    "default_sets": r[2] if r[2] else 3,
                    "default_reps": r[3] if r[3] else 10
                }
                for r in raw_exercises
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.post("/submit-log")
@app.post("/submit-log/")
def submit_workout_log(payload: List[LogItem]):
    if not payload:
        raise HTTPException(status_code=400, detail="Cannot log an empty training session payload sheet.")

    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        active_username = payload[0].username.lower().strip()

        log_entries = [
            (item.username.lower().strip(), item.exercise_name, item.set_number, item.weight_lbs, item.reps_performed)
            for item in payload
        ]
        cursor.executemany(
            "INSERT INTO workout_logs (username, exercise_name, set_number, weight_lbs, reps_performed) VALUES (?, ?, ?, ?, ?);",
            log_entries
        )
        conn.commit()

        # Automatically process consistency adjustments inside logging data stream
        update_user_streak(active_username)

        return {"status": "success", "message": "Successfully logged session and updated your streak!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


@app.get("/workout-history/{username}")
@app.get("/workout-history/{username}/")
def get_workout_history(username: str):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT log_date, exercise_name, set_number, weight_lbs, reps_performed 
            FROM workout_logs 
            WHERE username = ?
            ORDER BY log_date DESC;
        """, (username.lower().strip(),))
        rows = cursor.fetchall()
        return {
            "status": "success",
            "history": [
                {"date": r[0], "exercise_name": r[1], "set_number": r[2], "weight_lbs": r[3], "reps_performed": r[4]}
                for r in rows
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- STREAK & METRIC ENTRYPOINTS ---
@app.get("/streak/{username}")
@app.get("/streak/{username}/")
@app.get("/api/dashboard-metrics/{username}")
@app.get("/api/dashboard-metrics/{username}/")
def get_user_dashboard_metrics(username: str):
    cleaned_username = username.lower().strip()
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT current_streak, longest_streak FROM user_streaks WHERE username = ? LIMIT 1;",
            (cleaned_username,)
        )
        streak_row = cursor.fetchone()

        if streak_row:
            current = streak_row[0]
            longest = streak_row[1]
        else:
            current = 0
            longest = 0

        return {
            "status": "success",
            "streak_count": current,
            "current_streak": current,
            "longest_historical_streak": longest
        }
    except sqlite3.OperationalError as e:
        print(f"Database table warning: {e}")
        return {
            "status": "success",
            "streak_count": 0,
            "current_streak": 0,
            "longest_historical_streak": 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()