"""
Database Models for AWS-Style Pricing System
SQLAlchemy ORM models for regions, services, pricing, and calculation history
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Region(Base):
    """AWS Regions with pricing multipliers"""
    __tablename__ = "regions"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., us-east-1
    name = Column(String(100), nullable=False)  # e.g., N. Virginia
    multiplier = Column(Float, default=1.0)  # Regional pricing multiplier
    active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<Region {self.code}: {self.name}>"


class ServiceCategory(Base):
    """Service categories (Compute, Storage, Database, etc.)"""
    __tablename__ = "service_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)  # e.g., Compute
    description = Column(Text)
    
    services = relationship("Service", back_populates="category")
    
    def __repr__(self):
        return f"<Category {self.name}>"


class Service(Base):
    """AWS Services (EC2, S3, Lambda, etc.)"""
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)  # e.g., EC2
    name = Column(String(100), nullable=False)  # e.g., Elastic Compute Cloud
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("service_categories.id"))
    pricing_model = Column(String(50), nullable=False)  # hourly, tiered_gb, request_based, hybrid, flat_monthly
    active = Column(Boolean, default=True)
    
    # JSON field for service-specific configuration
    config = Column(JSON)  # Stores tiers, rates, instance types, etc.
    
    category = relationship("ServiceCategory", back_populates="services")
    skus = relationship("ServiceSKU", back_populates="service")
    
    def __repr__(self):
        return f"<Service {self.code}: {self.name}>"


class ServiceSKU(Base):
    """
    Service SKUs (Stock Keeping Units) - Individual pricing items
    Examples: EC2 t3.medium, S3 Standard Storage, Lambda requests
    """
    __tablename__ = "service_skus"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    sku_code = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)  # e.g., t3.medium, Standard Storage
    description = Column(Text)
    
    # Pricing details
    unit = Column(String(50))  # hour, GB, request, GB-second
    base_price = Column(Float, nullable=False)  # Base price in us-east-1
    
    # JSON field for SKU-specific attributes
    attributes = Column(JSON)  # Instance specs, storage class, etc.
    
    service = relationship("Service", back_populates="skus")
    
    def __repr__(self):
        return f"<SKU {self.sku_code}: {self.name}>"


class PricingTier(Base):
    """
    Tiered pricing rules (for S3, data transfer, etc.)
    """
    __tablename__ = "pricing_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    tier_name = Column(String(100))  # e.g., "First 50 TB"
    from_value = Column(Float, nullable=False)  # Start of tier (e.g., 0)
    to_value = Column(Float)  # End of tier (NULL for unlimited)
    price = Column(Float, nullable=False)  # Price per unit in this tier
    unit = Column(String(50))  # GB, TB, requests
    
    def __repr__(self):
        return f"<Tier {self.tier_name}: {self.from_value}-{self.to_value}>"


class CalculationHistory(Base):
    """
    History of cost calculations performed
    """
    __tablename__ = "calculation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # User/session info (optional)
    user_id = Column(String(100))
    session_id = Column(String(100))
    
    # Calculation details
    total_cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    
    # JSON field for full calculation breakdown
    services_used = Column(JSON)  # List of services and their configs
    breakdown = Column(JSON)  # Detailed cost breakdown
    
    # Metadata
    region = Column(String(50))
    notes = Column(Text)
    
    def __repr__(self):
        return f"<Calculation {self.id}: ${self.total_cost} at {self.timestamp}>"


class ArchitectureDiagram(Base):
    """
    Store architecture diagrams and their detected services
    """
    __tablename__ = "architecture_diagrams"
    
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Diagram info
    name = Column(String(200))
    description = Column(Text)
    diagram_url = Column(String(500))  # URL or path to diagram image
    
    # Detected services (JSON)
    detected_services = Column(JSON)  # List of auto-detected services
    
    # Associated calculation
    calculation_id = Column(Integer, ForeignKey("calculation_history.id"))
    
    # User info
    user_id = Column(String(100))
    
    def __repr__(self):
        return f"<Diagram {self.id}: {self.name}>"


class ServiceConfiguration(Base):
    """
    Predefined service configurations for quick estimates
    """
    __tablename__ = "service_configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    
    name = Column(String(200), nullable=False)  # e.g., "Small Web App", "Large Database"
    description = Column(Text)
    
    # Configuration as JSON
    config = Column(JSON, nullable=False)  # Instance type, storage, etc.
    
    # Estimated monthly cost
    estimated_cost = Column(Float)
    
    # Usage pattern
    is_template = Column(Boolean, default=False)
    is_popular = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Config {self.name}: ${self.estimated_cost}/mo>"


class CostAlert(Base):
    """
    Cost alerts and thresholds
    """
    __tablename__ = "cost_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=False)
    
    alert_name = Column(String(200), nullable=False)
    threshold = Column(Float, nullable=False)  # Alert when cost exceeds this
    
    # Alert configuration
    services = Column(JSON)  # Which services to monitor
    region = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    last_triggered = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<Alert {self.alert_name}: ${self.threshold}>"


# Legacy model for backward compatibility
class CloudService(Base):
    """Legacy model - kept for backward compatibility"""
    __tablename__ = "cloud_services_legacy"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)
    default_config = Column(String(100))
    hourly_rate = Column(Float)
    
    def __repr__(self):
        return f"<CloudService {self.name}>"

# Made with Bob
