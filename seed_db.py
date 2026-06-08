"""
Database Seeding Script
Populates the database with AWS regions, services, and pricing data
"""

from sqlalchemy.orm import Session
from database import engine, SessionLocal, init_db
from models import (
    Region, ServiceCategory, Service, ServiceSKU, 
    PricingTier, ServiceConfiguration
)
from pricing_database import REGIONS, PRICING_DB, SERVICE_CATEGORIES
import json


def seed_regions(db: Session):
    """Seed AWS regions"""
    print("Seeding regions...")
    
    for code, data in REGIONS.items():
        region = Region(
            code=code,
            name=data["name"],
            multiplier=data["multiplier"],
            active=True
        )
        db.add(region)
    
    db.commit()
    print(f"Added {len(REGIONS)} regions")


def seed_categories(db: Session):
    """Seed service categories"""
    print("Seeding service categories...")
    
    categories = {
        "Compute": "Virtual servers, containers, and serverless compute",
        "Storage": "Object, block, and file storage services",
        "Database": "Relational, NoSQL, and in-memory databases",
        "Networking": "CDN, load balancing, and network services",
        "Messaging": "Queue, notification, and event services",
        "Monitoring": "Logging, metrics, and observability",
        "Security": "Identity, encryption, and access management",
        "Management": "Operations and automation tools",
        "Analytics": "Data processing and analytics services",
        "Machine Learning": "AI and ML services"
    }
    
    for name, description in categories.items():
        category = ServiceCategory(
            name=name,
            description=description
        )
        db.add(category)
    
    db.commit()
    print(f"Added {len(categories)} categories")


def seed_services(db: Session):
    """Seed AWS services with pricing data"""
    print("Seeding services...")
    
    # Get category mappings
    categories = {cat.name: cat.id for cat in db.query(ServiceCategory).all()}
    
    service_count = 0
    sku_count = 0
    tier_count = 0
    
    for service_code, service_data in PRICING_DB.items():
        # Determine category
        category_name = service_data.get("category", "Compute")
        category_id = categories.get(category_name)
        
        # Create service
        service = Service(
            code=service_code,
            name=service_data.get("service", service_code),
            description=service_data.get("description", ""),
            category_id=category_id,
            pricing_model=service_data.get("model", "hourly"),
            active=True,
            config=json.dumps(service_data)  # Store full config as JSON
        )
        db.add(service)
        db.flush()  # Get the service ID
        
        service_count += 1
        
        # Create SKUs based on service type
        if service_data.get("model") == "hourly":
            # Handle hourly services (EC2, RDS, etc.)
            if "regions" in service_data and "*" in service_data["regions"]:
                for instance_type, rate in service_data["regions"]["*"].items():
                    sku = ServiceSKU(
                        service_id=service.id,
                        sku_code=f"{service_code}-{instance_type}",
                        name=instance_type,
                        description=f"{service_code} {instance_type} instance",
                        unit="hour",
                        base_price=rate,
                        attributes=json.dumps({"instanceType": instance_type})
                    )
                    db.add(sku)
                    sku_count += 1
            
            elif "instanceRates" in service_data:
                for instance_type, rate in service_data["instanceRates"].items():
                    sku = ServiceSKU(
                        service_id=service.id,
                        sku_code=f"{service_code}-{instance_type}",
                        name=instance_type,
                        description=f"{service_code} {instance_type} instance",
                        unit="hour",
                        base_price=rate,
                        attributes=json.dumps({"instanceType": instance_type})
                    )
                    db.add(sku)
                    sku_count += 1
            
            elif "nodeRates" in service_data:
                for node_type, rate in service_data["nodeRates"].items():
                    sku = ServiceSKU(
                        service_id=service.id,
                        sku_code=f"{service_code}-{node_type}",
                        name=node_type,
                        description=f"{service_code} {node_type} node",
                        unit="hour",
                        base_price=rate,
                        attributes=json.dumps({"nodeType": node_type})
                    )
                    db.add(sku)
                    sku_count += 1
        
        elif service_data.get("model") == "tiered_gb":
            # Handle tiered storage (S3, EBS, EFS)
            if "tiers" in service_data:
                for idx, tier in enumerate(service_data["tiers"]):
                    tier_obj = PricingTier(
                        service_id=service.id,
                        tier_name=f"Tier {idx + 1}",
                        from_value=tier["from"],
                        to_value=tier["to"],
                        price=tier["price"],
                        unit="GB"
                    )
                    db.add(tier_obj)
                    tier_count += 1
                
                # Create a general SKU
                sku = ServiceSKU(
                    service_id=service.id,
                    sku_code=f"{service_code}-storage",
                    name="Storage",
                    description=f"{service_code} tiered storage",
                    unit="GB",
                    base_price=service_data["tiers"][0]["price"],
                    attributes=json.dumps({"type": "tiered"})
                )
                db.add(sku)
                sku_count += 1
            
            elif "volumeTypes" in service_data:
                for vol_type, rate in service_data["volumeTypes"].items():
                    sku = ServiceSKU(
                        service_id=service.id,
                        sku_code=f"{service_code}-{vol_type}",
                        name=vol_type,
                        description=f"{service_code} {vol_type} volume",
                        unit="GB",
                        base_price=rate,
                        attributes=json.dumps({"volumeType": vol_type})
                    )
                    db.add(sku)
                    sku_count += 1
        
        elif service_data.get("model") in ["request_based", "hybrid"]:
            # Create SKU for request-based services
            sku = ServiceSKU(
                service_id=service.id,
                sku_code=f"{service_code}-requests",
                name="Requests",
                description=f"{service_code} requests",
                unit="request",
                base_price=service_data.get("pricePerMillion", 
                           service_data.get("pricePerMillionRequests", 
                           service_data.get("requestCostPerMillion", 0))),
                attributes=json.dumps({"type": "request_based"})
            )
            db.add(sku)
            sku_count += 1
    
    db.commit()
    print(f"Added {service_count} services")
    print(f"Added {sku_count} SKUs")
    print(f"Added {tier_count} pricing tiers")


