# ☁️ Cloud Cost Assistant - AWS Pricing Engine

A production-grade AWS-style pricing calculator with support for 30+ services, multi-region pricing, tiered models, and architecture diagram analysis.

## 🚀 Features

- **30+ AWS Services**: EC2, S3, RDS, Lambda, DynamoDB, CloudFront, and more
- **Multi-Region Support**: 10+ AWS regions with regional pricing multipliers
- **Multiple Pricing Models**:
  - Hourly (EC2, RDS, EKS)
  - Tiered Storage (S3, EBS, EFS)
  - Request-based (SQS, SNS, API Gateway)
  - Hybrid (Lambda, CloudFront)
  - Flat Monthly (IAM, VPC)
- **Architecture Analysis**: Analyze diagrams and get instant cost estimates
- **Cost History**: Track and review past calculations
- **RESTful API**: Complete FastAPI backend with OpenAPI documentation
- **Modern Frontend**: Interactive web interface for quick calculations

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL 12+
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cloud-cost-assistant
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Database

Update `database.py` with your PostgreSQL credentials:

```python
DATABASE_URL = "postgresql://username:password@localhost:5432/cloud_cost"
```

### 4. Initialize Database

```bash
python seed_db.py
```

This will:
- Create all necessary tables
- Seed 30+ AWS services with pricing data
- Add 10+ regions with multipliers
- Create sample configurations
- Set up legacy compatibility tables

## 🚀 Running the Application

### Start the API Server

```bash
python main.py
```

Or using uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at: `http://localhost:8000`

### Access the Frontend

Open `index.html` in your browser or serve it with a local server:

```bash
python -m http.server 3000
```

Then visit: `http://localhost:3000`

## 📚 API Documentation

### Interactive API Docs

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Get All Services
```http
GET /services
```

Response:
```json
{
  "count": 30,
  "services": [
    {
      "code": "EC2",
      "name": "Elastic Compute Cloud",
      "description": "Virtual Servers",
      "category": "Compute",
      "pricing_model": "hourly"
    }
  ]
}
```

#### Calculate Single Service Cost
```http
POST /calculate
Content-Type: application/json

{
  "service": "EC2",
  "config": {
    "region": "us-east-1",
    "instanceType": "t3.medium",
    "hours": 730,
    "count": 2
  }
}
```

Response:
```json
{
  "success": true,
  "result": {
    "service": "EC2",
    "region": "us-east-1",
    "region_multiplier": 1.0,
    "model": "hourly",
    "cost": 60.74,
    "breakdown": {
      "instanceType": "t3.medium",
      "hourlyRate": 0.0416,
      "hours": 730,
      "count": 2
    }
  }
}
```

#### Calculate Multiple Services
```http
POST /calculate-multiple
Content-Type: application/json

{
  "services": [
    {
      "service": "EC2",
      "config": {
        "region": "us-east-1",
        "instanceType": "t3.medium",
        "hours": 730,
        "count": 1
      }
    },
    {
      "service": "S3",
      "config": {
        "region": "us-east-1",
        "usageGB": 500
      }
    }
  ],
  "save_history": true,
  "notes": "Production environment estimate"
}
```

#### Get Regions
```http
GET /regions
```

#### Get Calculation History
```http
GET /history?limit=50
```

#### Get Statistics
```http
GET /stats
```

## 💡 Usage Examples

### Python Example

```python
import requests

# Calculate EC2 cost
response = requests.post('http://localhost:8000/calculate', json={
    "service": "EC2",
    "config": {
        "region": "us-east-1",
        "instanceType": "t3.medium",
        "hours": 730,
        "count": 2
    }
})

result = response.json()
print(f"Monthly cost: ${result['result']['cost']}")
```

### JavaScript Example

```javascript
async function calculateCost() {
    const response = await fetch('http://localhost:8000/calculate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            service: 'Lambda',
            config: {
                region: 'us-east-1',
                requests: 1000000,
                gbSeconds: 12800
            }
        })
    });
    
    const data = await response.json();
    console.log('Cost:', data.result.cost);
}
```

### cURL Example

```bash
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "service": "S3",
    "config": {
      "region": "us-east-1",
      "usageGB": 1000
    }
  }'
```

