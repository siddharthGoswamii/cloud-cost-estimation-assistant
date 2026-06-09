"""
AWS-Style Pricing Database
Complete pricing data for 30+ AWS services with multi-region support
"""

# Region definitions with pricing multipliers
REGIONS = {
    "us-east-1": {"name": "N. Virginia", "multiplier": 1.0},
    "us-east-2": {"name": "Ohio", "multiplier": 1.0},
    "us-west-1": {"name": "N. California", "multiplier": 1.05},
    "us-west-2": {"name": "Oregon", "multiplier": 1.0},
    "eu-west-1": {"name": "Ireland", "multiplier": 1.12},
    "eu-central-1": {"name": "Frankfurt", "multiplier": 1.15},
    "ap-south-1": {"name": "Mumbai", "multiplier": 1.0},
    "ap-southeast-1": {"name": "Singapore", "multiplier": 1.08},
    "ap-northeast-1": {"name": "Tokyo", "multiplier": 1.10},
    "sa-east-1": {"name": "São Paulo", "multiplier": 1.2}
}

# Pricing model types
PRICING_MODELS = {
    "hourly": "EC2, RDS, NAT, LB",
    "tiered_gb": "S3, EBS, EFS",
    "request_based": "SQS, SNS, API Gateway",
    "hybrid": "Lambda, CloudFront",
    "flat_monthly": "CloudWatch, IAM, Route53"
}

