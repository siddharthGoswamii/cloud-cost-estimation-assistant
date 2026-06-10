"""
Stateful Conversational Cost Estimation Agent
Maintains full session context with multi-turn conversation memory
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum


class CloudProvider(Enum):
    AWS = "AWS"
    AZURE = "Azure"
    GCP = "GCP"
    MULTI_CLOUD = "Multi-Cloud"


class Scale(Enum):
    SMALL = "Small"
    MEDIUM = "Medium"
    LARGE = "Large"
    ENTERPRISE = "Enterprise"


@dataclass
class ServiceConfig:
    """Individual service configuration with full state"""
    id: str
    name: str
    instance_type: str
    quantity: int
    hours_per_day: float = 24.0
    days_per_month: int = 30
    storage_gb: Optional[float] = None
    additional_params: Dict[str, Any] = field(default_factory=dict)
    assumptions: List[str] = field(default_factory=list)
    unit_price: float = 0.0
    monthly_cost: float = 0.0
    updated_at: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


@dataclass
class SessionState:
    """Complete session state for conversational agent"""
    session_id: str
    region: str = "ap-south-1"
    cloud_provider: str = "AWS"
    scale: str = "Medium"
    services: List[ServiceConfig] = field(default_factory=list)
    total_monthly_cost: float = 0.0
    total_annual_cost: float = 0.0
    last_updated_service: Optional[str] = None
    conversation_turn: int = 0
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self):
        return {
            "session_id": self.session_id,
            "region": self.region,
            "cloud_provider": self.cloud_provider,
            "scale": self.scale,
            "services": [s.to_dict() for s in self.services],
            "total_monthly_cost": self.total_monthly_cost,
            "total_annual_cost": self.total_annual_cost,
            "last_updated_service": self.last_updated_service,
            "conversation_turn": self.conversation_turn,
            "conversation_history": self.conversation_history,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }


class ConversationalCostAgent:
    """
    Expert Cloud Cost Estimation Agent with multi-turn conversational memory
    """
    
    # Default assumptions by cloud provider
    DEFAULT_ASSUMPTIONS = {
        "AWS": {
            "EC2": {"instance_type": "t3.medium", "storage": "30GB gp2"},
            "RDS": {"instance_type": "db.t3.micro", "storage": "20GB gp2", "deployment": "Single-AZ"},
            "S3": {"storage_class": "Standard", "storage": "100GB"},
            "Lambda": {"memory": "128MB", "pricing": "pay-per-use"},
            "CloudFront": {"distribution": "Standard"},
            "ELB": {"type": "Application Load Balancer"},
            "DynamoDB": {"capacity": "On-Demand"},
            "ElastiCache": {"node_type": "cache.t3.micro"},
        },
        "Azure": {
            "Azure SQL": {"tier": "S2 (50 DTUs)", "storage": "32GB", "redundancy": "LRS"},
            "Azure VM": {"size": "Standard_B2s", "disk": "Standard HDD"},
            "Azure Blob Storage": {"redundancy": "LRS", "tier": "Hot", "storage": "100GB"},
            "Azure App Service": {"tier": "B1", "os": "Linux"},
            "Azure Load Balancer": {"sku": "Basic"},
            "Azure CDN": {"tier": "Standard Microsoft"},
        },
        "GCP": {
            "Compute Engine": {"machine_type": "e2-medium", "disk": "standard persistent disk"},
            "Cloud SQL": {"tier": "db-f1-micro", "storage": "10GB SSD"},
            "Cloud Storage": {"class": "Standard", "location": "regional"},
        }
    }
    
    # Region mappings
    DEFAULT_REGIONS = {
        "AWS": "ap-south-1",
        "Azure": "Central India",
        "GCP": "asia-south1"
    }
    
    def __init__(self, pricing_engine=None):
        self.pricing_engine = pricing_engine
        self.sessions: Dict[str, SessionState] = {}
        
    def create_session(self, session_id: str) -> SessionState:
        """Create a new session"""
        session = SessionState(session_id=session_id)
        self.sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[SessionState]:
        """Get existing session"""
        return self.sessions.get(session_id)
    
    def detect_trigger(self, user_input: str, session: SessionState) -> str:
        """Detect which trigger pattern the user input matches"""
        user_input_lower = user_input.lower().strip()
        
        # TRIGGER 2: Must explicitly ask about assumptions for a known service
        # Require: "assumption" + a service name already in session
        if any(word in user_input_lower for word in ["assumption", "assume", "why did you"]):
            if session.services:  # Only route to T2 if we have services already
                service_names = [s.name.lower() for s in session.services]
                if any(svc in user_input_lower for svc in service_names):
                    return "TRIGGER_2_ASSUMPTIONS"
            return "TRIGGER_2_ASSUMPTIONS" if "assumption" in user_input_lower else "TRIGGER_1_INITIAL"
        
        # TRIGGER 3: Must have existing services AND explicit update intent
        # Require: update keywords + a service name OR a config parameter name
        update_intent_phrases = [
            "update the", "change the", "modify the", "change it to",
            "update it to", "increase the", "decrease the", "reduce the",
            "set it to", "instead of", "switch to", "upgrade to", "downgrade to"
        ]
        config_param_words = ["dtu", "instance", "storage", "gb", "tb", "hours",
                              "requests", "memory", "count", "quantity", "tier", "sku"]
        
        has_update_phrase = any(phrase in user_input_lower for phrase in update_intent_phrases)
        has_config_param = any(param in user_input_lower for param in config_param_words)
        has_existing_services = len(session.services) > 0
        
        if has_update_phrase and has_existing_services and has_config_param:
            return "TRIGGER_3_UPDATE"
        
        # TRIGGER 4: Explicit summary/total request — must be short and direct
        # A long message with "summary" in it is likely still an architecture description
        total_phrases = ["total cost", "show total", "final cost", "overall cost",
                         "show all costs", "cost summary", "recalculate all",
                         "what's the total", "what is the total"]
        if any(phrase in user_input_lower for phrase in total_phrases):
            if len(user_input_lower.split()) < 20:  # Short messages only
                return "TRIGGER_4_TOTAL"
        
        # TRIGGER 5: What-if analysis — must start with "what if" or "what would"
        if user_input_lower.startswith(("what if", "what would", "if i")):
            return "TRIGGER_5_WHATIF"
        
        # Additional check: if optimize/cheaper used alone (not in an architecture desc)
        if any(phrase in user_input_lower for phrase in ["optimize costs", "reduce costs",
                                                           "make it cheaper", "cost optimization"]):
            if len(user_input_lower.split()) < 15:
                return "TRIGGER_5_WHATIF"
        
        # Default: treat as new architecture description
        return "TRIGGER_1_INITIAL"
    
    def parse_architecture_description(self, description: str, session: SessionState) -> List[ServiceConfig]:
        """Parse architecture description and extract services"""
        services = []
        service_id = 0
        
        # Detect cloud provider
        if "azure" in description.lower():
            session.cloud_provider = "Azure"
        elif "gcp" in description.lower() or "google cloud" in description.lower():
            session.cloud_provider = "GCP"
        else:
            session.cloud_provider = "AWS"
        
        # Detect region
        region_patterns = {
            "AWS": r"(us-east-1|us-west-2|eu-west-1|ap-south-1|ap-northeast-1)",
            "Azure": r"(Central India|East US|West Europe|Southeast Asia)",
            "GCP": r"(asia-south1|us-central1|europe-west1)"
        }
        
        region_match = re.search(region_patterns.get(session.cloud_provider, ""), description, re.IGNORECASE)
        if region_match:
            session.region = region_match.group(1)
        else:
            session.region = self.DEFAULT_REGIONS[session.cloud_provider]
        
        # Detect scale
        if any(word in description.lower() for word in ["enterprise", "large scale", "high scale"]):
            session.scale = "Enterprise"
        elif any(word in description.lower() for word in ["large", "production"]):
            session.scale = "Large"
        elif any(word in description.lower() for word in ["medium", "startup"]):
            session.scale = "Medium"
        elif any(word in description.lower() for word in ["small", "dev", "test", "development"]):
            session.scale = "Small"
        
        # Service detection patterns
        service_patterns = self._get_service_patterns(session.cloud_provider)
        
        # For better context, use sentence-based splitting instead of just commas
        # This preserves more context for each service
        sentences = re.split(r'\.\s+', description)
        
        print(f"\n[DEBUG] Service Detection:")
        print(f"  Description length: {len(description)} chars")
        print(f"  Sentences: {len(sentences)}")
        print(f"  Patterns to match: {list(service_patterns.keys())}")
        
        # Track which services we've already found to avoid duplicates
        found_services = set()
        
        for service_name, pattern in service_patterns.items():
            if service_name in found_services:
                continue
            
            # Find the sentence(s) most relevant to this service
            # Collect all sentences that mention this service for better context
            relevant_text = []
            for sentence in sentences:
                if re.search(pattern, sentence, re.IGNORECASE):
                    relevant_text.append(sentence)
            
            if not relevant_text:
                # Try full description as fallback
                if re.search(pattern, description, re.IGNORECASE):
                    relevant_text = [description]
            
            if relevant_text:
                # Join relevant sentences to get full context
                best_chunk = '. '.join(relevant_text)
                service_id += 1
                config = self._extract_service_config(
                    service_name,
                    best_chunk,  # Pass the relevant context
                    session,
                    f"svc_{service_id}"
                )
                services.append(config)
                found_services.add(service_name)
                print(f"  [MATCH] {service_name} detected in context: '{best_chunk[:100]}'")
        
        print(f"\n[DEBUG] Total services detected: {len(services)}")
        print(f"  Services: {[s.name for s in services]}\n")
        
        return services
    
    def _get_service_patterns(self, cloud_provider: str) -> Dict[str, str]:
        """Get regex patterns for service detection - more flexible patterns"""
        if cloud_provider == "AWS":
            return {
                "EC2": r"(?:EC2|compute nodes?|instances?|servers?|virtual machines?|VMs?|c\d+i\.)",
                "RDS": r"(?:RDS|database|DB|MySQL|PostgreSQL|MariaDB|Oracle|SQL Server|Aurora|db\.m\d+g\.|db\.t\d+\.|db\.r\d+\.)",
                "S3": r"(?:S3|bucket|object storage|blob storage|standard bucket)\b",
                "Glacier": r"(?:Glacier|S3 Glacier|archive|cold storage)\b",
                "Lambda": r"(?:Lambda|serverless functions?|function invocations?)\b",
                "DynamoDB": r"(?:DynamoDB|NoSQL|document database)\b",
                "CloudFront": r"(?:CloudFront|CDN|content delivery)\b",
                "ELB": r"(?:Load Balancer|ELB|ALB|NLB|Application Load Balancer|Network Load Balancer)\b",
                "ElastiCache": r"(?:ElastiCache|Redis|Memcached|cache cluster|cache\.m\d+g\.)",
                "API Gateway": r"(?:API Gateway|REST API|HTTP API|WebSocket API)\b",
                "Kinesis": r"(?:Kinesis|data stream|streaming data)\b",
                "SNS": r"(?:SNS|Simple Notification|notification service|pub.?sub)\b",
                "SQS": r"(?:SQS|Simple Queue|message queue|queue service)\b",
                "NAT Gateway": r"(?:NAT Gateway|NAT instance)\b",
            }
        # Add Azure and GCP patterns as needed
        return {}
    
    def _extract_service_config(
        self,
        service_name: str,
        match_text: str,
        session: SessionState,
        service_id: str
    ) -> ServiceConfig:
        """Extract detailed configuration from matched text"""
        
        # Get default assumptions
        defaults = self.DEFAULT_ASSUMPTIONS.get(session.cloud_provider, {}).get(service_name, {})
        
        # Determine default instance type based on service
        default_instance_type = defaults.get("instance_type", "t3.medium")
        if service_name == "ElastiCache":
            default_instance_type = "cache.t3.micro"
        elif service_name == "RDS":
            default_instance_type = "db.t3.micro"
        elif service_name in ["S3", "Glacier", "CloudFront", "SNS", "SQS", "NAT Gateway", "ELB", "DynamoDB", "Lambda", "API Gateway"]:
            default_instance_type = "N/A"  # These services don't use instance types
        
        # Extract quantity - IMPROVED: Look for number BEFORE service name
        quantity = 1  # Default to 1
        # Pattern 1: "5 EC2" or "3 instances"
        quantity_match = re.search(rf'(\d+)\s+(?:{service_name}|instances?|servers?|nodes?|clusters?)', match_text, re.IGNORECASE)
        if quantity_match:
            quantity = int(quantity_match.group(1))
        # Pattern 2: "EC2 x5" or "instances x3"
        if quantity == 1:
            quantity_match = re.search(rf'(?:{service_name}|instances?|servers?)\s*[x×]\s*(\d+)', match_text, re.IGNORECASE)
            if quantity_match:
                quantity = int(quantity_match.group(1))
        
        # Build configuration
        config = ServiceConfig(
            id=service_id,
            name=service_name,
            instance_type=default_instance_type,
            quantity=quantity,
            hours_per_day=24.0,
            days_per_month=30,
            additional_params={"region": session.region}
        )
        
        # Extract instance type - SERVICE-SPECIFIC patterns to avoid cross-contamination
        instance_match = None
        if service_name == "RDS":
            # Only match db.* instance types for RDS
            instance_match = re.search(r'(db\.[a-z0-9]+\.\w+)', match_text, re.IGNORECASE)
        elif service_name == "ElastiCache":
            # Only match cache.* instance types for ElastiCache
            instance_match = re.search(r'(cache\.[a-z0-9]+\.\w+)', match_text, re.IGNORECASE)
        elif service_name == "EC2":
            # Only match EC2 instance types (not db.* or cache.*)
            instance_match = re.search(r'(t[23]\.\w+|m[456g]\.\w+|c[456]i?\.\w+|r[456]\.\w+)(?!\.)', match_text, re.IGNORECASE)
        else:
            # General pattern for other services
            instance_match = re.search(
                r'(t[23]\.\w+|m[456g]\.\w+|c[456]i?\.\w+|r[456]\.\w+)',
                match_text, re.IGNORECASE
            )
        if instance_match:
            config.instance_type = instance_match.group(0).lower()
            config.assumptions.append(f"Instance type explicitly specified: {config.instance_type}")
        else:
            if config.instance_type != "N/A":
                config.assumptions.append(f"[ASSUMPTION] Instance type: {config.instance_type} (default for {session.scale} scale)")
        
        # Extract storage - IMPROVED: Better patterns for various formats
        # For S3 and Glacier, look for storage amounts in the specific context
        if service_name == "S3":
            # For S3: look for "holding XTB" or "XTB of data" (but not "for cold/archive")
            storage_patterns = [
                r'holding\s+(\d+(?:\.\d+)?)\s*(TB|GB)\s+of\s+data',  # "holding 31TB of data"
                r'(\d+(?:\.\d+)?)\s*(TB|GB)\s+of\s+data(?!\s*,\s*while)',  # "31TB of data"
            ]
            
            for pattern in storage_patterns:
                storage_match = re.search(pattern, match_text, re.IGNORECASE)
                if storage_match:
                    storage_value = float(storage_match.group(1))
                    storage_unit = storage_match.group(2).upper()
                    config.storage_gb = storage_value * 1000 if storage_unit == "TB" else storage_value
                    config.assumptions.append(f"Storage explicitly specified: {config.storage_gb}GB")
                    break
        elif service_name == "Glacier":
            # For Glacier: look for "XTB for cold/archive" or "with XTB for"
            storage_patterns = [
                r'with\s+(\d+(?:\.\d+)?)\s*(TB|GB)\s+for',  # "with 10TB for"
                r'(\d+(?:\.\d+)?)\s*(TB|GB)\s+for\s+(?:cold|archive|backup)',  # "10TB for cold"
            ]
            
            for pattern in storage_patterns:
                storage_match = re.search(pattern, match_text, re.IGNORECASE)
                if storage_match:
                    storage_value = float(storage_match.group(1))
                    storage_unit = storage_match.group(2).upper()
                    config.storage_gb = storage_value * 1000 if storage_unit == "TB" else storage_value
                    config.assumptions.append(f"Storage explicitly specified: {config.storage_gb}GB")
                    break
            
            # For Glacier, detect storage class
            if service_name == "Glacier":
                if "flexible" in match_text.lower():
                    config.additional_params["storageClass"] = "flexible"
                elif "instant" in match_text.lower():
                    config.additional_params["storageClass"] = "instant"
                elif "deep" in match_text.lower():
                    config.additional_params["storageClass"] = "deep"
                else:
                    config.additional_params["storageClass"] = "flexible"  # Default
                config.assumptions.append(f"Glacier storage class: {config.additional_params['storageClass']}")
        elif service_name == "RDS":
            # For RDS, look for storage with gp2/gp3/io1 context
            storage_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(TB|GB)\s+(?:gp[23]|io[12]|standard)',
                match_text, re.IGNORECASE
            )
            if storage_match:
                storage_value = float(storage_match.group(1))
                storage_unit = storage_match.group(2).upper()
                config.storage_gb = storage_value * 1000 if storage_unit == "TB" else storage_value
                config.assumptions.append(f"Storage explicitly specified: {config.storage_gb}GB")
            elif "storage" in defaults:
                config.assumptions.append(f"[ASSUMPTION] Storage: {defaults['storage']} (default)")
        else:
            # For other services (EBS, etc.)
            storage_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(TB|GB)(?:\s+(?:of\s+)?(?:storage|store|disk|volume|capacity))?',
                match_text, re.IGNORECASE
            )
            # Also try: "storage of 100GB" or "with 2TB storage"
            if not storage_match:
                storage_match = re.search(
                    r'(?:with|of|has)\s+(\d+(?:\.\d+)?)\s*(TB|GB)\s+(?:storage|store|disk|volume|capacity|data)',
                    match_text, re.IGNORECASE
                )
            
            if storage_match:
                storage_value = float(storage_match.group(1))
                storage_unit = storage_match.group(2).upper()
                config.storage_gb = storage_value * 1000 if storage_unit == "TB" else storage_value
                config.assumptions.append(f"Storage explicitly specified: {config.storage_gb}GB")
        
        # Extract hours if present
        hours_match = re.search(r'(\d+)\s*hours?', match_text, re.IGNORECASE)
        if hours_match:
            total_hours = int(hours_match.group(1))
            config.hours_per_day = total_hours / 30  # Convert monthly to daily
            config.assumptions.append(f"Usage hours explicitly specified: {total_hours} hours/month")
        else:
            if service_name in ["EC2", "RDS", "ElastiCache", "NAT Gateway"]:
                config.assumptions.append(f"[ASSUMPTION] Usage: 730 hours/month (24/7 operation)")
        
        # Extract request counts for API-based services
        if service_name in ["SNS", "SQS", "API Gateway"]:
            million_match = re.search(r'(\d+)\s*(?:million|M)', match_text, re.IGNORECASE)
            if million_match:
                config.additional_params["requests"] = int(million_match.group(1)) * 1000000
                config.assumptions.append(f"Requests explicitly specified: {million_match.group(1)} million/month")
        
        # FIX 2: Extract both requests and GB-seconds for Lambda separately
        if service_name == "Lambda":
            # Extract requests (look specifically for request/invocation context)
            req_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(?:million|M)\s*(?:requests?|invocations?|calls?)',
                match_text, re.IGNORECASE
            )
            if req_match:
                config.additional_params["requests"] = int(float(req_match.group(1)) * 1_000_000)
                config.assumptions.append(
                    f"Requests explicitly specified: {req_match.group(1)} million/month"
                )
            
            # Extract GB-seconds (look specifically for GB-seconds context)
            gbs_match = re.search(
                r'(\d+(?:,\d+)?(?:\.\d+)?)\s*(?:GB[-\s]?seconds?|GBs)',
                match_text, re.IGNORECASE
            )
            if gbs_match:
                gb_seconds = float(gbs_match.group(1).replace(',', ''))
                config.additional_params["gbSeconds"] = gb_seconds
                config.assumptions.append(
                    f"GB-seconds explicitly specified: {gb_seconds:,.0f}/month"
                )
            else:
                config.assumptions.append(
                    "[ASSUMPTION] GB-seconds: not specified, defaulting to 0 (free tier covers 400,000)"
                )
        
        # FIX 3: Extract read/write requests for DynamoDB with more precise regex
        if service_name == "DynamoDB":
            # Extract storage
            dynamo_storage_match = re.search(
                r'(\d+(?:\.\d+)?)\s*GB\s*(?:storage|store)?',
                match_text, re.IGNORECASE
            )
            if dynamo_storage_match:
                config.storage_gb = float(dynamo_storage_match.group(1))
                config.additional_params["storageGB"] = config.storage_gb
            
            # Extract reads - handle "5 million read" and "5M read request units"
            read_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(?:million|M)\s*(?:read\s*(?:request\s*)?(?:units?)?|RRU|RCU)',
                match_text, re.IGNORECASE
            )
            if read_match:
                reads = int(float(read_match.group(1)) * 1_000_000)
                config.additional_params["reads"] = reads
                config.assumptions.append(f"Read requests explicitly specified: {read_match.group(1)}M/month")
            
            # Extract writes - handle "5 million write" and "5M write request units"
            write_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(?:million|M)\s*(?:write\s*(?:request\s*)?(?:units?)?|WRU|WCU)',
                match_text, re.IGNORECASE
            )
            if write_match:
                writes = int(float(write_match.group(1)) * 1_000_000)
                config.additional_params["writes"] = writes
                config.assumptions.append(f"Write requests explicitly specified: {write_match.group(1)}M/month")
        
        # Extract data transfer for CloudFront and NAT Gateway - IMPROVED
        if service_name in ["CloudFront", "NAT Gateway"]:
            # Look for data transfer amount - multiple patterns
            data_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(TB|GB)\s+(?:data\s+)?(?:transfer|out|egress|bandwidth)',
                match_text, re.IGNORECASE
            )
            if not data_match:
                data_match = re.search(
                    r'(?:transfer|handling|serving)\s+(\d+(?:\.\d+)?)\s*(TB|GB)',
                    match_text, re.IGNORECASE
                )
            if data_match:
                data_value = float(data_match.group(1))
                data_unit = data_match.group(2).upper()
                data_gb = data_value * 1000 if data_unit == "TB" else data_value
                config.additional_params["dataGB"] = data_gb
                config.assumptions.append(f"Data transfer explicitly specified: {data_gb}GB")
        
        # Add general assumptions
        config.assumptions.append(f"[ASSUMPTION] Region: {session.region}")
        config.assumptions.append(f"[ASSUMPTION] No reserved instance pricing applied")
        
        return config
    
    def calculate_service_cost(self, service: ServiceConfig, session: SessionState) -> float:
        """Calculate cost for a single service"""
        if self.pricing_engine:
            try:
                # FIX 5: Build config more carefully with explicit key precedence
                # Start with additional_params as base (user-extracted values)
                config = dict(service.additional_params) if service.additional_params else {}
                
                # Apply standard fields — DO NOT overwrite user-extracted values
                config.setdefault("region", session.region)
                config.setdefault("instanceType", service.instance_type)
                config.setdefault("hours", int(service.hours_per_day * service.days_per_month))
                config.setdefault("count", service.quantity)
                
                # FIX 1B: Storage - always include, never let it be missing
                if service.storage_gb is not None and service.storage_gb > 0:
                    config["storageGB"] = service.storage_gb
                    config["usageGB"] = service.storage_gb  # Some services use usageGB key
                elif service.name not in ["EC2", "Lambda", "API Gateway", "SNS", "SQS", "CloudFront", "NAT Gateway", "ELB"]:
                    # Only set default 0 for services that don't typically use storage
                    config.setdefault("storageGB", 0)
                    config.setdefault("usageGB", 0)
                
                print(f"\n=== PRICING CALCULATION DEBUG ===")
                print(f"Service: {service.name}")
                print(f"Config sent to engine: {config}")
                
                result = self.pricing_engine.calculate(service.name, config)
                service.monthly_cost = result["cost"]
                
                print(f"Result: ${service.monthly_cost:.2f}/month")
                print(f"Breakdown: {result.get('breakdown', {})}")
                print(f"=================================\n")
                
                return service.monthly_cost
            except Exception as e:
                print(f"[ERROR] Pricing calculation error for {service.name}: {e}")
                import traceback
                traceback.print_exc()
                service.assumptions.append(f"[WARN] [PRICE UNAVAILABLE] Error: {str(e)}")
                service.monthly_cost = 0.0
                return 0.0
        
        # Fallback: use estimated pricing
        print(f"[WARN] No pricing engine available for {service.name}")
        service.monthly_cost = 0.0
        return 0.0
    
    def format_trigger1_response(self, session: SessionState) -> str:
        """Format response for initial architecture analysis"""
        response = f"""---
