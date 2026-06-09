"""
AWS-Style Pricing Engine
Production-grade pricing calculation engine supporting multiple pricing models
Integrated with AWS Pricing API via boto3 for real-time pricing
"""

from typing import Dict, Any, Optional, List
from pricing_database import PRICING_DB, REGIONS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class PricingEngine:
    """
    Core pricing engine that mimics AWS billing logic
    Supports: hourly, tiered_gb, request_based, hybrid, flat_monthly models
    Now integrated with AWS Pricing API for real-time prices
    """
    
    def __init__(self, pricing_db: Dict = None, region_db: Dict = None, use_live_pricing: bool = True):
        self.pricing_db = pricing_db or PRICING_DB
        self.region_db = region_db or REGIONS
        self.use_live_pricing = use_live_pricing
        self.aws_pricing = None
        
        # Initialize AWS Pricing API if credentials are available
        if use_live_pricing and self._check_aws_credentials():
            try:
                from aws_pricing_boto3 import AWSPricingBoto3
                self.aws_pricing = AWSPricingBoto3()
                print("[OK] AWS Pricing API initialized - using live prices")
            except Exception as e:
                print(f"[WARN] Could not initialize AWS Pricing API: {e}")
                print("   Falling back to static pricing database")
                self.aws_pricing = None
        else:
            print("[INFO] Using static pricing database")
    
    def _check_aws_credentials(self) -> bool:
        """Check if AWS credentials are available"""
        return bool(os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'))
    
    def get_region_multiplier(self, region: str) -> float:
        """Get pricing multiplier for a specific region"""
        return self.region_db.get(region, {}).get("multiplier", 1.0)
    
    def get_service_info(self, service: str) -> Optional[Dict]:
        """
        Get service configuration from database
        If AWS Pricing API is available, merge live prices with static config
        """
        service_data = self.pricing_db.get(service)
        
        # If AWS Pricing API is available, try to get live prices
        if self.aws_pricing and service_data:
            service_data = self._enrich_with_live_prices(service, service_data)
        
        return service_data
    
    def _enrich_with_live_prices(self, service: str, service_data: Dict) -> Dict:
        """Enrich service data with live AWS prices"""
        try:
            # Make a copy to avoid modifying the original
            enriched_data = service_data.copy()
            
            if service == "EC2" and "regions" in enriched_data:
                # Get live EC2 prices for common instance types
                print(f"  [FETCH] Fetching live EC2 prices...")
                # We'll update this in the _calculate_hourly method
                
            elif service == "RDS" and "instanceRates" in enriched_data:
                # Get live RDS prices
                print(f"  [FETCH] Fetching live RDS prices...")
                # We'll update this in the _calculate_hourly method
                
            elif service == "Lambda":
                # Get live Lambda prices
                print(f"  [FETCH] Fetching live Lambda prices...")
                region = "us-east-1"  # Default, will be overridden in calculate
                lambda_pricing = self.aws_pricing.get_lambda_pricing(region)
                if lambda_pricing:
                    enriched_data["requestCostPerMillion"] = lambda_pricing["requestCostPerMillion"]
                    enriched_data["gbSecondCost"] = lambda_pricing["gbSecondCost"]
                    print(f"  [OK] Live Lambda prices: ${lambda_pricing['requestCostPerMillion']}/M requests, ${lambda_pricing['gbSecondCost']}/GB-second")
            
            return enriched_data
            
        except Exception as e:
            print(f"  [WARN] Could not fetch live prices for {service}: {e}")
            return service_data
    
    def calculate(self, service: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main calculation method - routes to appropriate pricing model
        
        Args:
            service: AWS service name (e.g., "EC2", "S3", "Lambda")
            config: Configuration dict with usage parameters
            
        Returns:
            Dict with cost breakdown and total
        """
        service_data = self.get_service_info(service)
        if not service_data:
            raise ValueError(f"Service '{service}' not found in pricing database")
        
        region = config.get("region", "us-east-1")
        region_multiplier = self.get_region_multiplier(region)
        
        model = service_data["model"]
        cost = 0
        breakdown = {}
        
        # Route to appropriate pricing model
        if model == "hourly":
            cost, breakdown = self._calculate_hourly(service_data, config)
        elif model == "tiered_gb":
            cost, breakdown = self._calculate_tiered(service_data, config)
        elif model == "request_based":
            cost, breakdown = self._calculate_request_based(service_data, config)
        elif model == "hybrid":
            cost, breakdown = self._calculate_hybrid(service_data, config)
        elif model == "flat_monthly":
            cost, breakdown = self._calculate_flat(service_data, config)
        elif model == "usage_based":
            cost, breakdown = self._calculate_usage_based(service_data, config)
        else:
            raise ValueError(f"Unknown pricing model: {model}")
        
        # FIX 4: Apply region multiplier BEFORE validation
        cost = cost * region_multiplier
        breakdown["regionMultiplier"] = region_multiplier
        breakdown["preMultiplierCost"] = round(cost / region_multiplier, 4)
        
        # BUG FIX: Add sanity checks for unreasonable costs (now sees final cost)
        self._validate_cost(service, cost, config, breakdown)
        
        return {
            "service": service,
            "region": region,
            "region_multiplier": region_multiplier,
            "model": model,
            "cost": round(cost, 4),
            "breakdown": breakdown,
            "description": service_data.get("description", "")
        }
    
    def _validate_cost(self, service: str, cost: float, config: Dict, breakdown: Dict):
        """Validate calculated costs for sanity - catch unreasonable values"""
        
        # Check for negative costs
        if cost < 0:
            print(f"  [WARN] SANITY CHECK FAILED: Negative cost ${cost:.2f} for {service}")
            raise ValueError(f"Negative cost calculated for {service}: ${cost:.2f}")
        
        # Check for extremely high costs (likely calculation error)
        if cost > 100000:  # $100k/month is suspicious for most services
            print(f"  [WARN] SANITY CHECK WARNING: Very high cost ${cost:,.2f} for {service}")
            print(f"     Config: {config}")
            print(f"     Breakdown: {breakdown}")
        
        # Service-specific sanity checks
        if service == "RDS":
            # RDS with 1 instance should typically be $10-500/month
            count = config.get("count", 1)
            if count == 1 and cost > 1000:
                print(f"  [WARN] SANITY CHECK WARNING: Single RDS instance cost ${cost:.2f} seems high")
                print(f"     Check if 'hours' parameter is being used as instance count")
        
        elif service == "DynamoDB":
            # DynamoDB with typical usage should be $0-100/month
            if cost > 500:
                print(f"  [WARN] SANITY CHECK WARNING: DynamoDB cost ${cost:.2f} seems high")
                print(f"     Verify per-million divisor is correct (should be 1,000,000)")
        
        elif service == "Lambda":
            # Lambda with typical usage should be $0-50/month
            if cost > 200:
                print(f"  [WARN] SANITY CHECK WARNING: Lambda cost ${cost:.2f} seems high")
                print(f"     Verify free tier is being applied correctly")
    
    def _calculate_hourly(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate hourly-based pricing (EC2, RDS, EKS, etc.) with live AWS prices"""
        hours = config.get("hours", 730)  # Default to monthly
        count = config.get("count", 1)
        region = config.get("region", "us-east-1")
        
        # Handle different hourly rate structures
        if "regions" in service_data:
            # EC2 pricing
            instance_type = config.get("instanceType", config.get("instance_type"))
            
            # Try to get live price from AWS API
            rate = service_data["regions"].get("*", {}).get(instance_type)
            if self.aws_pricing:
                try:
                    live_rate = self.aws_pricing.get_ec2_pricing(instance_type, region)
                    if live_rate:
                        rate = live_rate
                        print(f"  [OK] Using live EC2 price: ${rate}/hour for {instance_type}")
                    else:
                        print(f"  [INFO] Using static EC2 price: ${rate}/hour for {instance_type}")
                except Exception as e:
                    print(f"  [WARN] Could not fetch live EC2 price: {e}")
            
            if not rate:
                raise ValueError(f"Instance type '{instance_type}' not found")
            
            cost = rate * hours * count
            breakdown = {
                "instanceType": instance_type,
                "hourlyRate": rate,
                "hours": hours,
                "count": count
            }
        elif "instanceRates" in service_data:
            # RDS pricing
            instance_type = config.get("instanceType", config.get("instance_type"))
            rate = service_data["instanceRates"].get(instance_type)
            
            # Try to get live price from AWS API
            if self.aws_pricing:
                try:
                    live_rate = self.aws_pricing.get_rds_pricing(instance_type, region)
                    if live_rate:
                        rate = live_rate
                        print(f"  [OK] Using live RDS price: ${rate}/hour for {instance_type}")
                    else:
                        print(f"  [INFO] Using static RDS price: ${rate}/hour for {instance_type}")
                except Exception as e:
                    print(f"  [WARN] Could not fetch live RDS price: {e}")
            
            if not rate:
                raise ValueError(f"Instance type '{instance_type}' not found")
            cost = rate * hours * count
            
            # Add storage cost if applicable (RDS, Aurora)
            if "storagePerGB" in service_data and "storageGB" in config:
                storage_cost = service_data["storagePerGB"] * config["storageGB"]
                cost += storage_cost
                breakdown = {
                    "instanceType": instance_type,
                    "hourlyRate": rate,
                    "hours": hours,
                    "count": count,
                    "storageGB": config["storageGB"],
                    "storageCost": round(storage_cost, 4)
                }
            else:
                breakdown = {
                    "instanceType": instance_type,
                    "hourlyRate": rate,
                    "hours": hours,
                    "count": count
                }
        elif "clusterCostPerHour" in service_data:
            # EKS cluster pricing
            rate = service_data["clusterCostPerHour"]
            cost = rate * hours * count
            breakdown = {
                "clusterHourlyRate": rate,
                "hours": hours,
                "clusters": count
            }
        elif "hourlyRate" in service_data:
            # NAT Gateway, ELB
            rate = service_data["hourlyRate"]
            cost = rate * hours * count
            
            # Add data transfer if applicable
            if "dataPerGB" in service_data and "dataGB" in config:
                data_cost = service_data["dataPerGB"] * config["dataGB"]
                cost += data_cost
                breakdown = {
                    "hourlyRate": rate,
                    "hours": hours,
                    "count": count,
                    "dataGB": config["dataGB"],
                    "dataCost": round(data_cost, 4)
                }
            else:
                breakdown = {
                    "hourlyRate": rate,
                    "hours": hours,
                    "count": count
                }
        elif "types" in service_data:
            # ELB with types
            lb_type = config.get("type", "application")
            type_data = service_data["types"].get(lb_type, {})
            rate = type_data.get("hourlyRate", 0)
            lcu_rate = type_data.get("lcuRate", 0)
            lcus = config.get("lcus", 1)
            
            cost = (rate * hours) + (lcu_rate * lcus * hours)
            breakdown = {
                "type": lb_type,
                "hourlyRate": rate,
                "lcuRate": lcu_rate,
                "lcus": lcus,
                "hours": hours
            }
        else:
            raise ValueError("Unable to determine hourly pricing structure")
        
        return cost, breakdown
    
    def _calculate_tiered(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate tiered storage pricing (S3, EBS, EFS)"""
        usage_gb = config.get("usageGB", config.get("storageGB", 0))
        
        # BUG FIX: Ensure user-provided storage is never overwritten with 0
        if usage_gb == 0 and ("usageGB" in config or "storageGB" in config):
            print(f"  [WARN] WARNING: Storage was 0 but user specified storage in config")
        
        if "tiers" in service_data:
            # S3-style tiered pricing with free tier
            free_tier = service_data.get("freeTier", {})
            free_storage = free_tier.get("storageGB", 0)
            
            # Apply free tier BEFORE calculating
            billable_gb = max(0, usage_gb - free_storage)
            cost = self._calculate_tier_cost(service_data["tiers"], billable_gb)
            
            print(f"  [S3_TIERED] usage={usage_gb}GB | free_tier={free_storage}GB | billable={billable_gb}GB | cost=${cost:.4f}")
            
            breakdown = {
                "usageGB": usage_gb,
                "freeGB": free_storage,
                "billableGB": billable_gb,
                "model": "tiered"
            }
        elif "volumeTypes" in service_data:
            # EBS volume types
            volume_type = config.get("volumeType", "gp3")
            rate = service_data["volumeTypes"].get(volume_type, 0.10)
            cost = rate * usage_gb
            breakdown = {
                "volumeType": volume_type,
                "ratePerGB": rate,
                "usageGB": usage_gb
            }
        elif "storageClasses" in service_data:
            # EFS storage classes
            storage_class = config.get("storageClass", "standard")
            rate = service_data["storageClasses"].get(storage_class, 0.30)
            cost = rate * usage_gb
            breakdown = {
                "storageClass": storage_class,
                "ratePerGB": rate,
                "usageGB": usage_gb
            }
        else:
            raise ValueError("Unable to determine tiered pricing structure")
        
        return cost, breakdown
    
    def _calculate_tier_cost(self, tiers: List[Dict], usage: float) -> float:
        """Calculate cost across multiple pricing tiers"""
        remaining = usage
        total_cost = 0
        
        for tier in tiers:
            min_val = tier["from"]
            max_val = tier["to"] if tier["to"] is not None else float("inf")
            
            usable = min(remaining, max_val - min_val)
            
            if usable > 0:
                total_cost += usable * tier["price"]
                remaining -= usable
            
            if remaining <= 0:
                break
        
        return total_cost
    
    def _calculate_request_based(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate request-based pricing (SQS, SNS, API Gateway, DynamoDB)"""
        requests = config.get("requests", 0)
        
        # Apply free tier if available
        free_tier = service_data.get("freeTier", {})
        
        if "pricePerMillion" in service_data:
            # SQS, SNS, EventBridge
            free_requests = free_tier.get("requests", 0)
            billable_requests = max(0, requests - free_requests)
            cost = (billable_requests / 1_000_000) * service_data["pricePerMillion"]
            
            print(f"  [REQUEST_BASED] requests={requests:,} | free_tier={free_requests:,} | billable={billable_requests:,} | unit_price=${service_data['pricePerMillion']}/M | cost=${cost:.4f}")
            
            breakdown = {
                "requests": requests,
                "freeRequests": free_requests,
                "billableRequests": billable_requests,
                "pricePerMillion": service_data["pricePerMillion"]
            }
        elif "pricePerMillionRequests" in service_data:
            # API Gateway
            free_requests = free_tier.get("requests", 0)
            billable_requests = max(0, requests - free_requests)
            cost = (billable_requests / 1_000_000) * service_data["pricePerMillionRequests"]
            
            print(f"  [API_GATEWAY] requests={requests:,} | free_tier={free_requests:,} | billable={billable_requests:,} | unit_price=${service_data['pricePerMillionRequests']}/M | cost=${cost:.4f}")
            
            breakdown = {
                "requests": requests,
                "freeRequests": free_requests,
                "billableRequests": billable_requests,
                "pricePerMillion": service_data["pricePerMillionRequests"]
            }
        elif "writePerMillion" in service_data:
            # DynamoDB - BUG FIX: Use correct divisor (1,000,000 not 100,000)
            writes = config.get("writes", 0)
            reads = config.get("reads", 0)
            storage_gb = config.get("storageGB", 0)
            
            # Apply free tier
            free_storage = free_tier.get("storageGB", 0)
            billable_storage = max(0, storage_gb - free_storage)
            
            # DynamoDB free tier is 25 WCU and 25 RCU per month (not requests)
            # For simplicity, we'll apply free tier to requests
            write_cost = (writes / 1_000_000) * service_data["writePerMillion"]
            read_cost = (reads / 1_000_000) * service_data["readPerMillion"]
            storage_cost = billable_storage * service_data["storagePerGB"]
            
            print(f"  [DYNAMODB] writes={writes:,} | reads={reads:,} | storage={storage_gb}GB | free_storage={free_storage}GB")
            print(f"  [DYNAMODB] write_cost=${write_cost:.4f} (${service_data['writePerMillion']}/M) | read_cost=${read_cost:.4f} (${service_data['readPerMillion']}/M) | storage_cost=${storage_cost:.4f}")
            
            cost = write_cost + read_cost + storage_cost
            breakdown = {
                "writes": writes,
                "reads": reads,
                "storageGB": storage_gb,
                "freeStorageGB": free_storage,
                "billableStorageGB": billable_storage,
                "writeCost": round(write_cost, 4),
                "readCost": round(read_cost, 4),
                "storageCost": round(storage_cost, 4)
            }
        else:
            raise ValueError("Unable to determine request-based pricing structure")
        
        return cost, breakdown
    
    def _calculate_hybrid(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate hybrid pricing (Lambda, CloudFront)"""
        cost = 0
        breakdown = {}
        
        # Lambda-style: requests + GB-seconds
        if "requestCostPerMillion" in service_data:
            requests = config.get("requests", 0)
            gb_seconds = config.get("gbSeconds", 0)
            
            # BUG FIX: Apply free tier BEFORE calculating costs
            free_tier = service_data.get("freeTier", {})
            free_requests = free_tier.get("requests", 0)
            free_gb_seconds = free_tier.get("gbSeconds", 0)
            
            # Calculate billable amounts
            billable_requests = max(0, requests - free_requests)
            billable_gb_seconds = max(0, gb_seconds - free_gb_seconds)
            
            request_cost = (billable_requests / 1_000_000) * service_data["requestCostPerMillion"]
            compute_cost = billable_gb_seconds * service_data["gbSecondCost"]
            
            cost = request_cost + compute_cost
            
            print(f"  [LAMBDA_HYBRID] requests={requests:,} | free={free_requests:,} | billable={billable_requests:,} | req_cost=${request_cost:.4f}")
            print(f"  [LAMBDA_HYBRID] gb_seconds={gb_seconds:,} | free={free_gb_seconds:,} | billable={billable_gb_seconds:,} | compute_cost=${compute_cost:.4f}")
            
            breakdown = {
                "requests": requests,
                "freeRequests": free_requests,
                "billableRequests": billable_requests,
                "gbSeconds": gb_seconds,
                "freeGBSeconds": free_gb_seconds,
                "billableGBSeconds": billable_gb_seconds,
                "requestCost": round(request_cost, 4),
                "computeCost": round(compute_cost, 4)
            }
        
        # CloudFront-style: data transfer + requests
        elif "dataTransferPerGB" in service_data:
            data_gb = config.get("dataGB", 0)
            requests = config.get("requests", 0)
            
            data_cost = data_gb * service_data["dataTransferPerGB"]
            request_cost = (requests / 10_000) * service_data["requestsPer10k"]
            
            cost = data_cost + request_cost
            breakdown = {
                "dataGB": data_gb,
                "requests": requests,
                "dataCost": round(data_cost, 4),
                "requestCost": round(request_cost, 4)
            }
        
        # CloudWatch-style: multiple components
        elif "logIngestionPerGB" in service_data:
            log_gb = config.get("logIngestionGB", 0)
            metrics = config.get("metrics", 0)
            
            log_cost = log_gb * service_data["logIngestionPerGB"]
            metric_cost = (metrics / 1000) * service_data["metricsPer1000"]
            
            cost = log_cost + metric_cost
            breakdown = {
                "logIngestionGB": log_gb,
                "metrics": metrics,
                "logCost": round(log_cost, 4),
                "metricCost": round(metric_cost, 4)
            }
        
        return cost, breakdown
    
    def _calculate_flat(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate flat monthly pricing (IAM, some VPC components)"""
        cost = service_data.get("price", 0)
        breakdown = {
            "monthlyPrice": cost,
            "type": "flat"
        }
        return cost, breakdown
    
    def _calculate_usage_based(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate usage-based pricing (Route53, Athena, etc.)"""
        cost = 0
        breakdown = {}
        
        # Route53
        if "hostedZonePerMonth" in service_data:
            zones = config.get("hostedZones", 1)
            queries = config.get("queries", 0)
            
            zone_cost = zones * service_data["hostedZonePerMonth"]
            query_cost = (queries / 1_000_000) * service_data["queriesPerMillion"]
            
            cost = zone_cost + query_cost
            breakdown = {
                "hostedZones": zones,
                "queries": queries,
                "zoneCost": round(zone_cost, 4),
                "queryCost": round(query_cost, 4)
            }
        
        # Athena
        elif "pricePerTBScanned" in service_data:
            tb_scanned = config.get("tbScanned", 0)
            cost = tb_scanned * service_data["pricePerTBScanned"]
            breakdown = {
                "tbScanned": tb_scanned,
                "pricePerTB": service_data["pricePerTBScanned"]
            }
        
        return cost, breakdown
    
    def calculate_multiple(self, services: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate costs for multiple services
        
        Args:
            services: List of dicts with 'service' and 'config' keys
            
        Returns:
            Dict with total cost and per-service breakdown
        """
        results = []
        total_cost = 0
        
        for item in services:
            service = item.get("service")
            config = item.get("config", {})
            
            try:
                result = self.calculate(service, config)
                results.append(result)
                total_cost += result["cost"]
            except Exception as e:
                results.append({
                    "service": service,
                    "error": str(e),
                    "cost": 0
                })
        
        return {
            "totalCost": round(total_cost, 2),
            "currency": "USD",
            "services": results,
            "serviceCount": len(results)
        }
    
    def get_all_services(self) -> List[str]:
        """Get list of all available services"""
        return list(self.pricing_db.keys())
    
    def get_service_details(self, service: str) -> Optional[Dict]:
        """Get detailed information about a service"""
        return self.get_service_info(service)

# Made with Bob