# Complete AWS Services Pricing Database
PRICING_DB = {
    # ==================== COMPUTE ====================
    "EC2": {
        "service": "EC2",
        "category": "Compute",
        "model": "hourly",
        "description": "Elastic Compute Cloud - Virtual Servers",
        "regions": {
            "*": {
                "t3.micro": 0.0104,
                "t3.small": 0.0208,
                "t3.medium": 0.0416,
                "t3.large": 0.0832,
                "t3.xlarge": 0.1664,
                "t3.2xlarge": 0.3328,
                "m5.large": 0.096,
                "m5.xlarge": 0.192,
                "m5.2xlarge": 0.384,
                "c5.large": 0.085,
                "c5.xlarge": 0.17,
                "r5.large": 0.126,
                "r5.xlarge": 0.252
            }
        }
    },
    
    "Lambda": {
        "service": "Lambda",
        "category": "Compute",
        "model": "hybrid",
        "description": "Serverless Compute",
        "requestCostPerMillion": 0.20,
        "gbSecondCost": 0.00001667,
        "freeTier": {
            "requests": 1000000,
            "gbSeconds": 400000
        }
    },
    
    "ECS": {
        "service": "ECS",
        "category": "Compute",
        "model": "hourly",
        "description": "Elastic Container Service",
        "ratePerHourPerCPU": 0.04048,
        "ratePerHourPerGB": 0.004445
    },
    
    "EKS": {
        "service": "EKS",
        "category": "Compute",
        "model": "hourly",
        "description": "Elastic Kubernetes Service",
        "clusterCostPerHour": 0.10
    },
    
    "Fargate": {
        "service": "Fargate",
        "category": "Compute",
        "model": "hourly",
        "description": "Serverless Container Compute",
        "perVCPUHour": 0.04048,
        "perGBHour": 0.004445
    },
    
    # ==================== STORAGE ====================
    "S3": {
        "service": "S3",
        "category": "Storage",
        "model": "tiered_gb",
        "description": "Simple Storage Service",
        "tiers": [
            {"from": 0, "to": 50, "price": 0.023},
            {"from": 50, "to": 500, "price": 0.022},
            {"from": 500, "to": None, "price": 0.021}
        ],
        "requestPricing": {
            "putPerThousand": 0.005,
            "getPerThousand": 0.0004
        }
    },
    
    "EBS": {
        "service": "EBS",
        "category": "Storage",
        "model": "tiered_gb",
        "description": "Elastic Block Storage",
        "volumeTypes": {
            "gp3": 0.08,
            "gp2": 0.10,
            "io2": 0.125,
            "st1": 0.045,
            "sc1": 0.015
        },
        "snapshotPerGB": 0.05
    },
    
    "EFS": {
        "service": "EFS",
        "category": "Storage",
        "model": "tiered_gb",
        "description": "Elastic File System",
        "storageClasses": {
            "standard": 0.30,
            "infrequentAccess": 0.025
        }
    },
    
    "Glacier": {
        "service": "Glacier",
        "category": "Storage",
        "model": "tiered_gb",
        "description": "Archive Storage",
        "tiers": [
            {"from": 0, "to": None, "price": 0.004, "class": "instant"},
            {"from": 0, "to": None, "price": 0.0036, "class": "flexible"},
            {"from": 0, "to": None, "price": 0.00099, "class": "deep"}
        ]
    },
    
    # ==================== DATABASE ====================
    "RDS": {
        "service": "RDS",
        "category": "Database",
        "model": "hourly",
        "description": "Relational Database Service",
        "instanceRates": {
            "db.t3.micro": 0.017,
            "db.t3.small": 0.034,
            "db.t3.medium": 0.068,
            "db.t3.large": 0.136,
            "db.m5.large": 0.192,
            "db.m5.xlarge": 0.384,
            "db.r5.large": 0.24,
            "db.r5.xlarge": 0.48
        },
        "storagePerGB": 0.115,
        "iopsPerMonth": 0.10
    },
    
    "DynamoDB": {
        "service": "DynamoDB",
        "category": "Database",
        "model": "request_based",
        "description": "NoSQL Database",
        "writePerMillion": 1.25,
        "readPerMillion": 0.25,
        "storagePerGB": 0.25,
        "freeTier": {
            "writeUnits": 25,
            "readUnits": 25,
            "storageGB": 25
        }
    },
    
    "Aurora": {
        "service": "Aurora",
        "category": "Database",
        "model": "hourly",
        "description": "High-Performance Relational DB",
        "instanceRates": {
            "db.t3.medium": 0.082,
            "db.r5.large": 0.29,
            "db.r5.xlarge": 0.58
        },
        "storagePerGB": 0.10,
        "ioPerMillion": 0.20
    },
    
    "ElastiCache": {
        "service": "ElastiCache",
        "category": "Database",
        "model": "hourly",
        "description": "In-Memory Cache (Redis/Memcached)",
        "instanceRates": {
            "cache.t3.micro": 0.017,
            "cache.t3.small": 0.034,
            "cache.m5.large": 0.170,
            "cache.r5.large": 0.226
        }
    },
    
    "Redshift": {
        "service": "Redshift",
        "category": "Database",
        "model": "hourly",
        "description": "Data Warehouse",
        "nodeRates": {
            "dc2.large": 0.25,
            "dc2.8xlarge": 4.80,
            "ra3.xlplus": 1.086,
            "ra3.4xlarge": 3.26
        }
    },
    
    # ==================== NETWORKING ====================
    "CloudFront": {
        "service": "CloudFront",
        "category": "Networking",
        "model": "hybrid",
        "description": "Content Delivery Network",
        "dataTransferPerGB": 0.085,
        "requestsPer10k": 0.0075,
        "freeTier": {
            "dataTransferGB": 1000,
            "requests": 10000000
        }
    },
    
    "API Gateway": {
        "service": "API Gateway",
        "category": "Networking",
        "model": "request_based",
        "description": "API Management Service",
        "pricePerMillionRequests": 3.50,
        "websocketPerMillion": 1.00,
        "freeTier": {
            "requests": 1000000
        }
    },
    
    "ELB": {
        "service": "ELB",
        "category": "Networking",
        "model": "hourly",
        "description": "Elastic Load Balancer",
        "types": {
            "application": {
                "hourlyRate": 0.0225,
                "lcuRate": 0.008
            },
            "network": {
                "hourlyRate": 0.0225,
                "lcuRate": 0.006
            }
        }
    },
    
    "NAT Gateway": {
        "service": "NAT Gateway",
        "category": "Networking",
        "model": "hourly",
        "description": "Network Address Translation",
        "hourlyRate": 0.045,
        "dataPerGB": 0.045
    },
    
    "VPC": {
        "service": "VPC",
        "category": "Networking",
        "model": "flat_monthly",
        "description": "Virtual Private Cloud",
        "price": 0.0,
        "endpoints": {
            "interfacePerHour": 0.01,
            "gatewayPerHour": 0.0
        }
    },
    
    "Route53": {
        "service": "Route53",
        "category": "Networking",
        "model": "usage_based",
        "description": "DNS Service",
        "hostedZonePerMonth": 0.50,
        "queriesPerMillion": 0.40
    },
    
    # ==================== MESSAGING ====================
    "SQS": {
        "service": "SQS",
        "category": "Messaging",
        "model": "request_based",
        "description": "Simple Queue Service",
        "pricePerMillion": 0.40,
        "freeTier": {
            "requests": 1000000
        }
    },
    
    "SNS": {
        "service": "SNS",
        "category": "Messaging",
        "model": "request_based",
        "description": "Simple Notification Service",
        "pricePerMillion": 0.50,
        "emailPer100k": 2.00,
        "smsPer100": 0.75
    },
    
    "EventBridge": {
        "service": "EventBridge",
        "category": "Messaging",
        "model": "request_based",
        "description": "Event Bus Service",
        "pricePerMillion": 1.00,
        "customEventBusPerMillion": 1.00
    },
    
    "Kinesis": {
        "service": "Kinesis",
        "category": "Messaging",
        "model": "hourly",
        "description": "Real-time Data Streaming",
        "shardHourRate": 0.015,
        "putPayloadUnitPerMillion": 0.014
    },
    
    # ==================== MONITORING & MANAGEMENT ====================
    "CloudWatch": {
        "service": "CloudWatch",
        "category": "Monitoring",
        "model": "hybrid",
        "description": "Monitoring and Observability",
        "logIngestionPerGB": 0.50,
        "logStoragePerGB": 0.03,
        "metricsPer1000": 0.30,
        "dashboards": 3.00,
        "alarms": 0.10
    },
    
    "IAM": {
        "service": "IAM",
        "category": "Security",
        "model": "flat_monthly",
        "description": "Identity and Access Management",
        "price": 0.0
    },
    
    "KMS": {
        "service": "KMS",
        "category": "Security",
        "model": "request_based",
        "description": "Key Management Service",
        "keyPerMonth": 1.00,
        "requestsPer10000": 0.03
    },
    
    "CloudTrail": {
        "service": "CloudTrail",
        "category": "Monitoring",
        "model": "usage_based",
        "description": "API Activity Logging",
        "eventsPer100k": 2.00,
        "firstTrailFree": True
    },
    
    "Systems Manager": {
        "service": "Systems Manager",
        "category": "Management",
        "model": "usage_based",
        "description": "Operations Management",
        "parameterStorageAdvanced": 0.05,
        "automationPerStep": 0.002
    },
    
    # ==================== ANALYTICS ====================
    "Athena": {
        "service": "Athena",
        "category": "Analytics",
        "model": "usage_based",
        "description": "Serverless Query Service",
        "pricePerTBScanned": 5.00
    },
    
    "EMR": {
        "service": "EMR",
        "category": "Analytics",
        "model": "hourly",
        "description": "Big Data Processing",
        "ec2PriceMultiplier": 0.27
    },
    
    "Glue": {
        "service": "Glue",
        "category": "Analytics",
        "model": "usage_based",
        "description": "ETL Service",
        "dpuHourRate": 0.44
    },
    
    # ==================== MACHINE LEARNING ====================
    "SageMaker": {
        "service": "SageMaker",
        "category": "Machine Learning",
        "model": "hourly",
        "description": "ML Platform",
        "instanceRates": {
            "ml.t3.medium": 0.05,
            "ml.m5.xlarge": 0.23,
            "ml.p3.2xlarge": 3.825
        }
    },
    
    "Rekognition": {
        "service": "Rekognition",
        "category": "Machine Learning",
        "model": "request_based",
        "description": "Image and Video Analysis",
        "imageAnalysisPer1000": 1.00,
        "videoAnalysisPerMinute": 0.10
    }
}

# Service categories for organization
SERVICE_CATEGORIES = {
    "Compute": ["EC2", "Lambda", "ECS", "EKS", "Fargate"],
    "Storage": ["S3", "EBS", "EFS", "Glacier"],
    "Database": ["RDS", "DynamoDB", "Aurora", "ElastiCache", "Redshift"],
    "Networking": ["CloudFront", "API Gateway", "ELB", "NAT Gateway", "VPC", "Route53"],
    "Messaging": ["SQS", "SNS", "EventBridge", "Kinesis"],
    "Monitoring": ["CloudWatch", "CloudTrail"],
    "Security": ["IAM", "KMS"],
    "Management": ["Systems Manager"],
    "Analytics": ["Athena", "EMR", "Glue"],
    "Machine Learning": ["SageMaker", "Rekognition"]
}

# Made with Bob
