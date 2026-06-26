"""
Name: Kezia Chacko
Program: FastAPI backend service for the Custom Fitness Tracker app.
Handles workout recommendations with a flexible fallback strategy and logs session data to SQLite.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import sqlite3

app = FastAPI()

# Enable CORS so your local frontend index.html can communicate with the backend port
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- PYDANTIC SCHEMAS ---
class WorkoutRequest(BaseModel):
    physique: str
    equipment: str
    days_per_week: int
    duration_mins: int

class LogItem(BaseModel):
    exercise_name: str
    set_number: int
    weight_lbs: float
    reps_performed: int


# --- API ENDPOINTS ---

@app.get("/")
def read_root():
    return {"message": "Fitness Tracker Engine API is live and operational!"}


@app.get("/exercises")
@app.get("/exercises/")
def get_all_exercises():
    """Returns the full list of master exercises to populate the frontend swap dropdowns."""
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name, category FROM exercises ORDER BY category, name;")
        rows = cursor.fetchall()
        return [{"name": r[0], "category": r[1]} for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch master exercise list: {str(e)}")
    finally:
        conn.close()


@app.post("/recommend-workout")
@app.post("/recommend-workout/")
def get_workout_recommendation(payload: WorkoutRequest):
    """Queries the database for a routine matching the user's archetype with a flexible fallback strategy."""
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    try:
        # 1. Normalize strings to avoid case or spacing mismatches from frontend buttons
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

        # 2. Get Equipment ID
        cursor.execute("SELECT id FROM equipment_options WHERE name = ?;", (db_equipment_name,))
        eq_result = cursor.fetchone()
        if not eq_result:
            eq_id = 1  # Standard emergency fallback if equipment mapping breaks
        else:
            eq_id = eq_result[0]

        # 3. DUAL-STAGE SEARCH WITH AN ABSOLUTE CATCH-ALL
        # Stage A: Try finding the exact user request match (Physique + Equipment)
        cursor.execute("""
            SELECT id FROM programs 
            WHERE physique = ? AND equipment_id = ?
            LIMIT 1;
        """, (db_physique_name, eq_id))
        program_result = cursor.fetchone()

        # Stage B Fallback: If that combination doesn't exist, grab ANY routine matching this equipment style
        if not program_result:
            cursor.execute("""
                SELECT id FROM programs 
                WHERE equipment_id = ?
                LIMIT 1;
            """, (eq_id,))
            program_result = cursor.fetchone()

        # Stage C Fallback: Absolute bulletproof safety. If still nothing, give the very first routine in the database
        if not program_result:
            cursor.execute("SELECT id FROM programs LIMIT 1;")
            program_result = cursor.fetchone()

        # Final failure state check if database is entirely blank
        if not program_result:
            raise HTTPException(status_code=404, detail="The workout database appears to be completely empty. Please run build_tracker_db.py!")

        program_id = program_result[0]

        # 4. Fetch the exercises mapped to whatever program ID we settled on
        cursor.execute("""
            SELECT e.name, e.category, pe.default_sets, pe.default_reps
            FROM program_exercises pe
            JOIN exercises e ON pe.exercise_id = e.id
            WHERE pe.program_id = ?;
        """, (program_id,))

        raw_exercises = cursor.fetchall()

        formatted_exercises = [
            {
                "name": row[0],
                "category": row[1],
                "default_sets": row[2],
                "default_reps": row[3]
            }
            for row in raw_exercises
        ]

        return {"status": "success", "exercises": formatted_exercises}

    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Database operational failure: {str(e)}")
    finally:
        conn.close()


@app.post("/submit-log")
@app.post("/submit-log/")
def submit_workout_log(payload: List[LogItem]):
    """Receives array of tracked training inputs and writes them directly into the SQL logs."""
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    try:
        log_entries = [(item.exercise_name, item.set_number, item.weight_lbs, item.reps_performed) for item in payload]
        cursor.executemany("INSERT INTO workout_logs (exercise_name, set_number, weight_lbs, reps_performed) VALUES (?, ?, ?, ?);", log_entries)
        conn.commit()
        return {"status": "success", "message": "Successfully logged session!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()