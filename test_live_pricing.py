"""
Test script for AWS live pricing integration
"""

import os
import sys
from dotenv import load_dotenv
from pricing_engine import PricingEngine

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Load environment variables
load_dotenv()

print("\n" + "="*60)
print("Testing AWS Live Pricing Integration")
print("="*60 + "\n")

# Check credentials
if os.getenv('AWS_ACCESS_KEY_ID'):
    print("[OK] AWS credentials found in environment")
else:
    print("[ERROR] AWS credentials NOT found")
    print("   Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in .env file")
    exit(1)

# Initialize pricing engine with live pricing
print("\nInitializing Pricing Engine with live pricing...")
engine = PricingEngine(use_live_pricing=True)

print("\n" + "-"*60)
print("Test 1: EC2 t3.large pricing")
print("-"*60)

try:
    result = engine.calculate("EC2", {
        "region": "us-east-1",
        "instanceType": "t3.large",
        "hours": 730,
        "count": 1
    })
    print(f"[OK] EC2 t3.large cost: ${result['cost']:.2f}/month")
    print(f"   Hourly rate: ${result['breakdown']['hourlyRate']:.4f}/hour")
    print(f"   Region multiplier: {result['region_multiplier']}x")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "-"*60)
print("Test 2: RDS db.t3.micro pricing")
print("-"*60)

try:
    result = engine.calculate("RDS", {
        "region": "us-east-1",
        "instanceType": "db.t3.micro",
        "hours": 730,
        "count": 1,
        "storageGB": 20
    })
    print(f"[OK] RDS db.t3.micro cost: ${result['cost']:.2f}/month")
    print(f"   Hourly rate: ${result['breakdown']['hourlyRate']:.4f}/hour")
    print(f"   Storage cost: ${result['breakdown'].get('storageCost', 0):.2f}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "-"*60)
print("Test 3: Lambda pricing")
print("-"*60)

try:
    result = engine.calculate("Lambda", {
        "region": "us-east-1",
        "requests": 50_000_000,
        "gbSeconds": 100_000
    })
    print(f"[OK] Lambda cost: ${result['cost']:.2f}/month")
    print(f"   Request cost: ${result['breakdown']['requestCost']:.4f}")
    print(f"   Compute cost: ${result['breakdown']['computeCost']:.4f}")
    print(f"   Billable requests: {result['breakdown']['billableRequests']:,}")
    print(f"   Billable GB-seconds: {result['breakdown']['billableGBSeconds']:,}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "-"*60)
print("Test 4: S3 storage pricing")
print("-"*60)

try:
    result = engine.calculate("S3", {
        "region": "us-east-1",
        "storageGB": 100,
        "usageGB": 100
    })
    print(f"[OK] S3 cost: ${result['cost']:.2f}/month")
    print(f"   Storage: {result['breakdown']['usageGB']}GB")
    print(f"   Billable: {result['breakdown']['billableGB']}GB (after free tier)")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "-"*60)
print("Test 5: DynamoDB pricing")
print("-"*60)

try:
    result = engine.calculate("DynamoDB", {
        "region": "us-east-1",
        "writes": 5_000_000,
        "reads": 5_000_000,
        "storageGB": 10
    })
    print(f"[OK] DynamoDB cost: ${result['cost']:.2f}/month")
    print(f"   Write cost: ${result['breakdown']['writeCost']:.4f}")
    print(f"   Read cost: ${result['breakdown']['readCost']:.4f}")
    print(f"   Storage cost: ${result['breakdown']['storageCost']:.4f}")
except Exception as e:
    print(f"[ERROR] {e}")

print("\n" + "="*60)
print("Testing Complete!")
print("="*60 + "\n")

# Made with Bob