## 🏗️ Detected Architecture — {session.region}

### 📋 Services Identified
| # | Service | Type/SKU | Qty | Usage | Storage | Monthly Cost |
|---|---------|----------|-----|-------|---------|--------------|
"""
        
        for idx, service in enumerate(session.services, 1):
            usage_hours = int(service.hours_per_day * service.days_per_month)
            storage = f"{service.storage_gb}GB" if service.storage_gb else "N/A"
            response += f"| {idx} | {service.name} | {service.instance_type} | {service.quantity} | {usage_hours}h | {storage} | ${service.monthly_cost:.2f} |\n"
        
        response += f"\n### 🔍 Assumptions Made\n"
        for service in session.services:
            response += f"\n**{service.name}:**\n"
            for assumption in service.assumptions:
                response += f"- {assumption}\n"
        
        response += f"""
### 💰 Total Cost Estimate
| Period  | Cost       |
|---------|------------|
| Monthly | ${session.total_monthly_cost:.2f} |
| Annual  | ${session.total_annual_cost:.2f} |

> [INFO] Prices based on {session.region} as of {datetime.now().strftime('%Y-%m-%d')}. Subject to change.

💬 Want me to adjust any assumptions?
---"""
        
        return response
    
    def format_trigger2_response(self, service_name: str, session: SessionState) -> str:
        """Format response for assumptions query"""
        service = next((s for s in session.services if s.name.lower() == service_name.lower()), None)
        
        if not service:
            return f"[ERROR] Service '{service_name}' not found in current session."
        
        response = f"""---
