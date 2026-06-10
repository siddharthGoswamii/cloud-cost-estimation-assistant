"""
Cloud Cost Assistant API
FastAPI application with AWS-style pricing engine
"""

from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, func
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from datetime import datetime
import os

from database import SessionLocal, get_db
from models import (
    Region, Service, ServiceSKU, CalculationHistory,
    ServiceConfiguration, ArchitectureDiagram
)
from service_detector import ServiceDetector, ConversationalAgent
from conversational_cost_agent import ConversationalCostAgent
from pricing_engine import PricingEngine

# Initialize pricing engine ONCE with live pricing enabled
pricing_engine = PricingEngine(use_live_pricing=True)

# Initialize advanced conversational agent with the SAME pricing engine instance
advanced_agent = ConversationalCostAgent(pricing_engine=pricing_engine)

# Keep legacy agents for backward compatibility (if needed)
service_detector = ServiceDetector()
conversational_agent = ConversationalAgent()

# Initialize FastAPI app
app = FastAPI(
    title="Cloud Cost Assistant API",
    description="AWS-style pricing engine for cloud cost estimation",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== STATIC FILES ====================

# Serve HTML files from frontend folder
@app.get("/")
async def read_root():
    """Redirect to agent demo"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", "agent_demo.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    raise HTTPException(status_code=404, detail="Frontend not found")

@app.get("/{file_name}.html")
async def serve_html(file_name: str):
    """Serve HTML files from frontend folder"""
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend", f"{file_name}.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    raise HTTPException(status_code=404, detail="File not found")


# ==================== MIDDLEWARE ====================

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Log request processing time"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    print(f"Request: {request.url.path} | Time: {process_time:.4f}s")
    return response


# ==================== PYDANTIC MODELS ====================

class ServiceCalculationRequest(BaseModel):
    """Request model for single service calculation"""
    service: str = Field(..., description="AWS service code (e.g., EC2, S3, Lambda)")
    config: Dict[str, Any] = Field(..., description="Service configuration parameters")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "EC2",
                "config": {
                    "region": "us-east-1",
                    "instanceType": "t3.medium",
                    "hours": 730,
                    "count": 2
                }
            }
        }


class MultiServiceCalculationRequest(BaseModel):
    """Request model for multiple services calculation"""
    services: List[Dict[str, Any]] = Field(..., description="List of services with configs")
    save_history: Optional[bool] = Field(True, description="Save calculation to history")
    user_id: Optional[str] = Field(None, description="User identifier")
    notes: Optional[str] = Field(None, description="Calculation notes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "services": [
                    {
                        "service": "EC2",
                        "config": {
                            "region": "us-east-1",
                            "instanceType": "t3.medium",
                            "hours": 730,
                            "count": 2
                        }
                    },
                    {
                        "service": "S3",
                        "config": {
                            "region": "us-east-1",
                            "usageGB": 500
                        }
                    }
                ]
            }
        }


class ArchitectureDiagramRequest(BaseModel):
    """Request model for architecture diagram analysis"""
    name: str = Field(..., description="Diagram name")
    description: Optional[str] = Field(None, description="Diagram description")
    services: List[str] = Field(..., description="Detected services from diagram")
    configurations: Dict[str, Dict[str, Any]] = Field(..., description="Service configurations")
    user_id: Optional[str] = Field(None, description="User identifier")


# ==================== ROOT ENDPOINTS ====================

@app.get("/")
def home():
    """API home endpoint"""
    return {
        "message": "Cloud Cost Assistant API v2.0",
        "status": "online",
        "features": [
            "30+ AWS services supported",
            "Multi-region pricing",
            "Tiered pricing models",
            "Architecture diagram analysis",
            "Cost history tracking"
        ],
        "endpoints": {
            "services": "/services",
            "regions": "/regions",
            "calculate": "/calculate",
            "calculate-multiple": "/calculate-multiple",
            "history": "/history",
            "configurations": "/configurations"
        }
    }


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database error: {str(e)}")


# ==================== SERVICE ENDPOINTS ====================

@app.get("/services")
def get_services(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get all available AWS services"""
    query = db.query(Service).filter(Service.active == True)
    
    if category:
        query = query.join(Service.category).filter(
            func.lower(Service.category.name) == category.lower()
        )
    
    services = query.all()
    
    return {
        "count": len(services),
        "services": [
            {
                "code": s.code,
                "name": s.name,
                "description": s.description,
                "category": s.category.name if s.category else None,
                "pricing_model": s.pricing_model
            }
            for s in services
        ]
    }


@app.get("/services/{service_code}")
def get_service_details(service_code: str, db: Session = Depends(get_db)):
    """Get detailed information about a specific service"""
    service = db.query(Service).filter(
        func.upper(Service.code) == service_code.upper()
    ).first()
    
    if not service:
        raise HTTPException(status_code=404, detail=f"Service '{service_code}' not found")
    
    # Get SKUs
    skus = db.query(ServiceSKU).filter(ServiceSKU.service_id == service.id).all()
    
    return {
        "code": service.code,
        "name": service.name,
        "description": service.description,
        "category": service.category.name if service.category else None,
        "pricing_model": service.pricing_model,
        "skus": [
            {
                "code": sku.sku_code,
                "name": sku.name,
                "unit": sku.unit,
                "base_price": sku.base_price
            }
            for sku in skus
        ]
    }


@app.get("/regions")
def get_regions(db: Session = Depends(get_db)):
    """Get all available AWS regions"""
    regions = db.query(Region).filter(Region.active == True).all()
    
    return {
        "count": len(regions),
        "regions": [
            {
                "code": r.code,
                "name": r.name,
                "multiplier": r.multiplier
            }
            for r in regions
        ]
    }


# ==================== CALCULATION ENDPOINTS ====================

@app.post("/calculate")
def calculate_cost(request: ServiceCalculationRequest):
    """Calculate cost for a single service"""
    try:
        result = pricing_engine.calculate(request.service, request.config)
        return {
            "success": True,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/calculate-multiple")
def calculate_multiple_costs(
    request: MultiServiceCalculationRequest,
    db: Session = Depends(get_db)
):
    """Calculate costs for multiple services"""
    try:
        result = pricing_engine.calculate_multiple(request.services)
        
        # Save to history if requested
        if request.save_history:
            history = CalculationHistory(
                user_id=request.user_id,
                total_cost=result["totalCost"],
                currency="USD",
                services_used=request.services,
                breakdown=result,
                notes=request.notes
            )
            db.add(history)
            db.commit()
            result["history_id"] = history.id
        
        return {
            "success": True,
            "result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Calculation error: {str(e)}")


@app.post("/architecture-diagram")
def analyze_architecture_diagram(
    request: ArchitectureDiagramRequest,
    db: Session = Depends(get_db)
):
    """Analyze architecture diagram and calculate costs"""
    try:
        # Build services list for calculation
        services_to_calculate = []
        for service_code in request.services:
            if service_code in request.configurations:
                services_to_calculate.append({
                    "service": service_code,
                    "config": request.configurations[service_code]
                })
        
        # Calculate costs
        result = pricing_engine.calculate_multiple(services_to_calculate)
        
        # Save diagram
        diagram = ArchitectureDiagram(
            name=request.name,
            description=request.description,
            detected_services=request.services,
            user_id=request.user_id
        )
        db.add(diagram)
        
        # Save calculation history
        history = CalculationHistory(
            user_id=request.user_id,
            total_cost=result["totalCost"],
            currency="USD",
            services_used=services_to_calculate,
            breakdown=result,
            notes=f"Architecture: {request.name}"
        )
        db.add(history)
        db.commit()
        
        diagram.calculation_id = history.id
        db.commit()
        
        return {
            "success": True,
            "diagram_id": diagram.id,
            "calculation_id": history.id,
            "result": result
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


# ==================== HISTORY ENDPOINTS ====================

@app.get("/history")
def get_calculation_history(
    limit: int = 50,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Get calculation history"""
    query = db.query(CalculationHistory).order_by(CalculationHistory.timestamp.desc())
    
    if user_id:
        query = query.filter(CalculationHistory.user_id == user_id)
    
    history = query.limit(limit).all()
    
    return {
        "count": len(history),
        "history": [
            {
                "id": h.id,
                "timestamp": h.timestamp.isoformat(),
                "total_cost": h.total_cost,
                "currency": h.currency,
                "services_count": len(h.services_used) if h.services_used else 0,
                "notes": h.notes
            }
            for h in history
        ]
    }


@app.get("/history/{calculation_id}")
def get_calculation_details(calculation_id: int, db: Session = Depends(get_db)):
    """Get detailed calculation history"""
    history = db.query(CalculationHistory).filter(
        CalculationHistory.id == calculation_id
    ).first()
    
    if not history:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    return {
        "id": history.id,
        "timestamp": history.timestamp.isoformat(),
        "total_cost": history.total_cost,
        "currency": history.currency,
        "services_used": history.services_used,
        "breakdown": history.breakdown,
        "notes": history.notes,
        "user_id": history.user_id
    }


@app.delete("/history")
def clear_history(db: Session = Depends(get_db)):
    """Clear all calculation history"""
    try:
        deleted = db.query(CalculationHistory).delete()
        db.commit()
        return {
            "success": True,
            "message": f"Deleted {deleted} calculation records"
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error clearing history: {str(e)}")


# ==================== CONFIGURATION ENDPOINTS ====================

@app.get("/configurations")
def get_service_configurations(
    service: Optional[str] = None,
    popular_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get predefined service configurations"""
    query = db.query(ServiceConfiguration)
    
    if service:
        query = query.join(Service).filter(
            func.upper(Service.code) == service.upper()
        )
    
    if popular_only:
        query = query.filter(ServiceConfiguration.is_popular == True)
    
    configs = query.all()
    
    return {
        "count": len(configs),
        "configurations": [
            {
                "id": c.id,
                "name": c.name,
                "description": c.description,
                "estimated_cost": c.estimated_cost,
                "is_popular": c.is_popular
            }
            for c in configs
        ]
    }


# ==================== LEGACY ENDPOINTS (Backward Compatibility) ====================

class LegacyServiceRequest(BaseModel):
    """Legacy request format"""
    service_name: str
    quantity: int


@app.post("/calculate-legacy")
async def calculate_cost_legacy(
    items: List[LegacyServiceRequest],
    db: Session = Depends(get_db)
):
    """Legacy calculation endpoint for backward compatibility"""
    total_cost = 0
    details = []
    
    for item in items:
        sql_query = text(
            "SELECT service_name, hourly_rate FROM pricing_master "
            "WHERE TRIM(UPPER(service_name)) = TRIM(UPPER(:name))"
        )
        result = db.execute(sql_query, {"name": item.service_name.upper()}).fetchone()
        
        if result:
            name, rate = result
            subtotal = rate * 730 * item.quantity
            total_cost += subtotal
            
            details.append({
                "service": name,
                "monthly_cost": round(subtotal, 2)
            })
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Service {item.service_name} not found"
            )
    
    return {
        "total_monthly_estimate": round(total_cost, 2),
        "details": details
    }


# ==================== STATISTICS ENDPOINTS ====================

@app.get("/stats")


# ==================== AI AGENT ENDPOINTS ====================

class DiagramAnalysisRequest(BaseModel):
    """Request model for diagram analysis"""
    diagram_text: str = Field(..., description="Text description of architecture diagram")
    scale: Optional[str] = Field("small", description="Architecture scale: small, medium, large")
    user_id: Optional[str] = Field(None, description="User identifier")
    
    class Config:
        json_schema_extra = {
            "example": {
                "diagram_text": "Web application with EC2 instances behind a load balancer, RDS database, and S3 for static assets. CloudFront for CDN.",
                "scale": "medium"
            }
        }


class ConfigUpdateRequest(BaseModel):
    """Request model for conversational config updates"""
    service: str = Field(..., description="Service to update")
    current_config: Dict[str, Any] = Field(..., description="Current configuration")
    update_instruction: str = Field(..., description="Natural language update instruction")
    
    class Config:
        json_schema_extra = {
            "example": {
                "service": "EC2",
                "current_config": {
                    "instanceType": "t3.medium",
                    "count": 1,
                    "hours": 730,
                    "region": "us-east-1"
                },
                "update_instruction": "increase to 5 instances and change to t3.large"
            }
        }


@app.post("/analyze-diagram")
def analyze_diagram_text(request: DiagramAnalysisRequest, db: Session = Depends(get_db)):
    """
    AI-powered diagram analysis endpoint
    Automatically detects services and suggests configurations
    """
    try:
        # Parse diagram and detect services
        analysis = service_detector.parse_diagram_components(request.diagram_text)
        
        # Adjust configurations based on scale
        services_with_costs = []
        total_cost = 0
        
        for detected in analysis["detected_services"]:
            service_code = detected["service"]
            base_config = detected["config"]
            
            # Adjust config based on scale
            adjusted_config = service_detector.adjust_config_based_on_scale(
                service_code,
                base_config,
                request.scale
            )
            
            # Calculate cost
            try:
                cost_result = pricing_engine.calculate(service_code, adjusted_config)
                services_with_costs.append({
                    "service": service_code,
                    "confidence": detected["confidence"],
                    "reasoning": detected["reasoning"],
                    "config": adjusted_config,
                    "monthly_cost": cost_result["cost"],
                    "breakdown": cost_result["breakdown"]
                })
                total_cost += cost_result["cost"]
            except Exception as e:
                services_with_costs.append({
                    "service": service_code,
                    "confidence": detected["confidence"],
                    "reasoning": detected["reasoning"],
                    "config": adjusted_config,
                    "error": str(e)
                })
        
        # Save to database
        diagram = ArchitectureDiagram(
            name=f"Auto-detected: {analysis.get('architecture_pattern', 'Unknown')}",
            description=request.diagram_text[:500],
            detected_services=[s["service"] for s in services_with_costs],
            user_id=request.user_id
        )
        db.add(diagram)
        
        history = CalculationHistory(
            user_id=request.user_id,
            total_cost=total_cost,
            currency="USD",
            services_used=[{
                "service": s["service"],
                "config": s["config"]
            } for s in services_with_costs if "error" not in s],
            breakdown={
                "services": services_with_costs,
                "total": total_cost
            },
            notes=f"Auto-detected from diagram: {analysis.get('architecture_pattern', 'Unknown')}"
        )
        db.add(history)
        db.commit()
        
        diagram.calculation_id = history.id
        db.commit()
        
        return {
            "success": True,
            "analysis": {
                "architecture_pattern": analysis["architecture_pattern"],
                "estimated_scale": analysis["estimated_scale"],
                "regions": analysis["regions"],
                "detected_services_count": len(services_with_costs)
            },
            "services": services_with_costs,
            "total_monthly_cost": round(total_cost, 2),
            "diagram_id": diagram.id,
            "calculation_id": history.id,
            "message": "✅ Services automatically detected and costs calculated!"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")


@app.post("/update-config")
def update_configuration_conversational(request: ConfigUpdateRequest):
    """
    Conversational configuration update endpoint
    Allows natural language updates to service configurations
    """
    try:
        # Parse the update instruction
        updated_config = conversational_agent.parse_update_request(
            request.update_instruction,
            request.current_config
        )
        
        # Recalculate cost with new config
        cost_result = pricing_engine.calculate(request.service, updated_config)
        
        # Generate response message
        response_message = conversational_agent.generate_response(
            request.service,
            request.current_config,
            updated_config
        )
        
        return {
            "success": True,
            "message": response_message,
            "updated_config": updated_config,
            "new_cost": cost_result["cost"],
            "cost_breakdown": cost_result["breakdown"],
            "changes_detected": updated_config != request.current_config
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Update error: {str(e)}")


@app.post("/quick-estimate")
def quick_architecture_estimate(
    architecture_type: str = "web_application",
    scale: str = "small",
    region: str = "us-east-1"
):
    """
    Quick ballpark estimate for common architecture patterns
    
    Architecture types:
    - web_application: EC2, ELB, RDS, S3, CloudFront
    - serverless: Lambda, API Gateway, DynamoDB, S3
    - microservices: ECS/EKS, RDS, ElastiCache, SQS
    - data_pipeline: Kinesis, Lambda, S3, Athena
    """
    try:
        # Get typical services for pattern
        typical_services = service_detector.suggest_services_for_pattern(architecture_type)
        
        if not typical_services:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown architecture type: {architecture_type}"
            )
        
        # Build service configurations
        services_to_calculate = []
        for service_code in typical_services:
            if service_code in service_detector.SERVICE_PATTERNS:
                base_config = service_detector.SERVICE_PATTERNS[service_code]["default_config"].copy()
                base_config["region"] = region
                
                # Adjust for scale
                adjusted_config = service_detector.adjust_config_based_on_scale(
                    service_code,
                    base_config,
                    scale
                )
                
                services_to_calculate.append({
                    "service": service_code,
                    "config": adjusted_config
                })
        
        # Calculate costs
        result = pricing_engine.calculate_multiple(services_to_calculate)
        
        return {
            "success": True,
            "architecture_type": architecture_type,
            "scale": scale,
            "region": region,
            "services": result["services"],
            "total_monthly_cost": result["totalCost"],
            "message": f"✅ Quick estimate for {architecture_type} ({scale} scale)"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Estimation error: {str(e)}")


@app.get("/architecture-patterns")
def get_architecture_patterns():
    """Get available architecture patterns for quick estimates"""
    return {
        "patterns": [
            {
                "type": "web_application",
                "name": "Web Application",
                "description": "Traditional web app with load balancer, servers, database, and CDN",
                "typical_services": ["EC2", "ELB", "RDS", "S3", "CloudFront"]
            },
            {
                "type": "serverless",
                "name": "Serverless Architecture",
                "description": "Event-driven serverless application",
                "typical_services": ["Lambda", "API Gateway", "DynamoDB", "S3"]
            },
            {
                "type": "microservices",
                "name": "Microservices",
                "description": "Container-based microservices architecture",
                "typical_services": ["ECS", "EKS", "RDS", "ElastiCache", "SQS"]
            },
            {
                "type": "data_pipeline",
                "name": "Data Pipeline",
                "description": "Real-time data processing pipeline",
                "typical_services": ["Kinesis", "Lambda", "S3", "Athena"]
            }
        ]
    }

def get_statistics(db: Session = Depends(get_db)):
    """Get API statistics"""
    return {
        "total_services": db.query(func.count(Service.id)).scalar(),
        "total_regions": db.query(func.count(Region.id)).scalar(),
        "total_calculations": db.query(func.count(CalculationHistory.id)).scalar(),
        "total_skus": db.query(func.count(ServiceSKU.id)).scalar(),
        "active_services": db.query(func.count(Service.id)).filter(
            Service.active == True
        ).scalar()
    }


# ==================== ADVANCED CONVERSATIONAL AGENT ENDPOINTS ====================

class ConversationalRequest(BaseModel):
    """Request model for conversational agent"""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message or architecture description")
    image_data: Optional[str] = Field(None, description="Base64 encoded image data")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "user_123_session_1",
                "message": "I have a web application with 5 EC2 t3.large instances in us-east-1, RDS MySQL db.t3.large with 500GB storage, and S3 with 2TB of data"
            }
        }


class SessionStateResponse(BaseModel):
    """Response model for session state"""
    session_id: str
    conversation_turn: int
    total_monthly_cost: float
    total_annual_cost: float
    services_count: int


@app.post("/chat")
def conversational_chat(request: ConversationalRequest):
    """
    Advanced conversational endpoint with full session memory
    Maintains context across multiple turns
    """
    try:
        response_text = advanced_agent.process_message(
            session_id=request.session_id,
            user_message=request.message,
            image_data=request.image_data
        )
        
        session = advanced_agent.get_session(request.session_id)
        
        # Build services array for frontend
        services_array = []
        for service in session.services:
            services_array.append({
                "name": service.name,
                "instance_type": service.instance_type,
                "quantity": service.quantity,
                "hours_per_month": int(service.hours_per_day * service.days_per_month),
                "storage_gb": service.storage_gb,
                "unit_price": service.unit_price,
                "monthly_cost": service.monthly_cost,
                "assumptions": service.assumptions
            })
        
        # Debug logging
        print(f"\n=== CHAT RESPONSE DEBUG ===")
        print(f"Session ID: {session.session_id}")
        print(f"Services detected: {len(services_array)}")
        for svc in services_array:
            print(f"  - {svc['name']}: ${svc['monthly_cost']:.2f}/mo (type: {svc['instance_type']}, qty: {svc['quantity']})")
        print(f"Total Monthly Cost: ${session.total_monthly_cost:.2f}")
        print(f"=========================\n")
        
        return {
            "success": True,
            "message": response_text,
            "session_id": session.session_id,
            "turn": session.conversation_turn,
            "region": session.region,
            "cloud_provider": session.cloud_provider,
            "scale": session.scale,
            "services": services_array,
            "total_monthly_cost": round(session.total_monthly_cost, 2),
            "total_annual_cost": round(session.total_annual_cost, 2),
            "services_count": len(services_array)
        }
    except Exception as e:
        print(f"ERROR in /chat: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@app.get("/session/{session_id}")
def get_session_state(session_id: str):
    """Get current session state"""
    session = advanced_agent.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {
        "success": True,
        "session": session.to_dict()
    }


@app.delete("/session/{session_id}")
def clear_session(session_id: str):
    """Clear/reset a session"""
    if session_id in advanced_agent.sessions:
        del advanced_agent.sessions[session_id]
        return {
            "success": True,
            "message": f"Session {session_id} cleared"
        }
    raise HTTPException(status_code=404, detail="Session not found")


@app.get("/sessions")
def list_sessions():
    """List all active sessions"""
    return {
        "success": True,
        "sessions": [
            {
                "session_id": sid,
                "conversation_turn": session.conversation_turn,
                "services_count": len(session.services),
                "total_cost": session.total_monthly_cost,
                "created_at": session.created_at,
                "updated_at": session.updated_at
            }
            for sid, session in advanced_agent.sessions.items()
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# Made with Bob
