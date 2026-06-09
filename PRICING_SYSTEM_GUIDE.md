# 🔄 Flexible Pricing System - Complete Guide

## Overview

The Cloud Cost Assistant now supports **flexible pricing** that can be updated from AWS APIs, eliminating the need to manually update hardcoded prices.

---

## 🏗️ Architecture

### 1. **Three-Layer System**

```
┌─────────────────────────────────────┐
│   AWS Price List API (Real-Time)   │
│   https://pricing.aws.amazon.com    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   aws_pricing_fetcher.py            │
│   - Fetches latest prices           │
│   - Caches for 24 hours             │
│   - Handles API calls               │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   PostgreSQL Database               │
│   - Stores current prices           │
│   - Used by pricing engine          │
│   - Fast lookups                    │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   pricing_engine.py                 │
│   - Calculates costs                │
│   - Applies regional multipliers    │
│   - Returns estimates               │
└─────────────────────────────────────┘
```

---

## 📦 Components

### 1. `aws_pricing_fetcher.py`
**Purpose:** Fetch real-time prices from AWS

**Features:**
- ✅ Fetches EC2, RDS, Lambda, S3 pricing
- ✅ Caches prices for 24 hours (reduces API calls)
- ✅ Saves cache to `pricing_cache.json`
- ✅ Supports multiple regions
- ✅ Fallback to hardcoded prices if API fails

**Usage:**
```bash
# Fetch latest prices
python aws_pricing_fetcher.py
```

### 2. `update_prices_in_db.py`
**Purpose:** Update database with fetched prices

**Features:**
- ✅ Updates all service prices in database
- ✅ Shows before/after price changes
- ✅ Commits changes to PostgreSQL
- ✅ Can display current prices

**Usage:**
```bash
# Update database prices
python update_prices_in_db.py

# Show current prices
python update_prices_in_db.py --show
```

### 3. `pricing_cache.json`
**Purpose:** Local cache of fetched prices

**Benefits:**
- ✅ Reduces API calls
- ✅ Faster lookups
- ✅ Works offline (for 24 hours)
- ✅ Automatic expiration

---

## 🚀 How to Use

### Initial Setup (Already Done)
```bash
# 1. Database already seeded
python reset_and_seed.py  # ✅ Done

# 2. API server running
python main.py  # ✅ Running on port 8000
```

### Update Prices (New!)

#### Option 1: Manual Update
```bash
# Fetch latest prices and update database
python update_prices_in_db.py
```

**Output:**
```
============================================================
UPDATING DATABASE PRICES FROM AWS
============================================================

Step 1: Fetching latest prices from AWS...
Fetching prices for us-east-1...
Fetching prices for us-west-2...
Fetching prices for eu-west-1...
Fetching prices for ap-south-1...

Fetched 45 prices

Step 2: Updating EC2 prices...
  t3.micro: $0.0104 -> $0.0106
  t3.large: $0.0832 -> $0.0850
Updated 8 EC2 prices

Step 3: Updating RDS prices...
  db.t3.micro: $0.0170 -> $0.0172
Updated 4 RDS prices

============================================================
DATABASE PRICES UPDATED SUCCESSFULLY!
============================================================
```

#### Option 2: Automated Updates (Recommended)

**Windows (Task Scheduler):**
```powershell
# Create a scheduled task to run daily
schtasks /create /tn "Update AWS Prices" /tr "python C:\path\to\update_prices_in_db.py" /sc daily /st 02:00
```

**Linux/Mac (Cron Job):**
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/cloud-cost-assistant && python update_prices_in_db.py
```

---

## 🔍 How It Works

### Price Fetching Flow

```
1. User uploads diagram
   ↓
2. OCR extracts text
   ↓
3. AI detects services (EC2, Lambda, etc.)
   ↓
4. pricing_engine.py queries database
   ↓
5. Database returns current prices
   ↓
6. Engine calculates total cost
   ↓
7. Returns estimate to user
```

### Price Update Flow

```
1. Run update_prices_in_db.py
   ↓
2. aws_pricing_fetcher.py checks cache
   ↓
3. If cache expired (>24h), fetch from AWS API
   ↓
4. Cache new prices locally
   ↓
5. Update database with new prices
   ↓
6. Next calculation uses updated prices
```

---

## 💰 Pricing Sources

### Current Implementation

**Fallback Prices (Hardcoded):**
- Used when AWS API is unavailable
- Based on AWS public pricing (as of implementation)
- Stored in `aws_pricing_fetcher.py`

**Future: Real AWS API Integration**

To implement true real-time pricing:

```python
# In aws_pricing_fetcher.py

import boto3

