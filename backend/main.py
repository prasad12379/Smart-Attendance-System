from fastapi import FastAPI, Path, HTTPException
from fastapi.middleware.cors import CORSMiddleware  
import json

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)




def load_data():
    print("📥 Trying to load JSON file...")  
    with open('daily_attendance.json', 'r') as f:
        data = json.load(f)
    print("✅ JSON Loaded Successfully!")    
    return data
    

@app.get("/")
def hello():
    return{'message':'Welcome in Advance AI Integrated Attendance Management System.'}


@app.get('/about')
def about():
    return{ 'message':'A Smart Attendance system.'}

@app.get('/view')
def view():
    data=load_data()
    return data


@app.get('/daily_attendance/{date}')
def view_patient(date:str=Path(...,description='Enter Date',example='2025-07-02')):
   
    data=load_data()

    if date in data:
        return data[date]
    raise HTTPException(status_code=404, detail='Date not found.')

@app.get('/daily_attendance/{date}/{roll}')
def check_total_attendance(
    date: str = Path(..., description="Enter Date", examples={"example1": {"value": "2025-07-02"}}),
    roll: str = Path(..., description="Enter RollNo", examples={"example1": {"value": "2114"}})
):
    data = load_data()

    if date not in data:
        raise HTTPException(status_code=404, detail="Date not found.")

    for student in data[date]:
        
        if str(student.get("Roll Number")) == str(roll):
            return {
                "status": "Present",
                "entry_time": student.get("Time")
            }

    return {"status": "Absent"}

@app.get('/daily_attendance_/{roll}')
def check_attendance(
    roll: str = Path(..., description="Enter RollNo", examples={"example1": {"value": "2114"}})
):
    data = load_data()
    
    cnt=0
    dates=""
    for date in data:
        for student in data[date]:
            if (student.get("Roll Number")) == str(roll):
                cnt+=1
                dates=dates+" , "+date
                
            
    return {
        "Toatal present Day" : cnt ,
        "Dates" : dates
        
        }
        
        

    