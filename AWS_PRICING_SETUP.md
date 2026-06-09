# AWS Pricing API Integration with boto3

This guide explains how to configure your backend to query the AWS Pricing API programmatically using boto3.

## Overview

The `aws_pricing_boto3.py` module provides real-time pricing data from AWS using the official boto3 SDK. It fetches current prices for EC2, RDS, Lambda, and other services directly from AWS.

## Prerequisites

### 1. Install boto3

```bash
pip install boto3
```

Or use the clean requirements file:

```bash
pip install -r requirements_clean.txt
```

### 2. AWS Credentials Setup

You need AWS credentials with permissions to access the Pricing API. There are several ways to configure credentials:

#### Option A: Environment Variables (Recommended for Development)

```bash
# Windows PowerShell
$env:AWS_ACCESS_KEY_ID="your_access_key_id"
$env:AWS_SECRET_ACCESS_KEY="your_secret_access_key"
$env:AWS_DEFAULT_REGION="us-east-1"

# Linux/Mac
export AWS_ACCESS_KEY_ID="your_access_key_id"
export AWS_SECRET_ACCESS_KEY="your_secret_access_key"
export AWS_DEFAULT_REGION="us-east-1"
```

#### Option B: AWS CLI Configuration

```bash
aws configure
```

This will prompt you for:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (use `us-east-1` for pricing API)
- Default output format (use `json`)

#### Option C: IAM Role (Recommended for Production)

If running on EC2, Lambda, or ECS, attach an IAM role with the `pricing:GetProducts` permission.

### 3. Required IAM Permissions

Your AWS user/role needs the following permission:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "pricing:GetProducts",
        "pricing:DescribeServices"
      ],
      "Resource": "*"
    }
  ]
}
```

## Usage

### Fetch Prices Manually

Run the standalone script to fetch and cache prices:

```bash
python aws_pricing_boto3.py
```

This will:
1. Connect to AWS Pricing API
2. Fetch prices for EC2, RDS, Lambda across multiple regions
3. Cache results in `pricing_cache_boto3.json`
4. Display progress and results

### Use in Your Application

```python
from aws_pricing_boto3 import AWSPricingBoto3

# Initialize the pricing fetcher
pricing = AWSPricingBoto3()

# Get EC2 pricing
ec2_price = pricing.get_ec2_pricing("t3.large", region="us-east-1")
print(f"EC2 t3.large: ${ec2_price}/hour")

# Get RDS pricing
rds_price = pricing.get_rds_pricing("db.t3.micro", region="us-east-1")
print(f"RDS db.t3.micro: ${rds_price}/hour")

# Get Lambda pricing
lambda_pricing = pricing.get_lambda_pricing(region="us-east-1")
print(f"Lambda: ${lambda_pricing['requestCostPerMillion']}/M requests")
print(f"Lambda: ${lambda_pricing['gbSecondCost']}/GB-second")

# Fetch all prices for a region
pricing.fetch_all_prices(region="us-east-1")
```

### Integrate with Pricing Engine

Update `pricing_engine.py` to use live prices:

```python
from aws_pricing_boto3 import AWSPricingBoto3

class PricingEngine:
    def __init__(self):
        self.aws_pricing = AWSPricingBoto3()
        # ... rest of initialization
    
    def get_service_info(self, service: str):
        # Fetch live prices from AWS
        if service == "EC2":
            # Get live EC2 pricing
            pass
        elif service == "Lambda":
            # Get live Lambda pricing
            pass
        # ... etc
```

## Features

### 1. Automatic Caching

- Prices are cached for 24 hours to reduce API calls
- Cache is saved to `pricing_cache_boto3.json`
- Automatically loads cache on startup

### 2. Multi-Region Support

Fetch prices for any AWS region:

```python
regions = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
for region in regions:
    pricing.fetch_all_prices(region)
