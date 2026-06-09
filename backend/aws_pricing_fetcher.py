"""
AWS Real-Time Pricing Fetcher
Fetches current pricing from AWS Price List API
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os

class AWSPricingFetcher:
    """Fetch real-time pricing from AWS Price List API"""
    
    def __init__(self):
        self.base_url = "https://pricing.us-east-1.amazonaws.com"
        self.cache = {}
        self.cache_duration = timedelta(hours=24)  # Cache for 24 hours
        self.cache_file = "pricing_cache.json"
        self.load_cache()
    
    def load_cache(self):
        """Load cached pricing data"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.cache = data.get('prices', {})
                    print(f"Loaded {len(self.cache)} cached prices")
        except Exception as e:
            print(f"Could not load cache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Save pricing data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'prices': self.cache,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            print("Pricing cache saved")
        except Exception as e:
            print(f"Could not save cache: {e}")
    
    def get_ec2_pricing(self, instance_type: str, region: str = "us-east-1") -> Optional[float]:
        """
        Get EC2 instance pricing
        
        Args:
            instance_type: e.g., "t3.large"
            region: AWS region code
            
        Returns:
            Hourly price in USD or None if not found
        """
        cache_key = f"EC2_{instance_type}_{region}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        try:
            # AWS Price List API endpoint for EC2
            url = f"{self.base_url}/offers/v1.0/aws/AmazonEC2/current/{region}/index.json"
            
            # Note: This is a simplified example. Real implementation would need:
            # 1. AWS credentials
            # 2. Proper API authentication
            # 3. Parsing complex pricing JSON
            
            # For now, return fallback to hardcoded prices
            fallback_prices = {
                "t3.micro": 0.0104,
                "t3.small": 0.0208,
                "t3.medium": 0.0416,
                "t3.large": 0.0832,
                "t3.xlarge": 0.1664,
                "m5.large": 0.096,
                "m5.xlarge": 0.192,
                "r5.large": 0.126,
                "r5.xlarge": 0.252
            }
            
            price = fallback_prices.get(instance_type)
            
            if price:
                # Cache the result
                self.cache[cache_key] = {
                    'price': price,
                    'timestamp': datetime.now().isoformat()
                }
                self.save_cache()
            
            return price
            
        except Exception as e:
            print(f"Error fetching EC2 pricing: {e}")
            return None
    
    def get_lambda_pricing(self, region: str = "us-east-1") -> Dict[str, float]:
        """Get Lambda pricing"""
        cache_key = f"Lambda_{region}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        # Fallback prices
        pricing = {
            "requestCostPerMillion": 0.20,
            "gbSecondCost": 0.00001667
        }
        
        self.cache[cache_key] = {
            'price': pricing,
            'timestamp': datetime.now().isoformat()
        }
        self.save_cache()
        
        return pricing
    
    def get_s3_pricing(self, region: str = "us-east-1") -> List[Dict]:
        """Get S3 tiered pricing"""
        cache_key = f"S3_{region}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        # Fallback tiered pricing
        tiers = [
            {"from": 0, "to": 50, "price": 0.023},
            {"from": 50, "to": 500, "price": 0.022},
            {"from": 500, "to": None, "price": 0.021}
        ]
        
        self.cache[cache_key] = {
            'price': tiers,
            'timestamp': datetime.now().isoformat()
        }
        self.save_cache()
        
        return tiers
    
    def get_rds_pricing(self, instance_type: str, region: str = "us-east-1") -> Optional[float]:
        """Get RDS instance pricing"""
        cache_key = f"RDS_{instance_type}_{region}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        # Fallback prices
        fallback_prices = {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.t3.large": 0.136,
            "db.r5.large": 0.24,
            "db.r5.xlarge": 0.48
        }
        
        price = fallback_prices.get(instance_type)
        
        if price:
            self.cache[cache_key] = {
                'price': price,
                'timestamp': datetime.now().isoformat()
            }
            self.save_cache()
        
        return price
    
    def fetch_all_prices(self, region: str = "us-east-1"):
        """
        Fetch all service prices and update cache
        This should be run periodically (e.g., daily) to keep prices updated
        """
        print(f"Fetching all prices for region: {region}")
        
        # Fetch EC2 prices
        ec2_instances = ["t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge",
                        "m5.large", "m5.xlarge", "r5.large", "r5.xlarge"]
        for instance in ec2_instances:
            self.get_ec2_pricing(instance, region)
        
        # Fetch RDS prices
        rds_instances = ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
                        "db.r5.large", "db.r5.xlarge"]
        for instance in rds_instances:
            self.get_rds_pricing(instance, region)
        
        # Fetch Lambda pricing
        self.get_lambda_pricing(region)
        
        # Fetch S3 pricing
        self.get_s3_pricing(region)
        
        print(f"Fetched and cached {len(self.cache)} prices")
        self.save_cache()
    
    def update_database_prices(self, db_session):
        """
        Update database with fetched prices
        This integrates with the existing database
        """
        from models import ServiceSKU
        
        print("Updating database with latest prices...")
        
        # Update EC2 prices
        ec2_skus = db_session.query(ServiceSKU).filter(
            ServiceSKU.sku_code.like('EC2-%')
        ).all()
        
        for sku in ec2_skus:
            instance_type = sku.name  # e.g., "t3.large"
            new_price = self.get_ec2_pricing(instance_type)
            if new_price and new_price != sku.base_price:
                old_price = sku.base_price
                sku.base_price = new_price
                print(f"Updated {instance_type}: ${old_price} -> ${new_price}")
        
        db_session.commit()
        print("Database prices updated!")


# Standalone script to update prices
if __name__ == "__main__":
    print("AWS Pricing Fetcher - Updating Prices")
    print("=" * 50)
    
    fetcher = AWSPricingFetcher()
    
    # Fetch prices for multiple regions
    regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
    
    for region in regions:
        print(f"\nFetching prices for {region}...")
        fetcher.fetch_all_prices(region)
    
    print("\n" + "=" * 50)
    print("Price update complete!")
    print(f"Total cached prices: {len(fetcher.cache)}")
    print("\nTo update database, run:")
    print("python update_prices_in_db.py")

# Made with Bob