## 🔍 Assumptions for {service.name}

| Parameter        | Assumed Value     | Reason                          |
|------------------|-------------------|---------------------------------|
| Instance Type    | {service.instance_type} | Default for {session.scale} scale |
| Quantity         | {service.quantity} | Detected from description |
| Usage Hours      | {int(service.hours_per_day * service.days_per_month)}h/month | 24/7 operation assumed |
"""
        
        if service.storage_gb:
            response += f"| Storage          | {service.storage_gb}GB | Detected from description |\n"
        
        response += f"| Region           | {session.region} | Default or detected region |\n"
        
        response += f"\n### All Assumptions:\n"
        for assumption in service.assumptions:
            response += f"- {assumption}\n"
        
        response += f"\n💬 Want to update any of these values?\n---"
        
        return response
    
    def process_message(self, session_id: str, user_message: str, image_data: Optional[str] = None) -> str:
        """Main entry point for processing user messages"""
        
        # Get or create session
        session = self.get_session(session_id)
        if not session:
            session = self.create_session(session_id)
        
        # Increment conversation turn
        session.conversation_turn += 1
        session.conversation_history.append({
            "turn": session.conversation_turn,
            "user": user_message,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Detect trigger
        trigger = self.detect_trigger(user_message, session)
        
        # Process based on trigger
        if trigger == "TRIGGER_1_INITIAL":
            # Parse architecture
            services = self.parse_architecture_description(user_message, session)
            session.services = services
            
            # Calculate costs
            for service in session.services:
                self.calculate_service_cost(service, session)
            
            session.total_monthly_cost = sum(s.monthly_cost for s in session.services)
            session.total_annual_cost = session.total_monthly_cost * 12
            
            response = self.format_trigger1_response(session)
            
        elif trigger == "TRIGGER_2_ASSUMPTIONS":
            # Extract service name from query
            service_name = self._extract_service_name_from_query(user_message, session)
            response = self.format_trigger2_response(service_name, session)
            
        elif trigger == "TRIGGER_3_UPDATE":
            response = self._handle_update_trigger(user_message, session)
            
        elif trigger == "TRIGGER_4_TOTAL":
            response = self._handle_total_trigger(session)
            
        elif trigger == "TRIGGER_5_WHATIF":
            response = self._handle_whatif_trigger(user_message, session)
            
        else:
            response = "I'm not sure how to help with that. Can you rephrase?"
        
        # Save response to history
        session.conversation_history[-1]["assistant"] = response
        session.updated_at = datetime.utcnow().isoformat()
        
        return response
    
    def _extract_service_name_from_query(self, query: str, session: SessionState) -> str:
        """Extract service name from user query"""
        for service in session.services:
            if service.name.lower() in query.lower():
                return service.name
        return session.services[0].name if session.services else "Unknown"
    
    def _handle_update_trigger(self, user_message: str, session: SessionState) -> str:
        """Handle configuration update requests"""
        if not session.services:
            return "No services detected yet. Please describe your architecture first."
        
        user_lower = user_message.lower()
        
        # Step 1: Find which service the user wants to update
        target_service = None
        for service in session.services:
            if service.name.lower() in user_lower:
                target_service = service
                break
        
        if not target_service:
            # Could not identify target service — ask for clarification
            service_list = ", ".join([s.name for s in session.services])
            return (f"Which service would you like to update? "
                    f"Current services: {service_list}")
        
        # Step 2: Extract the new parameter values from the message
        old_cost = target_service.monthly_cost
        
        # Update quantity
        qty_match = re.search(r'(\d+)\s*(?:instances?|nodes?|servers?|replicas?)',
                               user_lower)
        if qty_match:
            target_service.quantity = int(qty_match.group(1))
        
        # Update instance type
        instance_match = re.search(
            r'(t[23]\.\w+|m[456]\.\w+|c[456]\.\w+|r[456]\.\w+|db\.\w+|cache\.\w+)',
            user_lower)
        if instance_match:
            target_service.instance_type = instance_match.group(1)
        
        # Update storage
        storage_match = re.search(r'(\d+(?:\.\d+)?)\s*(TB|GB)\s*(?:storage|disk)?',
                                   user_lower, re.IGNORECASE)
        if storage_match:
            val = float(storage_match.group(1))
            unit = storage_match.group(2).upper()
            target_service.storage_gb = val * 1000 if unit == "TB" else val
            target_service.additional_params["storageGB"] = target_service.storage_gb
        
        # Update hours/usage
        hours_match = re.search(r'(\d+)\s*hours?\s*(?:per\s*day|a\s*day|/day)?',
                                 user_lower)
        if hours_match:
            hrs = int(hours_match.group(1))
            # If "per day" context or value <= 24, treat as hours/day
            if hrs <= 24:
                target_service.hours_per_day = float(hrs)
            else:
                # Treat as hours/month
                target_service.hours_per_day = hrs / 30
        
        # Update requests for Lambda/API Gateway/DynamoDB
        req_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:million|M)\s*(?:requests?|invocations?)',
                               user_lower, re.IGNORECASE)
        if req_match:
            target_service.additional_params["requests"] = int(
                float(req_match.group(1)) * 1_000_000
            )
        
        # Step 3: Recalculate ONLY the updated service
        self.calculate_service_cost(target_service, session)
        new_cost = target_service.monthly_cost
        
        # Step 4: Update session totals
        session.total_monthly_cost = sum(s.monthly_cost for s in session.services)
        session.total_annual_cost = session.total_monthly_cost * 12
        session.last_updated_service = target_service.name
        
        # Step 5: Format response showing only the change
        diff = new_cost - old_cost
        diff_sign = "+" if diff >= 0 else ""
        
        return f"""---
