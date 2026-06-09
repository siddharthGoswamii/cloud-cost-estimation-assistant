# Conversational Cloud Cost Agent - Complete Guide

## 🤖 Overview

The Conversational Cloud Cost Agent is an advanced, stateful AI system that maintains full session context across multiple conversation turns. It analyzes cloud architectures and provides detailed cost estimates while remembering every service, configuration, and assumption throughout the conversation.

## ✨ Key Features

### 1. **Stateful Session Memory**
- Maintains complete conversation history
- Remembers all detected services and configurations
- Tracks every assumption made
- Supports multi-turn conversations without context loss

### 2. **Intelligent Trigger Detection**
The agent automatically detects 5 types of user intents:

- **TRIGGER 1: Initial Architecture Analysis** - Detects services from descriptions
- **TRIGGER 2: Assumptions Query** - Shows assumptions for specific services
- **TRIGGER 3: Configuration Updates** - Modifies specific service parameters
- **TRIGGER 4: Total Cost Summary** - Provides complete cost breakdown
- **TRIGGER 5: What-If Analysis** - Performs cost optimization scenarios

### 3. **Multi-Cloud Support**
- AWS (primary)
- Azure
- Google Cloud Platform (GCP)
- Multi-cloud architectures

### 4. **Transparent Pricing**
- Shows all assumptions clearly labeled as [ASSUMPTION]
- Displays unit prices and calculations
- Flags unavailable prices with ⚠️
- Provides detailed cost breakdowns

## 🚀 Getting Started

### Prerequisites
```bash
# Ensure the FastAPI server is running
python main.py
```

### Access the Agent
Open `conversational_agent.html` in your browser or navigate to:
```
http://localhost:8000/conversational_agent.html
```

## 📝 Usage Examples

### Example 1: Initial Architecture Description
```
User: "I have an e-commerce platform in us-east-1 with 5 EC2 t3.large instances 
running 730 hours/month, RDS MySQL db.t3.large with 500GB storage, S3 with 2TB 
of data, and CloudFront with 1TB data transfer."

Agent: [Detects all services, applies assumptions, calculates costs, 
shows detailed breakdown with monthly and annual totals]
```

### Example 2: Query Assumptions
```
User: "What assumptions did you make for EC2?"

Agent: [Shows table of all assumptions for EC2 including instance type, 
usage hours, region, redundancy, etc. with reasoning for each]
```

### Example 3: Update Configuration
```
User: "Update EC2 to use 10 instances instead of 5"

Agent: [Updates ONLY EC2 configuration, recalculates cost, shows 
previous vs new values, updates total cost]
```

### Example 4: Total Cost Summary
```
User: "Give me the total cost"

Agent: [Shows complete service breakdown table with all current 
configurations, highlights updated services with ✏️, displays 
monthly/annual/3-year totals]
```

### Example 5: What-If Analysis
```
User: "What if I change EC2 instances to t3.medium?"

Agent: [Runs hypothetical calculation WITHOUT modifying session, 
shows side-by-side comparison, calculates savings, asks if user 
wants to apply the change]
```

## 🏗️ Architecture

### Core Components

#### 1. **SessionState** (conversational_cost_agent.py)
```python
@dataclass
class SessionState:
    session_id: str
    region: str
    cloud_provider: str
    scale: str
    services: List[ServiceConfig]
    total_monthly_cost: float
    total_annual_cost: float
    conversation_turn: int
    conversation_history: List[Dict]
```

#### 2. **ServiceConfig**
```python
@dataclass
class ServiceConfig:
    id: str
    name: str
    instance_type: str
    quantity: int
    hours_per_day: float
    storage_gb: Optional[float]
    assumptions: List[str]
    unit_price: float
    monthly_cost: float
```

#### 3. **ConversationalCostAgent**
Main agent class with methods:
- `create_session()` - Initialize new session
- `detect_trigger()` - Identify user intent
- `parse_architecture_description()` - Extract services from text
- `calculate_service_cost()` - Calculate individual service costs
- `process_message()` - Main message processing pipeline

### API Endpoints

#### POST /chat
Main conversational endpoint
```json
{
  "session_id": "session_123",
  "message": "Your architecture description or question",
  "image_data": "base64_encoded_image (optional)"
}
```

Response:
```json
{
  "success": true,
  "response": "Formatted agent response",
  "session_state": {
    "session_id": "session_123",
    "conversation_turn": 1,
    "total_monthly_cost": 1234.56,
    "total_annual_cost": 14814.72,
    "services_count": 5,
    "region": "us-east-1",
    "cloud_provider": "AWS",
    "scale": "Medium"
  }
}
```

#### GET /session/{session_id}
Retrieve complete session state
```json
{
  "success": true,
  "session": {
    "session_id": "session_123",
    "services": [...],
    "conversation_history": [...],
    "total_monthly_cost": 1234.56
  }
}
```

#### DELETE /session/{session_id}
Clear/reset a session

#### GET /sessions
List all active sessions

## 🎯 Default Assumptions

### AWS Services
- **EC2**: t3.medium, On-Demand, no Reserved Instance discount
- **RDS**: db.t3.micro, Single-AZ, gp2 storage, 20GB
- **S3**: Standard storage class, 100GB
- **Lambda**: 128MB memory, pay-per-use
- **CloudFront**: Standard distribution
- **ELB**: Application Load Balancer
- **DynamoDB**: On-Demand capacity
- **ElastiCache**: cache.t3.micro

