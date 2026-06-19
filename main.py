import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- PYDANTIC SCHEMAS (Data Structures) ---

class UserPreferences(BaseModel):
    physique: str
    equipment: str
    days_per_week: int
    duration_mins: int


class LogSet(BaseModel):
    exercise_name: str
    set_number: int
    weight_lbs: Optional[float] = None
    reps_performed: Optional[int] = None


# --- ENDPOINTS ---

#Fetch a modular workout program based on preferences
@app.post("/recommend-workout")
def get_workout(prefs: UserPreferences):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    #First, find the matching program ID
    program_query = """
        SELECT programs.id 
        FROM programs
        JOIN equipment_options ON programs.equipment_id = equipment_options.id
        WHERE LOWER(programs.physique) = ? 
          AND LOWER(equipment_options.name) = ?
          AND programs.days_per_week = ?
          AND programs.duration_mins = ?
    """
    cursor.execute(program_query, (
        prefs.physique.lower(),
        prefs.equipment.lower(),
        prefs.days_per_week,
        prefs.duration_mins
    ))

    program_row = cursor.fetchone()

    if not program_row:
        conn.close()
        raise HTTPException(status_code=404, detail="No matching template found.")

    program_id = program_row[0]

    #Now, fetch all individual exercises linked to that program ID
    exercise_query = """
        SELECT exercises.name, exercises.category, program_exercises.default_sets, program_exercises.default_reps
        FROM program_exercises
        JOIN exercises ON program_exercises.exercise_id = exercises.id
        WHERE program_exercises.program_id = ?
    """
    cursor.execute(exercise_query, (program_id,))
    rows = cursor.fetchall()
    conn.close()

    #Format the rows cleanly into a list of structured objects
    workout_exercises = []
    for row in rows:
        workout_exercises.append({
            "name": row[0],
            "category": row[1],
            "default_sets": row[2],
            "default_reps": row[3]
        })

    return {"status": "success", "program_id": program_id, "exercises": workout_exercises}


#Get all master exercises (for the "Swap/Mix-and-Match" feature)
@app.get("/exercises")
def get_all_exercises():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    cursor.execute("SELECT name, category FROM exercises;")
    rows = cursor.fetchall()
    conn.close()

    return [{"name": r[0], "category": r[1]} for r in rows]


#Save a user's completed workout logs to the database
@app.post("/submit-log")
def submit_workout_log(logs: List[LogSet]):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    try:
        #Loop through each set logged by the user and insert it
        for entry in logs:
            cursor.execute("""
                INSERT INTO workout_logs (exercise_name, set_number, weight_lbs, reps_performed)
                VALUES (?, ?, ?, ?);
            """, (entry.exercise_name, entry.set_number, entry.weight_lbs, entry.reps_performed))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Failed to log workout: {str(e)}")

    conn.close()
    return {"status": "success", "message": "Workout tracked successfully!"}