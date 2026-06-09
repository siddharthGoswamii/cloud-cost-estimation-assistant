"""
Update Database Prices from AWS API
Run this script periodically to keep prices up-to-date
"""

from database import SessionLocal
from aws_pricing_fetcher import AWSPricingFetcher
from models import ServiceSKU, Service
from sqlalchemy import func

def update_all_prices():
    """Update all service prices in database"""
    print("\n" + "="*60)
    print("UPDATING DATABASE PRICES FROM AWS")
    print("="*60 + "\n")
    
    db = SessionLocal()
    fetcher = AWSPricingFetcher()
    
    try:
        # Fetch latest prices
        print("Step 1: Fetching latest prices from AWS...")
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
        for region in regions:
            fetcher.fetch_all_prices(region)
        
        print(f"\nFetched {len(fetcher.cache)} prices")
        
        # Update EC2 prices
        print("\nStep 2: Updating EC2 prices...")
        ec2_service = db.query(Service).filter(Service.code == "EC2").first()
        if ec2_service:
            ec2_skus = db.query(ServiceSKU).filter(
                ServiceSKU.service_id == ec2_service.id
            ).all()
            
            updated_count = 0
            for sku in ec2_skus:
                instance_type = sku.name
                new_price = fetcher.get_ec2_pricing(instance_type)
                
                if new_price and abs(new_price - sku.base_price) > 0.0001:
                    print(f"  {instance_type}: ${sku.base_price:.4f} -> ${new_price:.4f}")
                    sku.base_price = new_price
                    updated_count += 1
            
            print(f"Updated {updated_count} EC2 prices")
        
        # Update RDS prices
        print("\nStep 3: Updating RDS prices...")
        rds_service = db.query(Service).filter(Service.code == "RDS").first()
        if rds_service:
            rds_skus = db.query(ServiceSKU).filter(
                ServiceSKU.service_id == rds_service.id
            ).all()
            
            updated_count = 0
            for sku in rds_skus:
                instance_type = sku.name
                new_price = fetcher.get_rds_pricing(instance_type)
                
                if new_price and abs(new_price - sku.base_price) > 0.0001:
                    print(f"  {instance_type}: ${sku.base_price:.4f} -> ${new_price:.4f}")
                    sku.base_price = new_price
                    updated_count += 1
            
            print(f"Updated {updated_count} RDS prices")
        
        # Commit changes
        db.commit()
        
        print("\n" + "="*60)
        print("DATABASE PRICES UPDATED SUCCESSFULLY!")
        print("="*60)
        print("\nNext update recommended: 24 hours from now")
        print("To automate: Set up a cron job or scheduled task")
        
    except Exception as e:
        print(f"\nError updating prices: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def show_current_prices():
    """Display current prices in database"""
    print("\n" + "="*60)
    print("CURRENT PRICES IN DATABASE")
    print("="*60 + "\n")
    
    db = SessionLocal()
    
    try:
        # Show EC2 prices
        print("EC2 Instance Prices (per hour):")
        ec2_service = db.query(Service).filter(Service.code == "EC2").first()
        if ec2_service:
            ec2_skus = db.query(ServiceSKU).filter(
                ServiceSKU.service_id == ec2_service.id
            ).order_by(ServiceSKU.base_price).all()
            
            for sku in ec2_skus:
                print(f"  {sku.name:15} ${sku.base_price:.4f}/hour")
        
        # Show RDS prices
        print("\nRDS Instance Prices (per hour):")
        rds_service = db.query(Service).filter(Service.code == "RDS").first()
        if rds_service:
            rds_skus = db.query(ServiceSKU).filter(
                ServiceSKU.service_id == rds_service.id
            ).order_by(ServiceSKU.base_price).all()
            
            for sku in rds_skus:
                print(f"  {sku.name:15} ${sku.base_price:.4f}/hour")
        
        print("\n" + "="*60)
        
    finally:
        db.close()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        show_current_prices()
    else:
        update_all_prices()
        print("\nTo view current prices, run:")
        print("python update_prices_in_db.py --show")

# Made with Bob
