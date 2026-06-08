"""
AWS-Style Pricing Engine
Production-grade pricing calculation engine supporting multiple pricing models
"""

from typing import Dict, Any, Optional, List
from pricing_database import PRICING_DB, REGIONS


class PricingEngine:
    """
    Core pricing engine that mimics AWS billing logic
    Supports: hourly, tiered_gb, request_based, hybrid, flat_monthly models
    """
    
    def __init__(self, pricing_db: Dict = None, region_db: Dict = None):
        self.pricing_db = pricing_db or PRICING_DB
        self.region_db = region_db or REGIONS
    
    def get_region_multiplier(self, region: str) -> float:
        """Get pricing multiplier for a specific region"""
        return self.region_db.get(region, {}).get("multiplier", 1.0)
    
    def get_service_info(self, service: str) -> Optional[Dict]:
        """Get service configuration from database"""
        return self.pricing_db.get(service)
    
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
        
        # Apply region multiplier
        cost = cost * region_multiplier
        
        return {
            "service": service,
            "region": region,
            "region_multiplier": region_multiplier,
            "model": model,
            "cost": round(cost, 4),
            "breakdown": breakdown,
            "description": service_data.get("description", "")
        }
    
    def _calculate_hourly(self, service_data: Dict, config: Dict) -> tuple:
        """Calculate hourly-based pricing (EC2, RDS, EKS, etc.)"""
        hours = config.get("hours", 730)  # Default to monthly
        count = config.get("count", 1)
        
        # Handle different hourly rate structures
        if "regions" in service_data:
            instance_type = config.get("instanceType", config.get("instance_type"))
            rate = service_data["regions"].get("*", {}).get(instance_type)
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
            instance_type = config.get("instanceType", config.get("instance_type"))
            rate = service_data["instanceRates"].get(instance_type)
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
        
        if "tiers" in service_data:
            # S3-style tiered pricing
            cost = self._calculate_tier_cost(service_data["tiers"], usage_gb)
            breakdown = {
                "usageGB": usage_gb,
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
        
        if "pricePerMillion" in service_data:
            cost = (requests / 1_000_000) * service_data["pricePerMillion"]
            breakdown = {
                "requests": requests,
                "pricePerMillion": service_data["pricePerMillion"]
            }
        elif "pricePerMillionRequests" in service_data:
            cost = (requests / 1_000_000) * service_data["pricePerMillionRequests"]
            breakdown = {
                "requests": requests,
                "pricePerMillion": service_data["pricePerMillionRequests"]
            }
        elif "writePerMillion" in service_data:
            # DynamoDB
            writes = config.get("writes", requests)
            reads = config.get("reads", 0)
            storage_gb = config.get("storageGB", 0)
            
            write_cost = (writes / 1_000_000) * service_data["writePerMillion"]
            read_cost = (reads / 1_000_000) * service_data["readPerMillion"]
            storage_cost = storage_gb * service_data["storagePerGB"]
            
            cost = write_cost + read_cost + storage_cost
            breakdown = {
                "writes": writes,
                "reads": reads,
                "storageGB": storage_gb,
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
            
            request_cost = (requests / 1_000_000) * service_data["requestCostPerMillion"]
            compute_cost = gb_seconds * service_data["gbSecondCost"]
            
            cost = request_cost + compute_cost
            breakdown = {
                "requests": requests,
                "gbSeconds": gb_seconds,
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