## 🏗️ Architecture

```
cloud-cost-assistant/
├── pricing_database.py      # Complete AWS pricing data (30+ services)
├── pricing_engine.py        # Core calculation engine
├── models.py                # SQLAlchemy database models
├── database.py              # Database configuration
├── seed_db.py              # Database seeding script
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── index.html             # Frontend interface
└── README.md              # This file
```

## 🎯 Supported Services

### Compute
- EC2 (Elastic Compute Cloud)
- Lambda (Serverless)
- ECS (Container Service)
- EKS (Kubernetes)
- Fargate

### Storage
- S3 (Object Storage)
- EBS (Block Storage)
- EFS (File Storage)
- Glacier (Archive)

### Database
- RDS (Relational)
- DynamoDB (NoSQL)
- Aurora
- ElastiCache
- Redshift

### Networking
- CloudFront (CDN)
- API Gateway
- ELB (Load Balancer)
- NAT Gateway
- VPC
- Route53

### Messaging
- SQS (Queue)
- SNS (Notifications)
- EventBridge
- Kinesis

### Monitoring & Security
- CloudWatch
- IAM
- KMS
- CloudTrail
- Systems Manager

### Analytics & ML
- Athena
- EMR
- Glue
- SageMaker
- Rekognition

## 🌍 Supported Regions

- us-east-1 (N. Virginia) - 1.0x
- us-east-2 (Ohio) - 1.0x
- us-west-1 (N. California) - 1.05x
- us-west-2 (Oregon) - 1.0x
- eu-west-1 (Ireland) - 1.12x
- eu-central-1 (Frankfurt) - 1.15x
- ap-south-1 (Mumbai) - 1.0x
- ap-southeast-1 (Singapore) - 1.08x
- ap-northeast-1 (Tokyo) - 1.10x
- sa-east-1 (São Paulo) - 1.2x

## 🔧 Configuration Examples

### EC2 Instance
```json
{
  "service": "EC2",
  "config": {
    "region": "us-east-1",
    "instanceType": "t3.medium",
    "hours": 730,
    "count": 2
  }
}
```

### S3 Storage (Tiered)
```json
{
  "service": "S3",
  "config": {
    "region": "us-east-1",
    "usageGB": 1000
  }
}
```

### Lambda (Hybrid)
```json
{
  "service": "Lambda",
  "config": {
    "region": "us-east-1",
    "requests": 10000000,
    "gbSeconds": 128000
  }
}
```

### RDS Database
```json
{
  "service": "RDS",
  "config": {
    "region": "us-east-1",
    "instanceType": "db.t3.medium",
    "hours": 730,
    "storageGB": 100
  }
}
```

## 📊 Database Schema

The application uses a production-grade schema:

- **regions**: AWS regions with pricing multipliers
- **service_categories**: Service groupings
- **services**: AWS services with pricing models
- **service_skus**: Individual pricing items (SKUs)
- **pricing_tiers**: Tiered pricing rules
- **calculation_history**: Cost calculation records
- **architecture_diagrams**: Diagram analysis results
- **service_configurations**: Predefined templates

## 🧪 Testing

### Test the API
```bash
# Health check
curl http://localhost:8000/health

# Get all services
curl http://localhost:8000/services

# Get statistics
curl http://localhost:8000/stats
```

### Test Calculations
```bash
# EC2 calculation
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{"service":"EC2","config":{"region":"us-east-1","instanceType":"t3.medium","hours":730,"count":1}}'
```

## 🚀 Deployment

### Production Considerations

1. **Environment Variables**: Use environment variables for sensitive data
```python
import os
DATABASE_URL = os.getenv('DATABASE_URL')
```

2. **CORS**: Update CORS settings in `main.py` for production
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

3. **Database**: Use connection pooling and proper credentials

4. **Logging**: Add proper logging for production monitoring

5. **Rate Limiting**: Implement rate limiting for API endpoints

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Inspired by AWS Pricing Calculator
- Built with FastAPI, SQLAlchemy, and PostgreSQL
- Pricing data structure based on AWS Price List API

## 📧 Support

For issues and questions, please open an issue on GitHub.

---

**Built with ❤️ for cloud cost optimization**