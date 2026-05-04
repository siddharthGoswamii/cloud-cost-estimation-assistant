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