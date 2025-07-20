from fastapi import FastAPI, HTTPException, Depends, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel
import asyncpg
import os
import json
from dotenv import load_dotenv
import pandas as pd
from contextlib import asynccontextmanager

# Load environment variables
load_dotenv()

# Models
class AttendanceRecord(BaseModel):
    date: date
    subject: str
    roll_number: str
    timestamp: datetime

class StudentSummary(BaseModel):
    roll_number: str
    attendance: List[dict]

class SubjectAttendance(BaseModel):
    date: date
    subject: str
    attendance: List[dict]

# Database connection pool
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global pool
    pool = await asyncpg.create_pool(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        min_size=1,
        max_size=10
    )
    yield
    # Shutdown
    await pool.close()

app = FastAPI(lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load timetable
try:
    with open("timetable.json", "r") as f:
        TIMETABLE = json.load(f)
except Exception as e:
    raise RuntimeError(f"Failed to load timetable.json: {e}")

@app.get("/subjects/", response_model=dict)
async def get_subjects_for_date(date: date = Query(...)):
    async with pool.acquire() as conn:
        records = await conn.fetch(
            "SELECT DISTINCT subject FROM attendance WHERE date = $1", 
            date
        )
        if not records:
            raise HTTPException(status_code=404, detail="No records found for this date")
        return {
            "date": date,
            "available_subjects": [rec['subject'] for rec in records]
        }

@app.get("/daily_attendance/{date}/{roll}/{subject}", response_model=dict)
async def check_attendance(
    date: date = Path(...),
    roll: str = Path(..., min_length=1),
    subject: str = Path(..., min_length=1)
):
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT timestamp FROM attendance
            WHERE date = $1 AND subject = $2 AND roll_number = $3
            """,
            date, subject, roll
        )
        
        if not records:
            return {"status": "Absent", "times": []}
        
        return {
            "status": "Present",
            "times": [rec['timestamp'].strftime("%H:%M:%S") for rec in records]
        }

@app.get("/student/summary/{roll}", response_model=StudentSummary)
async def get_student_summary(
    roll: str = Path(..., min_length=1),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    async with pool.acquire() as conn:
        query = """
            SELECT date, subject, array_agg(timestamp) as times
            FROM attendance
            WHERE roll_number = $1
            {date_filter}
            GROUP BY date, subject
            ORDER BY date
        """
        
        params = [roll]
        date_filter = ""
        
        if start_date and end_date:
            if start_date > end_date:
                raise HTTPException(status_code=400, detail="Start date must be before end date")
            date_filter = "AND date BETWEEN $2 AND $3"
            params.extend([start_date, end_date])
        elif start_date:
            date_filter = "AND date >= $2"
            params.append(start_date)
        elif end_date:
            date_filter = "AND date <= $2"
            params.append(end_date)
            
        records = await conn.fetch(query.format(date_filter=date_filter), *params)
        
        attendance = []
        for rec in records:
            attendance.append({
                "date": rec['date'],
                "subject": rec['subject'],
                "status": "Present",
                "times": [t.strftime("%H:%M:%S") for t in rec['times']]
            })
        
        return {
            "roll_number": roll,
            "attendance": attendance
        }

@app.get("/attendance/records", response_model=SubjectAttendance)
async def get_subject_attendance(
    date: date = Query(...),
    subject: str = Query(..., min_length=1)
):
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT roll_number, timestamp FROM attendance
            WHERE date = $1 AND subject = $2
            ORDER BY timestamp
            """,
            date, subject
        )
        
        return {
            "date": date,
            "subject": subject,
            "attendance": [
                {
                    "roll_number": rec['roll_number'],
                    "timestamp": rec['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
                }
                for rec in records
            ]
        }

@app.get("/export/records")
async def export_subject_attendance(
    date: date = Query(...),
    subject: str = Query(..., min_length=1)
):
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT roll_number, timestamp FROM attendance
            WHERE date = $1 AND subject = $2
            ORDER BY timestamp
            """,
            date, subject
        )
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found")
        
        # Create DataFrame
        df = pd.DataFrame([dict(rec) for rec in records])
        df['timestamp'] = df['timestamp'].dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Save to Excel
        filename = f"attendance_{date}_{subject}.xlsx"
        df.to_excel(filename, index=False)
        
        return FileResponse(
            filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename
        )

@app.get("/attendance/range", response_model=List[SubjectAttendance])
async def get_attendance_range(
    start_date: date = Query(...),
    end_date: date = Query(...)
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date")
    
    async with pool.acquire() as conn:
        records = await conn.fetch(
            """
            SELECT date, subject, roll_number, timestamp 
            FROM attendance
            WHERE date BETWEEN $1 AND $2
            ORDER BY date, subject, timestamp
            """,
            start_date, end_date
        )
        
        if not records:
            raise HTTPException(status_code=404, detail="No records found in this date range")
        
        # Group by date and subject
        result = {}
        for rec in records:
            date_str = rec['date'].isoformat()
            subject = rec['subject']
            
            if date_str not in result:
                result[date_str] = {}
            if subject not in result[date_str]:
                result[date_str][subject] = []
                
            result[date_str][subject].append({
                "roll_number": rec['roll_number'],
                "timestamp": rec['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
            })
        
        # Convert to response model
        return [
            {
                "date": date.fromisoformat(date_str),
                "subject": subject,
                "attendance": attendance
            }
            for date_str, subjects in result.items()
            for subject, attendance in subjects.items()
        ]