## ✏️ Updated: {target_service.name}

| Parameter     | New Value              |
|---------------|------------------------|
| Instance Type | {target_service.instance_type} |
| Quantity      | {target_service.quantity} |
| Storage       | {f"{target_service.storage_gb}GB" if target_service.storage_gb else "N/A"} |
| Hours/Month   | {int(target_service.hours_per_day * target_service.days_per_month)}h |

| Cost          | Amount                 |
|---------------|------------------------|
| Previous Cost | ${old_cost:.2f}/month  |
| New Cost      | ${new_cost:.2f}/month  |
| Difference    | {diff_sign}${diff:.2f}/month |

**Updated Total: ${session.total_monthly_cost:.2f}/month**

> All other services remain unchanged.
💬 Want the full updated cost summary?
---"""
    
    def _handle_total_trigger(self, session: SessionState) -> str:
        """Handle total cost summary requests"""
        if not session.services:
            return "[ERROR] No services detected yet. Please describe your architecture first."
        
        response = f"""---
## 💰 Complete Cost Summary — {session.region}

### Full Service Breakdown
| # | Service     | Config          | Monthly Cost |
|---|-------------|-----------------|--------------|
"""
        
        for idx, service in enumerate(session.services, 1):
            config_str = f"{service.instance_type} x{service.quantity}"
            if service.storage_gb:
                config_str += f", {service.storage_gb}GB"
            response += f"| {idx} | {service.name} | {config_str} | ${service.monthly_cost:.2f} |\n"
        
        response += f"""
### Grand Total
| Period       | Cost        |
|--------------|-------------|
| Monthly      | ${session.total_monthly_cost:.2f} |
| Annual       | ${session.total_annual_cost:.2f} |
| 3-Year       | ${session.total_monthly_cost * 36:.2f} |

💬 Want to optimize any of these services?
---"""
        
        return response
    
    def _handle_whatif_trigger(self, user_message: str, session: SessionState) -> str:
        """Handle what-if analysis requests"""
        if not session.services:
            return "[ERROR] No services detected yet. Please describe your architecture first."
        
        response = f"""---
## [FETCH] What-If Analysis

I can help you explore cost optimization scenarios!

**Current Configuration:**
"""
        
        for service in session.services:
            response += f"- {service.name}: {service.quantity}x {service.instance_type} = ${service.monthly_cost:.2f}/month\n"
        
        response += f"""
**Total Monthly Cost:** ${session.total_monthly_cost:.2f}

**Try asking:**
- "What if I use t3.medium instead of t3.large?"
- "What if I reduce instances from 5 to 3?"
- "What if I move to a cheaper region?"

💬 Ask me a specific "what if" question!
---"""
        
        return response

# Made with Bob