```

### 3. Error Handling

- Gracefully handles API errors
- Falls back to cached prices if API is unavailable
- Provides detailed error messages

### 4. Supported Services

Currently supports:
- **EC2**: On-demand instance pricing
- **RDS**: Database instance pricing
- **Lambda**: Request and compute pricing
- **S3**: Storage pricing (coming soon)
- **DynamoDB**: Request pricing (coming soon)

## Pricing API Limitations

### 1. API Endpoint Region

The AWS Pricing API is only available in:
- `us-east-1` (US East - N. Virginia)
- `ap-south-1` (Asia Pacific - Mumbai)

The module automatically uses `us-east-1` regardless of your target region.

### 2. Rate Limits

AWS Pricing API has rate limits:
- 10 requests per second
- Use caching to minimize API calls

### 3. Data Freshness

- Prices are updated by AWS periodically (usually daily)
- Cache prices for 24 hours to balance freshness and performance

## Troubleshooting

### Error: "Unable to locate credentials"

**Solution**: Configure AWS credentials using one of the methods above.

```bash
aws configure
```

### Error: "Access Denied"

**Solution**: Ensure your IAM user/role has `pricing:GetProducts` permission.

### Error: "No pricing found"

**Possible causes**:
1. Instance type doesn't exist in that region
2. Incorrect instance type name (e.g., use "t3.large" not "T3.Large")
3. Service not available in that region

### Slow Performance

**Solution**: 
1. Use cached prices (automatically enabled)
2. Fetch prices in background/scheduled job
3. Don't fetch prices on every request

## Best Practices

### 1. Scheduled Price Updates

Run price updates daily via cron job or scheduled task:

```bash
# Linux cron (daily at 2 AM)
0 2 * * * cd /path/to/app && python aws_pricing_boto3.py

# Windows Task Scheduler
# Create a daily task to run: python aws_pricing_boto3.py
```

### 2. Use Cache First

Always check cache before making API calls:

```python
# The module does this automatically
price = pricing.get_ec2_pricing("t3.large")  # Uses cache if available
```

### 3. Handle Missing Prices

```python
price = pricing.get_ec2_pricing("t3.large")
if price is None:
    # Use fallback pricing or show error
    price = 0.0832  # Fallback price
```

### 4. Monitor API Usage

Track API calls to stay within rate limits:

```python
import logging
logging.basicConfig(level=logging.INFO)
# Module logs all API calls
```

## Integration with Main Application

### Step 1: Update main.py

Add endpoint to refresh prices:

```python
from aws_pricing_boto3 import AWSPricingBoto3

pricing_fetcher = AWSPricingBoto3()

@app.post("/api/refresh-prices")
async def refresh_prices(region: str = "us-east-1"):
    """Refresh AWS pricing data"""
    try:
        pricing_fetcher.fetch_all_prices(region)
        return {"success": True, "message": f"Prices refreshed for {region}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Step 2: Update Pricing Engine

Modify `pricing_engine.py` to use live prices:

```python
from aws_pricing_boto3 import AWSPricingBoto3

class PricingEngine:
    def __init__(self):
        self.aws_pricing = AWSPricingBoto3()
        self.pricing_db = PRICING_DATABASE  # Fallback
    
    def get_service_info(self, service: str):
        # Try to get live price first
        if service == "EC2":
            # Merge live prices with database
            pass
        # Fall back to database if live price unavailable
        return self.pricing_db.get(service)
```

## Cost Optimization

### API Call Costs

AWS Pricing API is **FREE** - no charges for API calls.

### Compute Costs

Minimal - fetching prices takes ~5-10 seconds for all services.

### Storage Costs

Cache file is ~50KB - negligible storage cost.

## Security Considerations

### 1. Protect AWS Credentials

- Never commit credentials to git
- Use environment variables or IAM roles
- Rotate credentials regularly

### 2. Least Privilege

Only grant `pricing:GetProducts` permission, nothing more.

### 3. Audit Access

Monitor CloudTrail logs for pricing API access.

## Next Steps

1. ✅ Install boto3
2. ✅ Configure AWS credentials
3. ✅ Test with: `python aws_pricing_boto3.py`
4. ⬜ Integrate with pricing_engine.py
5. ⬜ Set up scheduled price updates
6. ⬜ Add UI button to refresh prices

## Support

For issues or questions:
- AWS Pricing API Docs: https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/price-changes.html
- boto3 Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html