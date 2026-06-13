'''
Name: Kezia Chacko
Program: sqLite3 DB setup
'''


import sqlite3

def init_database():
    conn = sqlite3.connect("workout_app.db")
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")

    #Create the tables
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
            routine_text TEXT NOT NULL,
            FOREIGN KEY (equipment_id) REFERENCES equipment_options(id)
        );
    """)

    #ONLY insert the equipment options
    equipment_data = [("full_gym",), ("dumbbells_only",), ("bodyweight_only",)]
    cursor.executemany("INSERT OR IGNORE INTO equipment_options (name) VALUES (?);", equipment_data)

    conn.commit()
    conn.close()
    print("Database structure initialized cleanly!")

if __name__ == "__main__":
    init_database()