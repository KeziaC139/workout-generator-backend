from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3
import bcrypt
from datetime import date, timedelta

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows requests from any origin (VS Code Live Server, Netlify, localhost, etc.)
    allow_credentials=False,  # Set to False when allow_origins is "*" to avoid browser security rejections
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- DATABASE INITIALIZATION FOR AUTH & STREAKS ---
def init_auth_db():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # 1. Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
    """)

    # 2. Upgraded multi-user streaks table
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

    # Check if workout_logs table needs a user_id/username column for user-specific data tracking
    try:
        cursor.execute("ALTER TABLE workout_logs ADD COLUMN username TEXT;")
    except sqlite3.OperationalError:
        pass  # Column already exists

    conn.commit()
    conn.close()


init_auth_db()


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
        print(f"Streak Engine Engine Failure: {e}")
    finally:
        conn.close()


# --- PYDANTIC SCHEMAS ---
class UserAuth(BaseModel):
    username: str
    password: str


class WorkoutRequest(BaseModel):
    physique: str
    equipment: str
    days_per_week: int
    duration_mins: int


class LogItem(BaseModel):
    username: str  # Associated with logged-in user
    exercise_name: str
    set_number: int
    weight_lbs: float
    reps_performed: int


# --- AUTH ENDPOINTS ---

@app.post("/signup")
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

        if not program_result:
            raise HTTPException(status_code=404, detail="Database completely empty.")

        program_id = program_result[0]

        cursor.execute("""
            SELECT e.name, e.category, pe.default_sets, pe.default_reps
            FROM program_exercises pe
            JOIN exercises e ON pe.exercise_id = e.id
            WHERE pe.program_id = ?;
        """, (program_id,))
        raw_exercises = cursor.fetchall()

        return {"status": "success",
                "exercises": [{"name": r[0], "category": r[1], "default_sets": r[2], "default_reps": r[3]} for r in
                              raw_exercises]}
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
        # Extract target user information cleanly out of first incoming element parameter row
        active_username = payload[0].username.lower().strip()

        log_entries = [
            (item.username.lower().strip(), item.exercise_name, item.set_number, item.weight_lbs, item.reps_performed)
            for
            item in payload]
        cursor.executemany(
            "INSERT INTO workout_logs (username, exercise_name, set_number, weight_lbs, reps_performed) VALUES (?, ?, ?, ?, ?);",
            log_entries)
        conn.commit()

        # --- THE CORE INTEGRATION ACTION ---
        # Automatically process consistency adjustments right here inside the logging data stream!
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
        # Strictly filters history data by the logged-in user!
        cursor.execute("""
            SELECT log_date, exercise_name, set_number, weight_lbs, reps_performed 
            FROM workout_logs 
            WHERE username = ?
            ORDER BY log_date DESC;
        """, (username.lower().strip(),))
        rows = cursor.fetchall()
        return {"status": "success", "history": [
            {"date": r[0], "exercise_name": r[1], "set_number": r[2], "weight_lbs": r[3], "reps_performed": r[4]} for r
            in rows]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()


# --- FIXED METRIC ENTRYPOINTS FOR STREAK INTERFACE ---
@app.get("/streak/{username}")
@app.get("/streak/{username}/")
@app.get("/api/dashboard-metrics/{username}")
@app.get("/api/dashboard-metrics/{username}/")
def get_user_dashboard_metrics(username: str):
    """
    Exposes computed real-time streak calculations to the dashboard UI layout grid.
    Supports both the new direct /streak route and legacy dashboard metric routes.
    """
    cleaned_username = username.lower().strip()
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        # Check if the record exists; if not, safely initialize it to 0 instead of breaking
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
        # If the table doesn't exist yet in SQLite, fail gracefully by returning 0
        # instead of throwing a 500 crash error.
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