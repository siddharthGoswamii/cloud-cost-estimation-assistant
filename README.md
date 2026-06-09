# Cloud Cost Assistant

AI-powered cloud cost estimation tool with conversational interface and live AWS pricing.

## 📁 Project Structure

```
cloud-cost-assistant/
├── backend/           # Python FastAPI backend
│   ├── main.py       # Main API server
│   ├── pricing_engine.py
│   ├── conversational_cost_agent.py
│   ├── aws_pricing_boto3.py
│   ├── models.py
│   ├── database.py
│   └── ...
├── frontend/          # HTML/CSS/JS frontend
│   ├── agent_demo.html
│   ├── conversational_agent.html
│   └── index.html
├── docs/             # Documentation
│   ├── README.md
│   ├── SETUP_GUIDE.md
│   ├── AWS_PRICING_SETUP.md
│   └── PRICING_SYSTEM_GUIDE.md
└── start_server.bat  # Quick start script
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r backend/requirements.txt
```

### 2. Configure AWS Credentials (Optional)
Create `backend/.env` file:
```
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_secret_here
AWS_DEFAULT_REGION=us-east-1
```

### 3. Start Server
**Windows:**
```bash
start_server.bat
```

**Linux/Mac:**
```bash
cd backend && python main.py
```

### 4. Access UI
Open browser: **http://localhost:8000/**

## ✨ Features

- 🤖 **Conversational AI Agent** - Natural language cost estimation
- 💰 **Live AWS Pricing** - Real-time prices via AWS Pricing API
- 📊 **4 Example Prompts** - Quick start templates
- 🔍 **Service Detection** - Automatic architecture parsing
- 📈 **Multi-turn Conversations** - Stateful session management
- 🎯 **Accurate Extraction** - Quantities, instance types, storage, data transfer

## 📖 Documentation

See `docs/` folder for detailed guides:
- **SETUP_GUIDE.md** - Installation and configuration
- **AWS_PRICING_SETUP.md** - AWS API integration
- **PRICING_SYSTEM_GUIDE.md** - Pricing engine details

## 🛠️ Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, boto3
- **Frontend**: HTML, CSS, JavaScript
- **Database**: PostgreSQL
- **Cloud**: AWS Pricing API

## 📝 License

MIT License
