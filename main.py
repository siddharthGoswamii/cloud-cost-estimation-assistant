from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session
from database import SessionLocal
from pydantic import BaseModel
from typing import List

app = FastAPI()

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
        sql_query = text("SELECT service_name, hourly_rate FROM pricing_master WHERE service_name = :name")
        result = db.execute(sql_query, {"name": item['service_name'].upper()}).fetchone()
        
        if result:
            name, rate = result
            # Monthly cost = rate * 730 hours * quantity
            subtotal = rate * 730 * item['quantity']
            total_cost += subtotal
            
            details.append({
                "service": name,
                "monthly_cost": round(subtotal, 2)
            })
        else:
            raise HTTPException(status_code=404, detail=f"Service {item['service_name']} not found in SQL")

    return {
        "total_monthly_estimate": round(total_cost, 2),
         "detail" : details
    }