"""
Fetch and Display Real AWS Pricing Data
Uses AWS credentials from .env file to fetch live pricing from AWS API
"""

import os
import sys
import json

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

try:
    from dotenv import load_dotenv
except ImportError:
    print("Warning: python-dotenv not installed, using os.environ directly")
    load_dotenv = lambda: None

from aws_pricing_boto3 import AWSPricingBoto3

def display_pricing_data():
    """Fetch and display real AWS pricing data"""
    
    # Load environment variables
    load_dotenv()
    
    # Get AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
    
    if not aws_access_key or not aws_secret_key:
        print("❌ ERROR: AWS credentials not found in .env file")
        print("Please ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set")
        return
    
    print("\n" + "="*70)
    print("🌐 FETCHING REAL AWS PRICING DATA FROM AWS API")
    print("="*70)
    print(f"📍 Region: {aws_region}")
    print(f"🔑 Using AWS Account: {aws_access_key[:10]}...")
    print("="*70 + "\n")
    
    # Initialize pricing fetcher with credentials
    try:
        fetcher = AWSPricingBoto3(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        print("✅ Successfully connected to AWS Pricing API\n")
        
        # Fetch EC2 Pricing
        print("="*70)
        print("💻 EC2 INSTANCE PRICING (On-Demand, Linux)")
        print("="*70)
        
        ec2_instances = [
            "t3.micro", "t3.small", "t3.medium", "t3.large", "t3.xlarge",
            "m5.large", "m5.xlarge", "m5.2xlarge",
            "c5.large", "c5.xlarge",
            "r5.large", "r5.xlarge"
        ]
        
        ec2_prices = {}
        for instance in ec2_instances:
            price = fetcher.get_ec2_pricing(instance, aws_region, "Linux")
            if price:
                ec2_prices[instance] = price
                print(f"  ✓ {instance:15s} → ${price:.4f}/hour (${price*730:.2f}/month)")
        
        # Fetch RDS Pricing
        print("\n" + "="*70)
        print("🗄️  RDS DATABASE INSTANCE PRICING (On-Demand, MySQL)")
        print("="*70)
        
        rds_instances = [
            "db.t3.micro", "db.t3.small", "db.t3.medium", "db.t3.large",
            "db.r5.large", "db.r5.xlarge", "db.m5.large"
        ]
        
        rds_prices = {}
        for instance in rds_instances:
            price = fetcher.get_rds_pricing(instance, aws_region, "MySQL")
            if price:
                rds_prices[instance] = price
                print(f"  ✓ {instance:15s} → ${price:.4f}/hour (${price*730:.2f}/month)")
        
        # Fetch Lambda Pricing
        print("\n" + "="*70)
        print("⚡ AWS LAMBDA PRICING")
        print("="*70)
        
        lambda_pricing = fetcher.get_lambda_pricing(aws_region)
        print(f"  ✓ Requests:  ${lambda_pricing['requestCostPerMillion']:.2f} per 1M requests")
        print(f"  ✓ Compute:   ${lambda_pricing['gbSecondCost']:.10f} per GB-second")
        print(f"  ✓ Example:   1M requests @ 128MB, 200ms = ${lambda_pricing['requestCostPerMillion'] + (lambda_pricing['gbSecondCost'] * 0.128 * 0.2 * 1000000):.2f}")
        
        # Summary
        print("\n" + "="*70)
        print("📊 PRICING SUMMARY")
        print("="*70)
        print(f"  • Total EC2 instances fetched: {len(ec2_prices)}")
        print(f"  • Total RDS instances fetched: {len(rds_prices)}")
        print(f"  • Lambda pricing components: 2 (requests + compute)")
        print(f"  • Total cached prices: {len(fetcher.cache)}")
        print(f"  • Cache file: {fetcher.cache_file}")
        print("="*70)
        
        # Display cache info
        print("\n" + "="*70)
        print("💾 PRICING CACHE DETAILS")
        print("="*70)
        
        cache_summary = {}
        for key, value in fetcher.cache.items():
            service = key.split('_')[0]
            if service not in cache_summary:
                cache_summary[service] = 0
            cache_summary[service] += 1
        
        for service, count in cache_summary.items():
            print(f"  • {service}: {count} prices cached")
        
        print("\n✅ All pricing data fetched successfully from AWS API!")
        print("="*70 + "\n")
        
        # Export to JSON for reference
        export_data = {
            "region": aws_region,
            "timestamp": fetcher.cache[list(fetcher.cache.keys())[0]]['timestamp'] if fetcher.cache else None,
            "ec2_prices": ec2_prices,
            "rds_prices": rds_prices,
            "lambda_pricing": lambda_pricing,
            "total_cached": len(fetcher.cache)
        }
        
        with open('live_pricing_export.json', 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print("📄 Pricing data exported to: live_pricing_export.json\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: Failed to fetch pricing data")
        print(f"Error details: {str(e)}")
        print("\nPossible issues:")
        print("  1. Invalid AWS credentials")
        print("  2. Insufficient IAM permissions (need pricing:GetProducts)")
        print("  3. Network connectivity issues")
        print("  4. AWS API rate limiting")
        return

if __name__ == "__main__":
    display_pricing_data()

# Made with Bob
