import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# ==========================================
# 1. DATABASE CONFIGURATION & ENVIRONMENT
# ==========================================

# Read DATABASE_URL from Render Environment Variables; default to local SQLite for offline dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./workout_app.db")

# Fix Render PostgreSQL connection string syntax for SQLAlchemy 1.4+
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# SQLite requires extra thread checking flags; PostgreSQL does not
engine_kwargs = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ==========================================
# 2. DATABASE MODELS (SCHEMAS)
# ==========================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    exercise_name = Column(String, nullable=False)
    set_number = Column(Integer, nullable=False)
    weight_lbs = Column(Float, nullable=False)
    reps_performed = Column(Integer, nullable=False)
    log_date = Column(String, nullable=False)  # Stored as YYYY-MM-DD
    timestamp = Column(DateTime, default=datetime.utcnow)


# Automatically create all database tables upon backend startup
Base.metadata.create_all(bind=engine)

# ==========================================
# 3. FASTAPI SETUP & CORS
# ==========================================

app = FastAPI(
    title="Workout Path Architect API",
    description="Backend service providing auth, workout tracking, history, and streak analytics.",
    version="2.0.0"
)

# CORS configuration allowing cross-origin requests from Netlify and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your specific Netlify domain for tighter security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database Session Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ==========================================
# 4. PYDANTIC REQUEST/RESPONSE SCHEMAS
# ==========================================

class AuthPayload(BaseModel):
    username: str
    password: str


class ExerciseSet(BaseModel):
    exercise_name: str
    set_number: int
    weight_lbs: float
    reps_performed: int


class LogWorkoutPayload(BaseModel):
    username: str
    sets: List[ExerciseSet]


# ==========================================
# 5. API ENDPOINTS
# ==========================================

@app.get("/")
def root_check():
    """Health check ping endpoint to keep Render server warm."""
    return {
        "status": "online",
        "message": "Workout Path Architect API is running smoothly!",
        "database": "PostgreSQL" if "postgresql" in DATABASE_URL else "SQLite"
    }


# --- AUTHENTICATION ---

@app.post("/signup")
@app.post("/signup/")
def signup(payload: AuthPayload, db: Session = Depends(get_db)):
    clean_username = payload.username.strip().lower()
    if not clean_username or not payload.password:
        raise HTTPException(status_code=400, detail="Username and password are required.")

    user_exists = db.query(User).filter(User.username == clean_username).first()
    if user_exists:
        raise HTTPException(status_code=400, detail="Username is already taken.")

    # Note: For production security, hash passwords using passlib/bcrypt
    new_user = User(username=clean_username, password_hash=payload.password)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"status": "success", "message": "Account created successfully!", "username": new_user.username}


@app.post("/login")
@app.post("/login/")
def login(payload: AuthPayload, db: Session = Depends(get_db)):
    clean_username = payload.username.strip().lower()
    user = db.query(User).filter(
        User.username == clean_username,
        User.password_hash == payload.password
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password.")

    return {"status": "success", "message": "Login successful!", "username": user.username}


# --- WORKOUT LOGGING & HISTORY ---

@app.post("/log-workout")
@app.post("/log-workout/")
def log_workout(payload: LogWorkoutPayload, db: Session = Depends(get_db)):
    clean_username = payload.username.strip().lower()
    if not payload.sets:
        raise HTTPException(status_code=400, detail="No exercise sets provided to log.")

    today_str = datetime.now().strftime("%Y-%m-%d")

    new_entries = []
    for s in payload.sets:
        entry = WorkoutLog(
            username=clean_username,
            exercise_name=s.exercise_name,
            set_number=s.set_number,
            weight_lbs=s.weight_lbs,
            reps_performed=s.reps_performed,
            log_date=today_str
        )
        new_entries.append(entry)

    db.add_all(new_entries)
    db.commit()

    return {"status": "success", "message": f"Successfully logged {len(new_entries)} set(s)!"}


@app.get("/workout-history/{username}")
@app.get("/workout-history/{username}/")
def get_workout_history(username: str, db: Session = Depends(get_db)):
    clean_username = username.strip().lower()
    logs = db.query(WorkoutLog).filter(
        WorkoutLog.username == clean_username
    ).order_by(WorkoutLog.id.desc()).all()

    return {
        "status": "success",
        "username": clean_username,
        "history": [
            {
                "id": log.id,
                "date": log.log_date,
                "exercise_name": log.exercise_name,
                "set_number": log.set_number,
                "weight_lbs": log.weight_lbs,
                "reps_performed": log.reps_performed
            }
            for log in logs
        ]
    }


# --- STREAK TRACKING ENGINE ---

@app.get("/streak/{username}")
@app.get("/streak/{username}/")
def get_streak(username: str, db: Session = Depends(get_db)):
    clean_username = username.strip().lower()

    # Get distinct dates the user logged a workout, ordered descending
    distinct_dates = db.query(WorkoutLog.log_date).filter(
        WorkoutLog.username == clean_username
    ).distinct().order_by(WorkoutLog.log_date.desc()).all()

    if not distinct_dates:
        return {"status": "success", "username": clean_username, "streak": 0}

    logged_dates = [datetime.strptime(row[0], "%Y-%m-%d").date() for row in distinct_dates]

    today = datetime.now().date()
    yesterday = today - timedelta(days=1)

    # Check if the user has logged a workout today or yesterday to keep streak active
    if logged_dates[0] != today and logged_dates[0] != yesterday:
        return {"status": "success", "username": clean_username, "streak": 0}

    streak = 0
    current_check = logged_dates[0]

    for d in logged_dates:
        if d == current_check:
            streak += 1
            current_check -= timedelta(days=1)
        elif d < current_check:
            break

    return {"status": "success", "username": clean_username, "streak": streak}