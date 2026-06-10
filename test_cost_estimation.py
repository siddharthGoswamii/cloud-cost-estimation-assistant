"""
Test script to verify cost estimation fixes
"""
import sys
sys.path.append('backend')

from pricing_engine import PricingEngine
from conversational_cost_agent import ConversationalCostAgent

# Initialize
pricing_engine = PricingEngine(use_live_pricing=False)
agent = ConversationalCostAgent(pricing_engine=pricing_engine)

# Test the exact prompt from the screenshot
test_prompt = """A data ingestion pipeline deployed in us-east-1 consisting of 6 EC2 c6i.xlarge 
compute nodes running 730 hours each. The ingestion tier uses an Amazon ElastiCache Redis cluster 
using a cache.m6g.large node running full-time. Raw events are pushed to an RDS PostgreSQL 
db.m6g.xlarge Multi-AZ database with 800GB gp3 storage. The architecture archives processed 
records into an S3 standard bucket holding 31TB of data, while utilizing a separate S3 Glacier 
Flexible Retrieval bucket with 10TB for cold backups."""

print("=" * 80)
print("TESTING COST ESTIMATION")
print("=" * 80)
print(f"\nPrompt: {test_prompt[:100]}...\n")

# Create session and process
session_id = "test_session_001"
session = agent.create_session(session_id)

# Parse architecture
services = agent.parse_architecture_description(test_prompt, session)
session.services = services

print(f"\n{'='*80}")
print(f"DETECTED SERVICES: {len(services)}")
print(f"{'='*80}")

for idx, service in enumerate(services, 1):
    print(f"\n{idx}. {service.name}")
    print(f"   Instance Type: {service.instance_type}")
    print(f"   Quantity: {service.quantity}")
    print(f"   Storage: {service.storage_gb}GB" if service.storage_gb else "   Storage: N/A")
    print(f"   Additional Params: {service.additional_params}")

# Calculate costs
print(f"\n{'='*80}")
print("CALCULATING COSTS")
print(f"{'='*80}\n")

for service in session.services:
    cost = agent.calculate_service_cost(service, session)
    print(f"{service.name}: ${cost:.2f}/month")

session.total_monthly_cost = sum(s.monthly_cost for s in session.services)
session.total_annual_cost = session.total_monthly_cost * 12

print(f"\n{'='*80}")
print("COST SUMMARY")
print(f"{'='*80}")
print(f"Total Monthly: ${session.total_monthly_cost:.2f}")
print(f"Total Annual: ${session.total_annual_cost:.2f}")
print(f"{'='*80}\n")

# Expected costs (approximate):
# - 6x EC2 c6i.xlarge @ $0.17/hr * 730hrs = $745.20
# - 1x ElastiCache cache.m6g.large @ $0.161/hr * 730hrs = $117.53
# - 1x RDS db.m6g.xlarge @ $0.364/hr * 730hrs = $265.72
# - RDS storage 800GB @ $0.115/GB = $92.00
# - S3 31TB (31,000GB) @ ~$0.023/GB = $713.00
# - Glacier 10TB (10,000GB) @ $0.0036/GB = $36.00
# Total Expected: ~$1,969.45/month

print("\nExpected approximate total: ~$1,969/month")
print("(6x EC2 c6i.xlarge + ElastiCache + RDS + S3 + Glacier)")

# Made with Bob
