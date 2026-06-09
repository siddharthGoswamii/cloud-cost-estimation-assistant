"""
Reset and seed database
Clears all existing data and re-seeds
"""

from database import reset_db, SessionLocal
from seed_db import seed_regions, seed_categories, seed_services, seed_configurations, seed_legacy_data
from sqlalchemy import func
from models import Region, ServiceCategory, Service, ServiceSKU, PricingTier, ServiceConfiguration

def main():
    print("\n" + "="*60)
    print("DATABASE RESET AND SEEDING")
    print("="*60 + "\n")
    
    # Reset database (drop and recreate tables)
    print("Resetting database...")
    reset_db()
    
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
