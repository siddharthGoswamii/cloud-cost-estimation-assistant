import os
import json
from dotenv import load_dotenv
import boto3

# 1. Load the keys from your .env file into memory
load_dotenv()

print("🔑 Access Key Loaded:", os.getenv("AWS_ACCESS_KEY_ID")[:8] + "...")

# 2. Initialize the programmatic AWS pricing client
pricing_client = boto3.client('pricing', region_name='us-east-1')

try:
    # 3. Pull a quick baseline product price for test confirmation
    print("⏳ Querying AWS Price List API...")
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': 't3.large'},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': 'US East (N. Virginia)'},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'preInstalledSw', 'Value': 'NA'},
            {'Type': 'TERM_MATCH', 'Field': 'capacitystatus', 'Value': 'Used'},
        ],
        MaxResults=1
    )
    
    # 4. Parse out and print the raw price metric
    price_list = response.get('PriceList', [])
    if price_list:
        product_data = json.loads(price_list[0])
        on_demand_terms = product_data['terms']['OnDemand']
        for term in on_demand_terms.values():
            for dimension in term['priceDimensions'].values():
                hourly_cost = dimension['pricePerUnit']['USD']
                print(f"✅ Success! Dynamic On-Demand price for t3.large is: ${hourly_cost} / hour")
    else:
        print("❌ Connected, but couldn't find matching price data metrics.")

except Exception as e:
    print(f"❌ Authentication Failed. Error Details:\n{str(e)}")