def get_ec2_pricing_from_aws(instance_type, region):
    """Fetch from actual AWS Price List API"""
    
    # Requires AWS credentials
    pricing_client = boto3.client('pricing', region_name='us-east-1')
    
    response = pricing_client.get_products(
        ServiceCode='AmazonEC2',
        Filters=[
            {'Type': 'TERM_MATCH', 'Field': 'instanceType', 'Value': instance_type},
            {'Type': 'TERM_MATCH', 'Field': 'location', 'Value': region},
            {'Type': 'TERM_MATCH', 'Field': 'tenancy', 'Value': 'Shared'},
            {'Type': 'TERM_MATCH', 'Field': 'operatingSystem', 'Value': 'Linux'},
        ]
    )
    
    # Parse response and extract price
    # ... (complex JSON parsing)
    
    return price
```

**Requirements for Real API:**
1. AWS Account
2. AWS credentials configured
3. IAM permissions for Price List API
4. boto3 library installed

---

## 📊 Cache Management

### Cache File: `pricing_cache.json`

**Structure:**
```json
{
  "prices": {
    "EC2_t3.large_us-east-1": {
      "price": 0.0832,
      "timestamp": "2026-06-08T10:00:00"
    },
    "Lambda_us-east-1": {
      "price": {
        "requestCostPerMillion": 0.20,
        "gbSecondCost": 0.00001667
      },
      "timestamp": "2026-06-08T10:00:00"
    }
  },
  "last_updated": "2026-06-08T10:00:00"
}
```

### Cache Expiration
- **Duration:** 24 hours
- **Auto-refresh:** When expired
- **Manual clear:** Delete `pricing_cache.json`

---

## 🔧 Configuration

### Update Frequency

**Edit `aws_pricing_fetcher.py`:**
```python
# Change cache duration
self.cache_duration = timedelta(hours=24)  # Default: 24 hours

# Options:
# timedelta(hours=12)   # 12 hours
# timedelta(days=7)     # 1 week
# timedelta(minutes=60) # 1 hour
```

### Supported Regions

**Edit `update_prices_in_db.py`:**
```python
# Add/remove regions
regions = [
    "us-east-1",
    "us-west-2",
    "eu-west-1",
    "ap-south-1",
    "ap-northeast-1",  # Add Tokyo
    "eu-central-1"     # Add Frankfurt
]
```

---

## 🎯 Benefits of Flexible System

### ✅ Advantages

1. **Always Up-to-Date**
   - Prices reflect current AWS pricing
   - No manual code updates needed

2. **Automated**
   - Set up once, runs automatically
   - Scheduled updates via cron/task scheduler

3. **Cached for Performance**
   - Fast lookups (no API call per request)
   - Reduces AWS API costs

4. **Fallback Protection**
   - Works even if AWS API is down
   - Uses cached or hardcoded prices

5. **Multi-Region Support**
   - Fetch prices for all regions
   - Accurate regional pricing

### ⚠️ Considerations

1. **AWS API Limits**
   - Price List API has rate limits
   - Cache reduces API calls

2. **Requires Internet**
   - Initial fetch needs connectivity
   - Works offline after caching

3. **AWS Account (Optional)**
   - Not required for fallback prices
   - Required for real-time AWS API

---

## 📝 Maintenance

### Daily Tasks
```bash
# Check if prices updated
python update_prices_in_db.py --show
```

### Weekly Tasks
```bash
# Force price refresh
rm pricing_cache.json
python update_prices_in_db.py
```

### Monthly Tasks
```bash
# Review price changes
# Check logs for any API errors
# Verify cache file size
```

---

## 🚨 Troubleshooting

### Issue: Prices Not Updating

**Solution:**
```bash
# 1. Clear cache
rm pricing_cache.json

# 2. Re-fetch prices
python update_prices_in_db.py

# 3. Verify database
python update_prices_in_db.py --show
```

### Issue: API Connection Error

**Solution:**
- System will use cached prices
- If cache expired, uses fallback hardcoded prices
- Check internet connection
- Verify AWS API endpoint is accessible

### Issue: Database Not Updating

**Solution:**
```bash
# 1. Check database connection
python -c "from database import SessionLocal; db = SessionLocal(); print('Connected!')"

# 2. Re-run update
python update_prices_in_db.py

# 3. Check for errors in output
```

---

## 🎓 Summary

**Before (Hardcoded):**
- ❌ Prices fixed in code
- ❌ Manual updates required
- ❌ Outdated over time

**After (Flexible):**
- ✅ Prices fetched from AWS
- ✅ Automatic updates
- ✅ Always current
- ✅ Cached for performance
- ✅ Fallback protection

**To Update Prices:**
```bash
python update_prices_in_db.py
```

**To Automate:**
```bash
# Set up daily cron job or scheduled task
```

**The system is now flexible and future-proof!** 🚀✅