### Azure Services
- **Azure SQL**: S2 tier (50 DTUs), 32GB, LRS backup
- **Azure VM**: Standard_B2s, Standard HDD
- **Azure Blob Storage**: LRS redundancy, Hot tier, 100GB
- **Azure App Service**: B1 tier, Linux
- **Azure Load Balancer**: Basic SKU
- **Azure CDN**: Standard Microsoft tier

### GCP Services
- **Compute Engine**: e2-medium, standard persistent disk
- **Cloud SQL**: db-f1-micro, SSD, 10GB
- **Cloud Storage**: Standard class, regional

### General Assumptions
- **Usage**: 730 hours/month (24/7) unless specified
- **Redundancy**: Single instance (no HA/Multi-AZ) unless diagram shows otherwise
- **Region**: ap-south-1 (AWS) / Central India (Azure) / asia-south1 (GCP)
- **Scale Mapping**: 
  - Small = dev/test
  - Medium = startup
  - Large = SMB
  - Enterprise = high-scale

## 📊 Response Formats

### Trigger 1: Initial Architecture
```
---
## 🏗️ Detected Architecture — us-east-1

### 📋 Services Identified
| # | Service | Type/SKU | Qty | Usage | Storage | Monthly Cost |
|---|---------|----------|-----|-------|---------|--------------|
| 1 | EC2     | t3.large | 5   | 730h  | N/A     | $XXX.XX      |

### 🔍 Assumptions Made
**EC2:**
- [ASSUMPTION] Instance type: t3.large (default for Medium scale)
- [ASSUMPTION] Usage: 730 hours/month (24/7 operation)
- [ASSUMPTION] Region: us-east-1

### 💰 Total Cost Estimate
| Period  | Cost       |
|---------|------------|
| Monthly | $XXX.XX    |
| Annual  | $XXX.XX    |

💬 Want me to adjust any assumptions?
---
```

### Trigger 2: Assumptions Query
```
---
## 🔍 Assumptions for EC2

| Parameter     | Assumed Value | Reason                    |
|---------------|---------------|---------------------------|
| Instance Type | t3.large      | Default for Medium scale  |
| Usage Hours   | 730h/month    | 24/7 operation assumed    |
| Storage       | 30GB gp2      | Default EBS volume        |

💬 Want to update any of these values?
---
```

### Trigger 3: Configuration Update
```
---
## ✏️ Updated Configuration: EC2

### Changed Parameters
| Parameter | Previous Value | New Value |
|-----------|---------------|-----------|
| Quantity  | 5             | 10        |

### Recalculated Cost
| Metric        | Value      |
|---------------|------------|
| Monthly Cost  | $XXX.XX    |
| Previous Cost | $XXX.XX    |
| Difference    | +$XXX.XX   |

> All other services remain unchanged.
---
```

## 🔧 Configuration

### Pricing Lookup Priority
1. Check `pricing_master` table in PostgreSQL DB
2. Call live pricing API (AWS/Azure/GCP)
3. Use last known price with ⚠️ flag if unavailable

### Session Management
- Sessions are stored in-memory (can be extended to database)
- Each session has unique ID
- Sessions persist until explicitly cleared
- Export sessions as JSON for backup

## 🎨 UI Features

### Chat Interface
- Real-time conversational interface
- Message history with user/assistant distinction
- Markdown and table rendering in responses
- Auto-scroll to latest message

### Example Prompts
8 pre-configured prompts for quick testing:
1. 🛒 E-commerce Platform
2. ⚡ Serverless API
3. 🐳 Microservices
4. 📊 Data Pipeline
5. 🔍 Show Assumptions
6. ✏️ Update Config
7. 💰 Total Cost
8. 🔄 What-If Analysis

### Session Info Bar
- Session ID
- Conversation turn count
- Number of detected services
- Current region

### Cost Summary Sidebar
- Real-time monthly cost
- Annual cost projection
- List of detected services with individual costs

## 🚧 Future Enhancements

### Planned Features
- [ ] Image analysis with OCR for architecture diagrams
- [ ] Complete what-if analysis implementation
- [ ] Multi-cloud cost comparison
- [ ] Reserved instance recommendations
- [ ] Cost optimization suggestions
- [ ] Export to PDF/Excel
- [ ] Integration with actual cloud provider APIs
- [ ] Historical cost tracking
- [ ] Budget alerts and notifications

## 🐛 Troubleshooting

### Server Not Running
```bash
# Start the server
python main.py

# Server should show:
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Connection Refused
- Ensure server is running on port 8000
- Check firewall settings
- Verify CORS is enabled in main.py

### Session Not Found
- Session IDs are generated client-side
- Sessions are in-memory (cleared on server restart)
- Use "New Session" button to start fresh

### Pricing Calculation Errors
- Check database connection
- Verify pricing_master table has data
- Review service_detector.py for service patterns

## 📚 API Documentation

Full API documentation available at:
```
http://localhost:8000/docs
```

Interactive API testing at:
```
http://localhost:8000/redoc
```

## 🤝 Contributing

To extend the agent:

1. **Add New Triggers**: Update `detect_trigger()` method
2. **Add Service Patterns**: Extend `_get_service_patterns()`
3. **Add Cloud Providers**: Update `DEFAULT_ASSUMPTIONS`
4. **Customize Responses**: Modify `format_trigger*_response()` methods

## 📄 License

Part of the Cloud Cost Assistant project.

---

**Made with ❤️ by Bob**