from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic import BaseModel
from typing import List
import time
from fastapi import Request

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE)
    allow_headers=["*"],  # Allows all headers
)

#LOGGING API HITS
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    # This logs the time taken for every SQL query/API call in your terminal
    print(f"Request: {request.url.path} | Time: {process_time:.4f}s")
    return response

#GLOBAL ERROR HANDLING 
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import JSONResponse

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=500,
        content={"message": "Database is acting up, bhai! Please check your Postgres connection."},
    )

# Database connection helper
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class ServiceRequest(BaseModel):
    service_name: str
    quantity: int

@app.get("/")
def home():
    return {"message": "Pure SQL Cloud API is Live"}

@app.post("/calculate")
async def calculate_cost(items: List[ServiceRequest], db: Session = Depends(get_db)):
    total_cost = 0
    details = []
    
    for item in items:
        # ASLI SQL QUERY YAHA HAI!
        sql_query = text("SELECT service_name, hourly_rate FROM pricing_master WHERE TRIM(UPPER(service_name)) = TRIM(UPPER(:name))")
        
        # CHANGE HERE: item['service_name'] ko item.service_name kar diya
        result = db.execute(sql_query, {"name": item.service_name.upper()}).fetchone()
        
        if result:
            name, rate = result
            # CHANGE HERE: item['quantity'] ko item.quantity kar diya
            subtotal = rate * 730 * item.quantity
            total_cost += subtotal

            # SAVING HISTORY
            sql_insert = text("""
                INSERT INTO calculation_history (service_name, quantity, total_cost) 
                VALUES (:name, :qty, :cost)
            """)
            db.execute(sql_insert, {"name": name, "qty": item.quantity, "cost": subtotal})
            
            details.append({
                "service": name,
                "monthly_cost": round(subtotal, 2)
            })
        else:
            raise HTTPException(status_code=404, detail=f"Service {item.service_name} not found")
    
    db.commit()

    return {
        "total_monthly_estimate": round(total_cost, 2),
        "details": details
    }

@app.get("/history")
def get_history(db: Session = Depends(get_db)):
    # Saari history nikalne ki SQL query
    query = text("SELECT * FROM calculation_history ORDER BY timestamp DESC")
    results = db.execute(query).fetchall()
    
    # Result ko readable format mein convert karo
    history_list = []
    for row in results:
        history_list.append({
            "id": row[0],
            "time": row[1],
            "service": row[2],
            "qty": row[3],
            "cost": row[4]
        })
    return {"usage_history": history_list}

# 1. Schema for Updating Price
class PriceUpdate(BaseModel):
    service_name: str
    new_rate: float

# 2. Update Endpoint
@app.put("/update-price")
async def update_service_price(data: PriceUpdate, db: Session = Depends(get_db)):
    # SQL UPDATE Query
    query = text("UPDATE pricing_master SET hourly_rate = :rate WHERE service_name = :name")
    result = db.execute(query, {"rate": data.new_rate, "name": data.service_name.upper()})
    
    db.commit() # Save the changes
    
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Service not found in Database")
        
    return {"message": f"Price for {data.service_name} updated to {data.new_rate}"}

#ADDING NEW SERVICE
class NewService(BaseModel):
    service_name: str
    instance_type: str
    hourly_rate: float

@app.delete("/clear-history")
async def clear_calculation_history(db: Session = Depends(get_db)):
    query = text("DELETE FROM calculation_history")
    db.execute(query)
    db.commit()
    return {"message": "History has been cleared"}