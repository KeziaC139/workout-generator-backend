import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class NewWorkout(BaseModel):
    physique: str
    equipment_name: str  # e.g., "full_gym", "dumbbells_only"
    days_per_week: int
    duration_mins: int
    routine_text: str

class UserPreferences(BaseModel):
    physique: str
    equipment: str
    days_per_week: int
    duration_mins: int


@app.post("/recommend-workout")
def get_workout(prefs: UserPreferences):
    #Connect to new SQL database
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    #Write the SQL Query using a JOIN to link the tables together
    #The '?' marks are placeholders to safely insert user data (prevents hacking/SQL injection)
    query = """
        SELECT programs.routine_text 
        FROM programs
        JOIN equipment_options ON programs.equipment_id = equipment_options.id
        WHERE LOWER(programs.physique) = ? 
          AND LOWER(equipment_options.name) = ?
          AND programs.days_per_week = ?
          AND programs.duration_mins = ?
    """

    #Execute the query with the user's inputs
    cursor.execute(query, (
        prefs.physique.lower(),
        prefs.equipment.lower(),
        prefs.days_per_week,
        prefs.duration_mins
    ))

    #Fetch the row result
    result = cursor.fetchone()

    #Always close the database connection when done
    conn.close()

    #Handle whether we found a routine or not
    if result:
        # result is a tuple, e.g., ("Workout details...",), so we grab index 0
        return {"status": "success", "routine": result[0]}
    else:
        raise HTTPException(
            status_code=404,
            detail="No workout program matches your exact criteria in our database yet!"
        )


@app.post("/admin/add-workout")
def add_workout_via_api(workout: NewWorkout):
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    # Check if the requested equipment type actually exists in equipment table
    cursor.execute("SELECT id FROM equipment_options WHERE name = ?;", (workout.equipment_name.lower(),))
    equipment_row = cursor.fetchone()

    if not equipment_row:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail=f"Equipment '{workout.equipment_name}' is invalid. Choose full_gym, dumbbells_only, or bodyweight_only."
        )

    equipment_id = equipment_row[0]

    #Insert the new routine into the programs table
    try:
        cursor.execute("""
            INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins, routine_text)
            VALUES (?, ?, ?, ?, ?);
        """, (
            workout.physique.lower(),
            equipment_id,
            workout.days_per_week,
            workout.duration_mins,
            workout.routine_text
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    conn.close()
    return {"status": "success", "message": "New workout routine successfully saved to database."}