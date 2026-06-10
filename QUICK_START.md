# 🚀 Quick Start Guide - Cloud Cost Assistant

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher (running on localhost:5432)
- Web browser (Chrome, Firefox, Edge, or Safari)

## Step-by-Step Setup

### 1. Install Python Dependencies

Open terminal in the project root directory and run:

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- FastAPI (web framework)
- SQLAlchemy (database ORM)
- psycopg2-binary (PostgreSQL driver)
- uvicorn (ASGI server)
- pydantic (data validation)

### 2. Configure Database

**Option A: Use existing PostgreSQL**

Edit `backend/database.py` and update the connection string:

```python
DATABASE_URL = "postgresql://YOUR_USERNAME:YOUR_PASSWORD@localhost:5432/cloud_cost"
```

**Option B: Create new database**

```sql
-- Connect to PostgreSQL
psql -U postgres

-- Create database
CREATE DATABASE cloud_cost;

-- Exit
\q
```

### 3. Initialize Database

Run the seed script to create tables and populate data:

```bash
cd backend
python seed_db.py
```

You should see:
```
🚀 AWS PRICING DATABASE SEEDING
📊 Initializing database...
🌍 Seeding regions...
✅ Added 10 regions
📁 Seeding service categories...
✅ Added 10 categories
⚙️  Seeding services...
✅ Added 30+ services
✅ DATABASE SEEDING COMPLETED SUCCESSFULLY!
```

### 4. Start the API Server

**Option A: Using Python directly**

```bash
cd backend
python main.py
```

**Option B: Using the batch file (Windows)**

Double-click `start_server.bat` in the root directory

**Option C: Using uvicorn**

```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. Open the Frontend

**Option A: AI Agent Interface (Recommended)**

Open `frontend/conversational_agent.html` in your browser

**Option B: Agent Demo**

Open `frontend/agent_demo.html` in your browser

**Option C: Basic Calculator**

Open `frontend/index.html` in your browser

## 🎯 Using the Application

### Method 1: AI-Powered Analysis (Easiest)

1. Open `frontend/conversational_agent.html`
2. Describe your architecture in plain English:
   ```
   "Web application with 3 EC2 instances, load balancer, 
   RDS PostgreSQL database with 200GB storage, and S3 for images"
   ```
3. Click "🤖 Analyze Architecture"
4. AI automatically detects services and calculates costs!

### Method 2: Quick Architecture Patterns

1. Open `frontend/agent_demo.html`
2. Click one of the quick pattern cards:
   - 🌐 Web Application
   - ⚡ Serverless
   - 🐳 Microservices
   - 📊 Data Pipeline
3. Select scale (small/medium/large)
4. Get instant cost estimate!

### Method 3: Manual Calculator

1. Open `frontend/index.html`
2. Select service from dropdown
3. Configure parameters
4. Click "Calculate Cost"

## 🔍 Testing the API

### Check API Health

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-06-09T10:00:00.000Z"
}
```

### Get All Services

```bash
curl http://localhost:8000/services
```

### Calculate EC2 Cost

```bash
curl -X POST http://localhost:8000/calculate \
  -H "Content-Type: application/json" \
  -d '{
    "service": "EC2",
    "config": {
      "region": "us-east-1",
      "instanceType": "t3.medium",
      "hours": 730,
      "count": 2
    }
  }'
```

### AI Diagram Analysis

```bash
curl -X POST http://localhost:8000/analyze-diagram \
  -H "Content-Type: application/json" \
  -d '{
    "diagram_text": "Web app with EC2, RDS, S3, and CloudFront",
    "scale": "medium"
  }'
```

## 📊 API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Issue: "Database connection failed"

**Solution:**
1. Check PostgreSQL is running: `pg_isready`
2. Verify credentials in `backend/database.py`
3. Ensure database exists: `psql -U postgres -l`

### Issue: "Module not found"

**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Issue: "Port 8000 already in use"

**Solution:**

**Windows:**
```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

**Linux/Mac:**
```bash
lsof -ti:8000 | xargs kill -9
```

Or change port in `backend/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)
```

### Issue: "CORS error in browser"

**Solution:**
The API already has CORS enabled. Make sure you're accessing the HTML files via:
- File protocol: `file:///path/to/frontend/conversational_agent.html`
- Or serve with: `python -m http.server 3000` in frontend directory

### Issue: "No services detected"

**Solution:**
Re-run the seed script:
```bash
cd backend
python seed_db.py
```

## 🎨 Example Workflows

### Workflow 1: Quick Web App Estimate

1. Open `frontend/conversational_agent.html`
2. Type: "Small web application with EC2 and RDS"
3. Click "Analyze"
4. Get instant cost breakdown

### Workflow 2: Update Configuration

1. After getting initial estimate
2. In any service card, type: "change to 5 instances"
3. Click "Update"
4. See new cost immediately

### Workflow 3: Compare Regions

1. Get estimate for us-east-1
2. Update: "use Mumbai region"
3. Compare costs with regional multiplier

### Workflow 4: Scale Architecture

1. Start with "small" scale
2. Get estimate
3. Change scale to "large"
4. See how costs scale

## 📁 Project Structure

```
cloud-cost-assistant/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── pricing_engine.py          # Cost calculation engine
│   ├── pricing_database.py        # 30+ services pricing data
│   ├── service_detector.py        # AI service detection
│   ├── models.py                  # Database models
│   ├── database.py                # DB configuration
│   ├── seed_db.py                 # Database seeding
│   └── requirements.txt           # Python dependencies
├── frontend/
│   ├── conversational_agent.html  # AI agent interface (BEST)
│   ├── agent_demo.html            # Pattern-based interface
│   └── index.html                 # Basic calculator
├── docs/
│   └── *.md                       # Documentation
├── start_server.bat               # Windows quick start
└── QUICK_START.md                 # This file
```

## 🌟 Key Features

✅ **30+ AWS Services**: EC2, S3, RDS, Lambda, DynamoDB, and more
✅ **AI Service Detection**: Automatically identifies services from descriptions
✅ **Conversational Updates**: Update configs in plain English
✅ **Multi-Region Support**: 10+ AWS regions with pricing multipliers
✅ **Architecture Patterns**: Quick estimates for common patterns
✅ **Real-time Calculation**: Instant cost updates
✅ **Cost History**: Track all calculations
✅ **RESTful API**: Complete API with OpenAPI docs

## 🎯 Next Steps

1. ✅ Start the server
2. ✅ Open the AI agent interface
3. ✅ Try describing an architecture
4. ✅ Explore the API documentation
5. ✅ Check out the example workflows

## 📞 Need Help?

- Check API docs: http://localhost:8000/docs
- Review documentation in `docs/` folder
- Check troubleshooting section above

---

**Ready to calculate cloud costs? Start the server and open the AI agent interface!** 🚀