def seed_configurations(db: Session):
    """Seed common service configurations"""
    print("Seeding service configurations...")
    
    # Get service IDs
    services = {s.code: s.id for s in db.query(Service).all()}
    
    configurations = [
        {
            "service": "EC2",
            "name": "Small Web Server",
            "description": "Single t3.small instance for small websites",
            "config": {
                "instanceType": "t3.small",
                "hours": 730,
                "count": 1,
                "region": "us-east-1"
            },
            "estimated_cost": 15.18
        },
        {
            "service": "EC2",
            "name": "Medium Application Server",
            "description": "t3.medium instance for medium workloads",
            "config": {
                "instanceType": "t3.medium",
                "hours": 730,
                "count": 1,
                "region": "us-east-1"
            },
            "estimated_cost": 30.37
        },
        {
            "service": "RDS",
            "name": "Small Database",
            "description": "db.t3.micro for development/testing",
            "config": {
                "instanceType": "db.t3.micro",
                "hours": 730,
                "storageGB": 20,
                "region": "us-east-1"
            },
            "estimated_cost": 14.71
        },
        {
            "service": "S3",
            "name": "Small Storage",
            "description": "100 GB standard storage",
            "config": {
                "usageGB": 100,
                "region": "us-east-1"
            },
            "estimated_cost": 2.25
        },
        {
            "service": "Lambda",
            "name": "Light Serverless",
            "description": "1M requests, 128MB memory",
            "config": {
                "requests": 1000000,
                "gbSeconds": 12800,
                "region": "us-east-1"
            },
            "estimated_cost": 0.41
        }
    ]
    
    for config_data in configurations:
        service_code = config_data["service"]
        if service_code in services:
            config = ServiceConfiguration(
                service_id=services[service_code],
                name=config_data["name"],
                description=config_data["description"],
                config=json.dumps(config_data["config"]),
                estimated_cost=config_data["estimated_cost"],
                is_template=True,
                is_popular=True
            )
            db.add(config)
    
    db.commit()
    print(f"Added {len(configurations)} service configurations")


def seed_legacy_data(db: Session):
    """Seed legacy pricing_master table for backward compatibility"""
    print("Seeding legacy pricing_master table...")
    
    from sqlalchemy import text
    
    # Drop and recreate legacy table
    db.execute(text("DROP TABLE IF EXISTS pricing_master"))
    db.execute(text("""
        CREATE TABLE pricing_master (
            id SERIAL PRIMARY KEY,
            service_name TEXT NOT NULL,
            instance_type TEXT,
            hourly_rate REAL NOT NULL
        )
    """))
    
    # Add some legacy data
    legacy_services = [
        ("EC2", "t3.micro", 0.0104),
        ("EC2", "t3.small", 0.0208),
        ("EC2", "t3.medium", 0.0416),
        ("EC2", "t3.large", 0.0832),
        ("S3", "Standard Storage", 0.023),
        ("RDS", "db.t3.micro", 0.017),
        ("RDS", "db.t3.small", 0.034),
        ("Lambda", "Requests (per 1M)", 0.20),
        ("DynamoDB", "Write (per 1M)", 1.25),
        ("DynamoDB", "Read (per 1M)", 0.25)
    ]
    
    for service_name, instance_type, rate in legacy_services:
        db.execute(text("""
            INSERT INTO pricing_master (service_name, instance_type, hourly_rate)
            VALUES (:name, :type, :rate)
        """), {"name": service_name, "type": instance_type, "rate": rate})
    
    db.commit()
    print(f"Added {len(legacy_services)} legacy pricing entries")


def main():
    """Main seeding function"""
    print("\n" + "="*60)
    print("AWS PRICING DATABASE SEEDING")
    print("="*60 + "\n")
    
    # Initialize database (create tables)
    print("Initializing database...")
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Seed data in order
        seed_regions(db)
        seed_categories(db)
        seed_services(db)
        seed_configurations(db)
        seed_legacy_data(db)
        
        print("\n" + "="*60)
        print("DATABASE SEEDING COMPLETED SUCCESSFULLY!")
        print("="*60 + "\n")
        
        # Print summary
        from sqlalchemy import func
        print("Database Summary:")
        print(f"   Regions: {db.query(func.count(Region.id)).scalar()}")
        print(f"   Categories: {db.query(func.count(ServiceCategory.id)).scalar()}")
        print(f"   Services: {db.query(func.count(Service.id)).scalar()}")
        print(f"   SKUs: {db.query(func.count(ServiceSKU.id)).scalar()}")
        print(f"   Pricing Tiers: {db.query(func.count(PricingTier.id)).scalar()}")
        print(f"   Configurations: {db.query(func.count(ServiceConfiguration.id)).scalar()}")
        print()
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()

# Made with Bob
