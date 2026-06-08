"""
AI-Powered Service Detection from Architecture Diagrams
Automatically identifies cloud services and suggests configurations
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DetectedService:
    """Represents a detected service from diagram"""
    service_code: str
    service_name: str
    confidence: float
    suggested_config: Dict[str, Any]
    reasoning: str


class ServiceDetector:
    """
    Detects AWS services from architecture diagram descriptions or text
    Uses pattern matching and keyword detection
    """
    
    # Service detection patterns
    SERVICE_PATTERNS = {
        "EC2": {
            "keywords": ["ec2", "virtual machine", "vm", "instance", "server", "compute instance"],
            "default_config": {
                "instanceType": "t3.medium",
                "hours": 730,
                "count": 1,
                "region": "us-east-1"
            },
            "reasoning": "Virtual server for compute workloads"
        },
        "S3": {
            "keywords": ["s3", "storage", "bucket", "object storage", "file storage", "blob"],
            "default_config": {
                "usageGB": 100,
                "region": "us-east-1"
            },
            "reasoning": "Object storage for files and data"
        },
        "RDS": {
            "keywords": ["rds", "database", "mysql", "postgres", "postgresql", "sql", "relational"],
            "default_config": {
                "instanceType": "db.t3.medium",
                "hours": 730,
                "storageGB": 100,
                "region": "us-east-1"
            },
            "reasoning": "Managed relational database"
        },
        "DynamoDB": {
            "keywords": ["dynamodb", "nosql", "document db", "key-value"],
            "default_config": {
                "writes": 1000000,
                "reads": 5000000,
                "storageGB": 25,
                "region": "us-east-1"
            },
            "reasoning": "NoSQL database for high-scale applications"
        },
        "Lambda": {
            "keywords": ["lambda", "serverless", "function", "faas"],
            "default_config": {
                "requests": 1000000,
                "gbSeconds": 12800,
                "region": "us-east-1"
            },
            "reasoning": "Serverless compute for event-driven workloads"
        },
        "CloudFront": {
            "keywords": ["cloudfront", "cdn", "content delivery", "edge"],
            "default_config": {
                "dataGB": 1000,
                "requests": 10000000,
                "region": "us-east-1"
            },
            "reasoning": "Content delivery network for global distribution"
        },
        "API Gateway": {
            "keywords": ["api gateway", "api", "rest api", "http api"],
            "default_config": {
                "requests": 1000000,
                "region": "us-east-1"
            },
            "reasoning": "Managed API service"
        },
        "ELB": {
            "keywords": ["load balancer", "elb", "alb", "nlb", "application load balancer"],
            "default_config": {
                "type": "application",
                "hours": 730,
                "lcus": 1,
                "region": "us-east-1"
            },
            "reasoning": "Load balancer for distributing traffic"
        },
        "NAT Gateway": {
            "keywords": ["nat gateway", "nat", "network address translation"],
            "default_config": {
                "hours": 730,
                "dataGB": 100,
                "region": "us-east-1"
            },
            "reasoning": "NAT gateway for private subnet internet access"
        },
        "SQS": {
            "keywords": ["sqs", "queue", "message queue"],
            "default_config": {
                "requests": 1000000,
                "region": "us-east-1"
            },
            "reasoning": "Message queue for asynchronous processing"
        },
        "SNS": {
            "keywords": ["sns", "notification", "pub/sub", "topic"],
            "default_config": {
                "requests": 1000000,
                "region": "us-east-1"
            },
            "reasoning": "Notification service for pub/sub messaging"
        },
        "CloudWatch": {
            "keywords": ["cloudwatch", "monitoring", "logs", "metrics"],
            "default_config": {
                "logIngestionGB": 10,
                "metrics": 1000,
                "region": "us-east-1"
            },
            "reasoning": "Monitoring and logging service"
        },
        "Route53": {
            "keywords": ["route53", "dns", "domain"],
            "default_config": {
                "hostedZones": 1,
                "queries": 1000000,
                "region": "us-east-1"
            },
            "reasoning": "DNS and domain management"
        },
        "ECS": {
            "keywords": ["ecs", "container", "docker", "fargate"],
            "default_config": {
                "ratePerHourPerCPU": 0.04048,
                "hours": 730,
                "region": "us-east-1"
            },
            "reasoning": "Container orchestration service"
        },
        "EKS": {
            "keywords": ["eks", "kubernetes", "k8s"],
            "default_config": {
                "hours": 730,
                "count": 1,
                "region": "us-east-1"
            },
            "reasoning": "Managed Kubernetes service"
        },
        "Aurora": {
            "keywords": ["aurora", "aurora mysql", "aurora postgres"],
            "default_config": {
                "instanceType": "db.r5.large",
                "hours": 730,
                "storageGB": 100,
                "region": "us-east-1"
            },
            "reasoning": "High-performance managed database"
        },
        "ElastiCache": {
            "keywords": ["elasticache", "redis", "memcached", "cache"],
            "default_config": {
                "instanceType": "cache.t3.small",
                "hours": 730,
                "region": "us-east-1"
            },
            "reasoning": "In-memory caching service"
        },
        "Kinesis": {
            "keywords": ["kinesis", "streaming", "data stream"],
            "default_config": {
                "hours": 730,
                "region": "us-east-1"
            },
            "reasoning": "Real-time data streaming"
        },
        "EventBridge": {
            "keywords": ["eventbridge", "event bus", "events"],
            "default_config": {
                "requests": 1000000,
                "region": "us-east-1"
            },
            "reasoning": "Event-driven architecture service"
        },
        "VPC": {
            "keywords": ["vpc", "virtual private cloud", "network"],
            "default_config": {
                "region": "us-east-1"
            },
            "reasoning": "Virtual private cloud networking"
        }
    }
    
    # Architecture pattern detection
    ARCHITECTURE_PATTERNS = {
        "web_application": {
            "indicators": ["web", "frontend", "backend", "api"],
            "typical_services": ["EC2", "ELB", "RDS", "S3", "CloudFront"]
        },
        "serverless": {
            "indicators": ["serverless", "lambda", "api gateway"],
            "typical_services": ["Lambda", "API Gateway", "DynamoDB", "S3"]
        },
        "microservices": {
            "indicators": ["microservice", "container", "kubernetes"],
            "typical_services": ["ECS", "EKS", "RDS", "ElastiCache", "SQS"]
        },
        "data_pipeline": {
            "indicators": ["pipeline", "etl", "analytics"],
            "typical_services": ["Kinesis", "Lambda", "S3", "Athena", "Glue"]
        }
    }
    
    def detect_services(self, diagram_text: str) -> List[DetectedService]:
        """
        Detect services from diagram description or text
        
        Args:
            diagram_text: Text description of architecture diagram
            
        Returns:
            List of detected services with configurations
        """
        diagram_text_lower = diagram_text.lower()
        detected = []
        
        for service_code, pattern in self.SERVICE_PATTERNS.items():
            confidence = self._calculate_confidence(diagram_text_lower, pattern["keywords"])
            
            if confidence > 0.3:  # Threshold for detection
                detected.append(DetectedService(
                    service_code=service_code,
                    service_name=service_code,
                    confidence=confidence,
                    suggested_config=pattern["default_config"].copy(),
                    reasoning=pattern["reasoning"]
                ))
        
        # Sort by confidence
        detected.sort(key=lambda x: x.confidence, reverse=True)
        
        return detected
    
    def _calculate_confidence(self, text: str, keywords: List[str]) -> float:
        """Calculate confidence score based on keyword matches"""
        matches = sum(1 for keyword in keywords if keyword in text)
        return min(matches / len(keywords) * 2, 1.0)  # Cap at 1.0
    
    def detect_architecture_pattern(self, diagram_text: str) -> Optional[str]:
        """Detect overall architecture pattern"""
        diagram_text_lower = diagram_text.lower()
        
        for pattern_name, pattern_data in self.ARCHITECTURE_PATTERNS.items():
            matches = sum(1 for indicator in pattern_data["indicators"] 
                         if indicator in diagram_text_lower)
            if matches >= 2:
                return pattern_name
        
        return None
    
    def suggest_services_for_pattern(self, pattern: str) -> List[str]:
        """Suggest typical services for an architecture pattern"""
        if pattern in self.ARCHITECTURE_PATTERNS:
            return self.ARCHITECTURE_PATTERNS[pattern]["typical_services"]
        return []
    
    def adjust_config_based_on_scale(
        self, 
        service_code: str, 
        config: Dict[str, Any], 
        scale: str = "small"
    ) -> Dict[str, Any]:
        """
        Adjust configuration based on scale (small, medium, large)
        
        Args:
            service_code: AWS service code
            config: Base configuration
            scale: "small", "medium", or "large"
            
        Returns:
            Adjusted configuration
        """
        adjusted = config.copy()
        
        scale_multipliers = {
            "small": 1,
            "medium": 3,
            "large": 10
        }
        
        multiplier = scale_multipliers.get(scale, 1)
        
        # Adjust instance types based on scale
        if service_code == "EC2":
            instance_map = {
                "small": "t3.small",
                "medium": "t3.large",
                "large": "m5.xlarge"
            }
            adjusted["instanceType"] = instance_map.get(scale, "t3.medium")
            adjusted["count"] = multiplier
            
        elif service_code == "RDS":
            instance_map = {
                "small": "db.t3.small",
                "medium": "db.t3.large",
                "large": "db.m5.xlarge"
            }
            adjusted["instanceType"] = instance_map.get(scale, "db.t3.medium")
            adjusted["storageGB"] = 100 * multiplier
            
        elif service_code == "S3":
            adjusted["usageGB"] = 100 * multiplier
            
        elif service_code == "Lambda":
            adjusted["requests"] = 1000000 * multiplier
            adjusted["gbSeconds"] = 12800 * multiplier
            
        elif service_code == "DynamoDB":
            adjusted["writes"] = 1000000 * multiplier
            adjusted["reads"] = 5000000 * multiplier
            adjusted["storageGB"] = 25 * multiplier
        
        return adjusted
    
    def parse_diagram_components(self, diagram_text: str) -> Dict[str, Any]:
        """
        Parse diagram text to extract components and relationships
        
        Returns structured information about the architecture
        """
        result = {
            "detected_services": [],
            "architecture_pattern": None,
            "estimated_scale": "small",
            "regions": [],
            "components": []
        }
        
        # Detect services
        detected_services = self.detect_services(diagram_text)
        result["detected_services"] = [
            {
                "service": s.service_code,
                "confidence": s.confidence,
                "config": s.suggested_config,
                "reasoning": s.reasoning
            }
            for s in detected_services
        ]
        
        # Detect architecture pattern
        result["architecture_pattern"] = self.detect_architecture_pattern(diagram_text)
        
        # Estimate scale based on keywords
        if any(word in diagram_text.lower() for word in ["large", "enterprise", "high traffic"]):
            result["estimated_scale"] = "large"
        elif any(word in diagram_text.lower() for word in ["medium", "production"]):
            result["estimated_scale"] = "medium"
        else:
            result["estimated_scale"] = "small"
        
        # Detect regions
        region_keywords = {
            "us-east-1": ["virginia", "us-east"],
            "us-west-2": ["oregon", "us-west"],
            "eu-west-1": ["ireland", "europe"],
            "ap-south-1": ["mumbai", "india"],
            "ap-northeast-1": ["tokyo", "japan"]
        }
        
        for region, keywords in region_keywords.items():
            if any(kw in diagram_text.lower() for kw in keywords):
                result["regions"].append(region)
        
        if not result["regions"]:
            result["regions"] = ["us-east-1"]  # Default
        
        return result


class ConversationalAgent:
    """
    Conversational interface for updating configurations
    Allows natural language updates to service configurations
    """
    
    def __init__(self):
        self.context = {}
    
    def parse_update_request(self, user_input: str, current_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse natural language update request
        
        Examples:
        - "increase EC2 instances to 5"
        - "change to t3.large"
        - "add 500GB storage"
        - "use Mumbai region"
        """
        updated_config = current_config.copy()
        user_input_lower = user_input.lower()
        
        # Instance count updates
        count_match = re.search(r'(\d+)\s*(instance|server|vm)', user_input_lower)
        if count_match:
            updated_config["count"] = int(count_match.group(1))
        
        # Instance type updates
        instance_match = re.search(r'(t3\.\w+|m5\.\w+|c5\.\w+|r5\.\w+|db\.t3\.\w+|db\.m5\.\w+)', user_input_lower)
        if instance_match:
            updated_config["instanceType"] = instance_match.group(1)
        
        # Storage updates
        storage_match = re.search(r'(\d+)\s*(gb|tb)', user_input_lower)
        if storage_match:
            amount = int(storage_match.group(1))
            unit = storage_match.group(2)
            if unit == "tb":
                amount *= 1024
            updated_config["storageGB"] = amount
            updated_config["usageGB"] = amount
        
        # Region updates
        region_map = {
            "virginia": "us-east-1",
            "ohio": "us-east-2",
            "oregon": "us-west-2",
            "california": "us-west-1",
            "ireland": "eu-west-1",
            "frankfurt": "eu-central-1",
            "mumbai": "ap-south-1",
            "singapore": "ap-southeast-1",
            "tokyo": "ap-northeast-1"
        }
        
        for location, region_code in region_map.items():
            if location in user_input_lower:
                updated_config["region"] = region_code
                break
        
        return updated_config
    
    def generate_response(self, service: str, old_config: Dict, new_config: Dict) -> str:
        """Generate human-readable response about configuration changes"""
        changes = []
        
        for key in new_config:
            if key in old_config and old_config[key] != new_config[key]:
                changes.append(f"{key}: {old_config[key]} → {new_config[key]}")
        
        if changes:
            return f"Updated {service} configuration:\n" + "\n".join(f"  • {c}" for c in changes)
        else:
            return "No changes detected in the configuration."

# Made with Bob
