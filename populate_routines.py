'''
Name: Kezia Chacko
Program: populate tables with routines
'''
import sqlite3


def populate_large_dataset():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()

    #Fetch current equipment mappings to match names to database IDs
    cursor.execute("SELECT id, name FROM equipment_options;")
    equipment_mapping = {name: id for id, name in cursor.fetchall()}

    #Master list of comprehensive routines
    #Format: (physique, equipment_id, days_per_week, duration_mins, routine_text)
    comprehensive_routines = [
        # --- BODYBUILDER ROUTINES ---
        (
            "bodybuilder",
            equipment_mapping["full_gym"],
            4,
            60,
            "### 4-Day Full Gym Hypertrophy Split (60 Mins)\n\n"
            "**Day 1: Push (Chest/Shoulders/Triceps)**\n"
            "* Barbell Bench Press: 4 sets x 8-10 reps\n"
            "* Seated Dumbbell Shoulder Press: 3 sets x 10-12 reps\n"
            "* Incline Dumbbell Flyes: 3 sets x 12 reps\n"
            "* Overhead Cable Tricep Extensions: 3 sets x 15 reps\n\n"
            "**Day 2: Pull (Back/Biceps)**\n"
            "* Lat Pulldowns: 4 sets x 8-10 reps\n"
            "* Seated Cable Rows: 3 sets x 10-12 reps\n"
            "* Barbell Bicep Curls: 3 sets x 12 reps\n"
            "* Hammer Curls: 3 sets x 12 reps\n\n"
            "**Day 3: Legs/Abs**\n"
            "* Barbell Back Squats: 4 sets x 8-10 reps\n"
            "* Romanian Deadlifts (RDLs): 3 sets x 10 reps\n"
            "* Leg Press: 3 sets x 12-15 reps\n"
            "* Hanging Leg Raises: 3 sets x Max reps\n\n"
            "**Day 4: Arms & Weak Points Focus**\n"
            "* Close-Grip Bench Press: 3 sets x 10 reps\n"
            "* Preacher Curls: 3 sets x 12 reps\n"
            "* Lateral Raises: 4 sets x 15 reps"
        ),
        (
            "bodybuilder",
            equipment_mapping["dumbbells_only"],
            3,
            60,
            "### 3-Day Dumbbell Full Body Sculpt (60 Mins)\n\n"
            "**Day 1: Full Body A**\n"
            "* DB Goblet Squats: 4 sets x 10-12 reps\n"
            "* DB Flat Bench Press: 4 sets x 10 reps\n"
            "* DB One-Arm Rows: 3 sets x 12 reps/side\n"
            "* DB Lying Hammer Curls: 3 sets x 12 reps\n\n"
            "**Day 2: Full Body B**\n"
            "* DB Romanian Deadlifts: 4 sets x 12 reps\n"
            "* Seated DB Shoulder Press: 3 sets x 10 reps\n"
            "* DB Floor Chest Flyes: 3 sets x 12 reps\n"
            "* DB Overhead Tricep Extension: 3 sets x 12 reps\n\n"
            "**Day 3: Full Body C**\n"
            "* DB Bulgarian Split Squats: 3 sets x 10 reps/leg\n"
            "* DB Incline Bench Press: 3 sets x 12 reps\n"
            "* DB Chest-Supported Rows: 4 sets x 10 reps\n"
            "* DB Lateral Raises: 4 sets x 15 reps"
        ),
        (
            "bodybuilder",
            equipment_mapping["bodyweight_only"],
            4,
            30,
            "### 4-Day Bodyweight Callisthenic Mass (30 Mins)\n\n"
            "*Perform as a high-density circuit. Minimize rest between exercises to max out time.*\n\n"
            "**Days 1 & 3: Upper Body Intensity**\n"
            "* Decline Push-ups (Feet elevated): 4 sets x 12-15 reps\n"
            "* Inverted Bodyweight Rows (using a sturdy table or low bar): 4 sets x 10-12 reps\n"
            "* Pike Push-ups (Shoulder focus): 3 sets x 8-10 reps\n"
            "* Bench Dips: 3 sets x 15 reps\n\n"
            "**Days 2 & 4: Lower Body & Core Burn**\n"
            "* Prisoner Squats (Hands behind head): 4 sets x 20 reps\n"
            "* Walking Lunges: 3 sets x 15 steps per leg\n"
            "* Single-Leg Glute Bridges: 3 sets x 12 reps/leg\n"
            "* Hollow Body Hold: 3 sets x 45-second hold"
        ),

        # --- ATHLETE ROUTINES ---
        (
            "athlete",
            equipment_mapping["full_gym"],
            3,
            60,
            "### 3-Day Power, Speed & Agility Program (60 Mins)\n\n"
            "**Day 1: Power & Explosiveness**\n"
            "* Medicine Ball Slams: 3 sets x 5 reps (Max Effort)\n"
            "* Hang Cleans: 4 sets x 4 reps\n"
            "* Trap Bar Deadlifts: 4 sets x 5 reps (Focusing on bar speed)\n"
            "* Box Jumps: 3 sets x 5 reps\n\n"
            "**Day 2: Strength & Trunk Stability**\n"
            "* Front Squats: 4 sets x 6 reps\n"
            "* Overhead Press: 3 sets x 6 reps\n"
            "* Pull-ups (Weighted if possible): 4 sets x 6-8 reps\n"
            "* Pallof Press (Cable Core Rotation): 3 sets x 12 reps/side\n\n"
            "**Day 3: Unilateral & Conditioning**\n"
            "* Barbell Reverse Lunges: 3 sets x 8 reps/leg\n"
            "* Dumbbell Incline Bench Press: 3 sets x 8 reps\n"
            "* Face Pulls: 3 sets x 15 reps\n"
            "* Rowing Machine Sprint Intervals: 5 rounds of 30s sprint / 30s easy rest"
        ),
        (
            "athlete",
            equipment_mapping["dumbbells_only"],
            3,
            30,
            "### 3-Day Athletic Conditioning Circuit (30 Mins)\n\n"
            "*Perform exercises back-to-back with 30 seconds of rest between movements. Run through 4 full rounds.*\n\n"
            "**The Routine (Perform Days 1, 3, and 5):**\n"
            "1. DB Thrusters (Squat to Overhead Press): 45 seconds work\n"
            "2. DB Renegade Rows (Push-up to row alternate): 45 seconds work\n"
            "3. Dumbbell Suitcase Deadlifts: 45 seconds work\n"
            "4. DB Alternate Reverse Lunges: 45 seconds work\n"
            "5. High Knees (Cardio Burst): 45 seconds work\n"
            "*Rest 2 full minutes at the end of each round.*"
        ),

        # --- STRONGMAN ROUTINES ---
        (
            "strongman",
            equipment_mapping["full_gym"],
            4,
            90,
            "### 4-Day Brutal Strength & Carry Split (90 Mins)\n\n"
            "**Day 1: Overhead Press & Shoulders**\n"
            "* Push Press: Warm up, then 5 sets x 3 reps (Heavy)\n"
            "* Seated Barbell Overhead Press: 3 sets x 6 reps\n"
            "* Dumbbell Z-Press (Seated on floor): 3 sets x 8 reps\n"
            "* Farmer's Walks: 4 runs x 40 meters (Heavy load)\n\n"
            "**Day 2: Squat Strength & Core**\n"
            "* Barbell Back Squats: 5 sets x 5 reps\n"
            "* Safety Bar Squats or Front Squats: 3 sets x 6 reps\n"
            "* Heavy Dumbbell Shrugs: 3 sets x 12 reps\n"
            "* Sandbag or Heavy Plate Carries: 3 runs x 50 meters\n\n"
            "**Day 3: Deadlift & Posterior Chain**\n"
            "* Conventional Deadlift: 5 sets x 3 reps\n"
            "* Deficit Deadlifts (Standing on a 2-inch block): 3 sets x 5 reps\n"
            "* Barbell Good Mornings: 3 sets x 8 reps\n"
            "* Kroc Rows (Ultra heavy single-arm rows): 2 sets x 20 reps\n\n"
            "**Day 4: Loading & Conditioning**\n"
            "* Tire Flips or Heavy Sled Pushes: 5 rounds x 30 meters\n"
            "* Kettlebell Swings (Heavy): 4 sets x 15 reps\n"
            "* Plank Holds with plate on back: 3 sets x 60 seconds"
        ),
        (
            "strongman",
            equipment_mapping["dumbbells_only"],
            3,
            60,
            "### 3-Day Heavy Dumbbell Power & Grip Program (60 Mins)\n\n"
            "**Day 1: Posterior & Grip Focus**\n"
            "* DB Romanian Deadlifts (Heavy): 4 sets x 8 reps\n"
            "* DB Suitcase Carries (One side heavy carry): 4 runs x 30 meters/side\n"
            "* Heavy DB Rows (Strict form): 4 sets x 8 reps\n"
            "* Dumbbell Wrist Curls: 3 sets x 15 reps\n\n"
            "**Day 2: Pressing Power**\n"
            "* DB Clean and Press (Floor to overhead): 5 sets x 5 reps\n"
            "* DB Floor Press (Tricep and lockout strength): 4 sets x 8 reps\n"
            "* DB Single-Arm Overhead Press: 3 sets x 8 reps/side\n"
            "* DB Standing Hammer Curls: 3 sets x 10 reps\n\n"
            "**Day 3: Lower Body Power**\n"
            "* DB Goblet Squats (Pause 2 seconds at bottom): 4 sets x 8 reps\n"
            "* DB Bulgarian Split Squats: 3 sets x 8 reps/leg\n"
            "* DB Farmer's Hold (Stand still with heaviest weights possible): 3 sets x Max time hold"
        )
    ]

    #Insert the dataset cleanly
    cursor.execute("DELETE FROM programs;")
    cursor.executemany("""
        INSERT INTO programs (physique, equipment_id, days_per_week, duration_mins, routine_text)
        VALUES (?, ?, ?, ?, ?);
    """, comprehensive_routines)

    conn.commit()
    conn.close()
    print(f"Success! Populated database with {len(comprehensive_routines)} full workout programs.")


if __name__ == "__main__":
    populate_large_dataset()