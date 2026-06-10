"""
AWS Real-Time Pricing Fetcher using boto3
Fetches current pricing from AWS Price List API programmatically
"""

import boto3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
from decimal import Decimal

class AWSPricingBoto3:
    """Fetch real-time pricing from AWS using boto3"""
    
    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None, region_name='us-east-1'):
        """
        Initialize AWS Pricing client
        
        Args:
            aws_access_key_id: AWS access key (optional, uses env vars if not provided)
            aws_secret_access_key: AWS secret key (optional, uses env vars if not provided)
            region_name: AWS region for pricing API (default: us-east-1)
        """
        # AWS Pricing API is only available in us-east-1 and ap-south-1
        self.pricing_client = boto3.client(
            'pricing',
            region_name='us-east-1',  # Pricing API endpoint
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        
        self.cache = {}
        self.cache_duration = timedelta(hours=24)
        self.cache_file = "pricing_cache_boto3.json"
        self.load_cache()
    
    def load_cache(self):
        """Load cached pricing data"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    self.cache = data.get('prices', {})
                    print(f"[OK] Loaded {len(self.cache)} cached prices from {self.cache_file}")
        except Exception as e:
            print(f"[WARN] Could not load cache: {e}")
            self.cache = {}
    
    def save_cache(self):
        """Save pricing data to cache"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump({
                    'prices': self.cache,
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
            print(f"[OK] Pricing cache saved to {self.cache_file}")
        except Exception as e:
            print(f"[WARN] Could not save cache: {e}")
    
    def _get_region_code(self, region: str) -> str:
        """Convert region code to AWS region name"""
        region_mapping = {
            'us-east-1': 'US East (N. Virginia)',
            'us-east-2': 'US East (Ohio)',
            'us-west-1': 'US West (N. California)',
            'us-west-2': 'US West (Oregon)',
            'eu-west-1': 'EU (Ireland)',
            'eu-west-2': 'EU (London)',
            'eu-central-1': 'EU (Frankfurt)',
            'ap-south-1': 'Asia Pacific (Mumbai)',
            'ap-southeast-1': 'Asia Pacific (Singapore)',
            'ap-southeast-2': 'Asia Pacific (Sydney)',
            'ap-northeast-1': 'Asia Pacific (Tokyo)',
        }
        return region_mapping.get(region, 'US East (N. Virginia)')
    
    def get_ec2_pricing(self, instance_type: str, region: str = "us-east-1", 
                       operating_system: str = "Linux") -> Optional[float]:
        """
        Get EC2 instance on-demand pricing using boto3
        
        Args:
            instance_type: e.g., "t3.large"
            region: AWS region code
            operating_system: OS type (Linux, Windows, etc.)
            
        Returns:
            Hourly price in USD or None if not found
        """
        cache_key = f"EC2_{instance_type}_{region}_{operating_system}"
        
        # Check cache
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        try:
            region_name = self._get_region_code(region)
            
            # Query AWS Pricing API
            response = self.pricing_client.get_products(
                ServiceCode='AmazonEC2',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': operating_system},
                    {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
                    {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
                    {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
                ],
                MaxResults=1
            )
            
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                
                # Extract on-demand pricing
                on_demand = price_item['terms']['OnDemand']
                price_dimensions = list(on_demand.values())[0]['priceDimensions']
                price_per_unit = list(price_dimensions.values())[0]['pricePerUnit']['USD']
                
                price = float(price_per_unit)
                
                # Cache the result
                self.cache[cache_key] = {
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'instance_type': instance_type,
                    'region': region
                }
                self.save_cache()
                
                print(f"[OK] Fetched EC2 {instance_type} in {region}: ${price}/hour")
                return price
            else:
                print(f"[WARN] No pricing found for EC2 {instance_type} in {region}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error fetching EC2 pricing for {instance_type}: {e}")
            return None
    
    def get_rds_pricing(self, instance_type: str, region: str = "us-east-1",
                       database_engine: str = "MySQL") -> Optional[float]:
        """
        Get RDS instance on-demand pricing
        
        Args:
            instance_type: e.g., "db.t3.micro"
            region: AWS region code
            database_engine: Database engine (MySQL, PostgreSQL, etc.)
            
        Returns:
            Hourly price in USD or None if not found
        """
        cache_key = f"RDS_{instance_type}_{region}_{database_engine}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        try:
            region_name = self._get_region_code(region)
            
            response = self.pricing_client.get_products(
                ServiceCode='AmazonRDS',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'databaseEngine', 'Value': database_engine},
                    {'Type': 'TERM_MATCH', 'Field': 'deploymentOption', 'Value': 'Single-AZ'},
                ],
                MaxResults=1
            )
            
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                on_demand = price_item['terms']['OnDemand']
                price_dimensions = list(on_demand.values())[0]['priceDimensions']
                price_per_unit = list(price_dimensions.values())[0]['pricePerUnit']['USD']
                
                price = float(price_per_unit)
                
                self.cache[cache_key] = {
                    'price': price,
                    'timestamp': datetime.now().isoformat(),
                    'instance_type': instance_type,
                    'region': region
                }
                self.save_cache()
                
                print(f"[OK] Fetched RDS {instance_type} in {region}: ${price}/hour")
                return price
            else:
                print(f"[WARN] No pricing found for RDS {instance_type} in {region}")
                return None
                
        except Exception as e:
            print(f"[ERROR] Error fetching RDS pricing for {instance_type}: {e}")
            return None
    
    def get_lambda_pricing(self, region: str = "us-east-1") -> Dict[str, float]:
        """
        Get Lambda pricing (requests and compute)
        
        Returns:
            Dict with requestCostPerMillion and gbSecondCost
        """
        cache_key = f"Lambda_{region}"
        
        if cache_key in self.cache:
            cached_data = self.cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                return cached_data['price']
        
        region_name = self._get_region_code(region)
        
        # Map region to usagetype prefix
        region_prefix_map = {
            "us-east-1": "",           # N. Virginia has no prefix
            "us-east-2": "USE2-",
            "us-west-1": "USW1-",
            "us-west-2": "USW2-",
            "eu-west-1": "EU-",
            "ap-south-1": "APS3-",
            "ap-northeast-1": "APN1-",
            "ap-southeast-1": "APS1-",
            "ap-southeast-2": "APS2-",
        }
        prefix = region_prefix_map.get(region, "")
        
        try:
            # Fetch request pricing
            response = self.pricing_client.get_products(
                ServiceCode='AWSLambda',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'usagetype',
                     'Value': f'{prefix}Lambda-Request-Tier1'},
                ],
                MaxResults=1
            )
            
            request_price = 0.20  # fallback
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                on_demand = price_item['terms']['OnDemand']
                price_dimensions = list(on_demand.values())[0]['priceDimensions']
                # Price is per request, convert to per million
                per_request = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
                request_price = per_request * 1_000_000
                print(f"  [OK] Live Lambda request price: ${request_price}/M requests")
            else:
                print(f"  [WARN] Lambda request pricing not found, using default ${request_price}/M")
            
            # Fetch GB-second pricing
            response = self.pricing_client.get_products(
                ServiceCode='AWSLambda',
                Filters=[
                    {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region_name},
                    {'Type': 'TERM_MATCH', 'Field': 'usagetype',
                     'Value': f'{prefix}Lambda-GB-Second'},
                ],
                MaxResults=1
            )
            
            gb_second_price = 0.0000166667  # fallback
            if response['PriceList']:
                price_item = json.loads(response['PriceList'][0])
                on_demand = price_item['terms']['OnDemand']
                price_dimensions = list(on_demand.values())[0]['priceDimensions']
                gb_second_price = float(list(price_dimensions.values())[0]['pricePerUnit']['USD'])
                print(f"  [OK] Live Lambda GB-second price: ${gb_second_price}/GB-sec")
            else:
                print(f"  [WARN] Lambda GB-second pricing not found, using default ${gb_second_price}")
            
            pricing = {
                "requestCostPerMillion": request_price,
                "gbSecondCost": gb_second_price
            }
            
            self.cache[cache_key] = {
                'price': pricing,
                'timestamp': datetime.now().isoformat()
            }
            self.save_cache()
            return pricing
            
        except Exception as e:
            print(f"  [ERROR] Error fetching Lambda pricing: {e}")
            return {"requestCostPerMillion": 0.20, "gbSecondCost": 0.0000166667}
    
    def fetch_all_prices(self, region: str = "us-east-1"):
        """
        Fetch all service prices and update cache
        """
        print(f"\n{'='*60}")
        print(f"[FETCH] Fetching AWS prices for region: {region}")
        print(f"{'='*60}\n")
        
        # Fetch EC2 prices
        ec2_instances = ["t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge",
                        "m5.large", "m5.xlarge", "m5.2xlarge",
                        "c5.large", "c5.xlarge",
                        "r5.large", "r5.xlarge"]
        
        print("[LOAD] Fetching EC2 instance prices...")
        for instance in ec2_instances:
            self.get_ec2_pricing(instance, region)
        
        # Fetch RDS prices
        rds_instances = ["db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
                        "db.r5.large", "db.r5.xlarge", "db.m5.large"]
        
        print("\n[LOAD] Fetching RDS instance prices...")
        for instance in rds_instances:
            self.get_rds_pricing(instance, region)
        
        # Fetch Lambda pricing
        print("\n[LOAD] Fetching Lambda pricing...")
        self.get_lambda_pricing(region)
        
        print(f"\n{'='*60}")
        print(f"[OK] Fetched and cached {len(self.cache)} prices")
        print(f"{'='*60}\n")


# Standalone script to fetch and cache prices
if __name__ == "__main__":
    print("\n" + "="*60)
    print("AWS Pricing Fetcher (boto3) - Real-Time Price Updates")
    print("="*60 + "\n")
    
    # Check for AWS credentials
    import os
    if not os.getenv('AWS_ACCESS_KEY_ID') and not os.getenv('AWS_SECRET_ACCESS_KEY'):
        print("[WARN]  WARNING: AWS credentials not found in environment variables")
        print("   Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY to fetch live prices")
        print("   Or configure AWS CLI with 'aws configure'\n")
    
    try:
        fetcher = AWSPricingBoto3()
        
        # Fetch prices for multiple regions
        regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
        
        for region in regions:
            fetcher.fetch_all_prices(region)
        
        print("\n" + "="*60)
        print(f"[OK] Price update complete!")
        print(f"[STATS] Total cached prices: {len(fetcher.cache)}")
        print(f"[SAVE] Cache saved to: {fetcher.cache_file}")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        print("\nMake sure you have:")
        print("1. boto3 installed: pip install boto3")
        print("2. AWS credentials configured")
        print("3. IAM permissions for pricing:GetProducts\n")

# Made with Bob
