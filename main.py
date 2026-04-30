from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI()

# This defines what the Developer's frontend will send to you
class ServiceItem(BaseModel):
    service_name: str
    quantity: int

@app.get("/")
def home():
    return {"message": "Cloud Cost Assistant API is Running"}

@app.post("/calculate")
async def calculate_manual_cost(items: List[ServiceItem]):
    # Hardcoded Pricing Master (We will move this to a Database in Week 2)
    # Prices are monthly estimates based on standard 24/7 usage (730 hours)
    prices = {
        "EC2": 30.37, 
        "S3": 2.30, 
        "RDS": 12.41,
        "Lambda": 0.20,
        "ELB": 16.42
    }
    
    total = 0
    breakdown = []
    
    for item in items:
        # Get the price, default to 0 if service is not in our list
        unit_price = prices.get(item.service_name.upper(), 0)
        item_total = unit_price * item.quantity
        total += item_total
        
        breakdown.append({
            "service": item.service_name,
            "unit_price": unit_price,
            "quantity": item.quantity,
            "subtotal": round(item_total, 2)
        })
        
    return {
        "total_monthly_estimate": round(total, 2),
        "currency": "USD",
        "details": breakdown
    }