# SoulSync AI - Complete Setup Guide

This comprehensive guide will walk you through setting up SoulSync AI on your local machine for development. Follow these steps carefully to ensure a smooth setup process.

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

| Software | Version | Purpose | Download Link |
|----------|---------|---------|---------------|
| **Python** | 3.11+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 20+ | Frontend runtime | [nodejs.org](https://nodejs.org/) |
| **MongoDB** | 6.0+ | Primary database | [mongodb.com](https://www.mongodb.com/try/download/community) |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/) |
| **Chrome** | Latest | Voice mode (Web Speech API) | [google.com/chrome](https://www.google.com/chrome/) |

### Verify Installations

Open your terminal/command prompt and run:

```bash
# Check Python
python --version  # Should show Python 3.11 or higher

# Check Node.js
node -v  # Should show v20 or higher

# Check npm
npm -v  # Should show version number

# Check Git
git --version  # Should show git version
```

## 🚀 Quick Start (5 Minutes)

If you're familiar with setting up development environments, here's the fast track:

```bash
# 1. Clone repository
git clone https://github.com/intsurjeetkaran-droid/SoulSync.git
cd SoulSync/soulsync-ai

# 2. Create Python virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Install frontend dependencies
cd soulsync-frontend
npm install
cd ..

# 5. Configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration section)

# 6. Start MongoDB (if not running)
# Windows: Start MongoDB service
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod

# 7. Start backend (Terminal 1)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 8. Start frontend (Terminal 2)
cd soulsync-frontend
npm run dev

# 9. Open browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

## 📝 Detailed Setup Instructions

### Step 1: Clone the Repository

```bash
# Navigate to your projects directory
cd ~/Projects  # or any directory you use for projects

# Clone the repository
git clone https://github.com/intsurjeetkaran-droid/SoulSync.git

# Enter the project directory
cd SoulSync/soulsync-ai
```

### Step 2: Set Up Python Environment

#### Windows

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# You should see (venv) in your command prompt
```

#### macOS/Linux

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# You should see (venv) in your terminal
```

### Step 3: Install Backend Dependencies

```bash
# Make sure virtual environment is active
# Install all Python packages
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi  # Should show FastAPI
```

**Common Issues:**
- If you get "permission denied" errors, try: `pip install --user -r requirements.txt`
- If you're on Windows and get build errors, install Microsoft C++ Build Tools

### Step 4: Install Frontend Dependencies

```bash
# Navigate to frontend directory
cd soulsync-frontend

# Install Node packages
npm install

# This may take a few minutes. Go grab a coffee! ☕

# Verify installation
npm list react  # Should show React version
```

### Step 5: Set Up MongoDB

#### Option A: MongoDB Atlas (Cloud - Recommended for Beginners)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account
3. Create a new cluster (free tier M0)
4. Wait for cluster to be created (2-3 minutes)
5. Click "Connect" → "Connect your application"
6. Copy the connection string
7. Replace `<password>` with your database user password
8. Update your `.env` file with this connection string

#### Option B: Local MongoDB Installation

**Windows:**
1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Run the installer and follow the setup wizard
3. Install as a Windows Service (recommended)
4. MongoDB will start automatically

**macOS:**
```bash
# Install using Homebrew
brew tap mongodb/brew
brew install mongodb-community

# Start MongoDB
brew services start mongodb-community
```

**Linux (Ubuntu/Debian):**
```bash
# Import MongoDB public key
wget -qO - https://www.mongodb.org/static/pgp/server-6.0.asc | sudo apt-key add -

# Add MongoDB repository
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/6.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-6.0.list

# Update and install
sudo apt-get update
sudo apt-get install -y mongodb-org

# Start MongoDB
sudo systemctl start mongod
sudo systemctl enable mongod
```

#### Create Database

```bash
# Connect to MongoDB
mongosh

# Create database
use soulsync_db

# Create a test collection
db.createCollection("test")

# Exit
exit
```

### Step 6: Configure Environment Variables

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file:**
   ```bash
   # Open with your preferred editor
   # Windows: notepad .env
   # macOS: nano .env
   # Linux: nano .env or code .env
   ```

3. **Required Configuration:**

   ```env
   # ─── Groq API (Required) ────────────────────────────────────
   # Get your free API key from https://console.groq.com/keys
   GROQ_API_KEY=your_groq_api_key_here
   
   # ─── MongoDB (Required) ─────────────────────────────────────
   # For local MongoDB:
   MONGODB_URL=mongodb://localhost:27017/soulsync_db
   MONGODB_DB=soulsync_db
   
   # For MongoDB Atlas (cloud):
   # MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/soulsync_db
   
   # ─── JWT Authentication ─────────────────────────────────────
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
   JWT_ALGORITHM=HS256
   JWT_EXPIRE_MINUTES=10080
   ```

4. **Get Groq API Key:**
   - Go to [Groq Console](https://console.groq.com/keys)
   - Sign up or log in
   - Create a new API key
   - Copy and paste it into your `.env` file

### Step 7: Start the Backend Server

```bash
# Make sure you're in the soulsync-ai directory
# and your virtual environment is active

# Start the backend with auto-reload (development mode)
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Will watch for changes and will restart on changes
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [67890]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Verify Backend:**
- Open browser: http://localhost:8000
- You should see: `{"project": "SoulSync AI", "version": "3.0.0", ...}`
- API Documentation: http://localhost:8000/docs

### Step 8: Start the Frontend Server

Open a **new terminal window** (keep the backend running):

```bash
# Navigate to frontend directory
cd soulsync-frontend

# Start development server
npm run dev
```

**Expected Output:**
```
  VITE v5.x.x  ready in xxx ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h to show help
```

**Verify Frontend:**
- Open browser: http://localhost:5173
- You should see the SoulSync AI landing page
- Click "Login" and use demo credentials (see credentials.txt)

### Step 9: Test the Application

1. **Login to the application:**
   - Go to http://localhost:5173
   - Click "Login"
   - Use credentials from `credentials.txt` in the root directory

2. **Test chat functionality:**
   - Type a message in the chat input
   - Wait for AI response (should take <1 second)
   - Check if memories are being stored

3. **Test voice mode:**
   - Click the "Voice" button in the header
   - Allow microphone access
   - Tap the sphere and speak
   - Wait for response

## 🔧 Troubleshooting Common Issues

### Backend Issues

#### "ModuleNotFoundError: No module named 'backend'"
```bash
# Make sure you're in the soulsync-ai directory
# and your virtual environment is active
cd soulsync-ai
source venv/bin/activate  # or venv\Scripts\activate on Windows
```

#### "MongoDB connection failed"
```bash
# Check if MongoDB is running
# Windows: Check Services
# macOS: brew services list
# Linux: sudo systemctl status mongod

# If not running, start it
# Windows: Net start MongoDB
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

#### "GROQ_API_KEY is not set"
```bash
# Make sure your .env file is in the soulsync-ai directory
# Check that GROQ_API_KEY is set correctly
# Restart the backend after changing .env
```

### Frontend Issues

#### "npm: command not found"
```bash
# Install Node.js from nodejs.org
# Or use nvm (Node Version Manager)
```

#### "Port 5173 already in use"
```bash
# Kill the process using port 5173
# Windows: netstat -ano | findstr :5173
# macOS/Linux: lsof -ti:5173 | xargs kill -9

# Or change the port in vite.config.js
```

#### "Cannot connect to backend"
```bash
# Make sure backend is running on port 8000
# Check VITE_API_URL in soulsync-frontend/.env
# Should be: VITE_API_URL=http://localhost:8000
```

### Database Issues

#### "Authentication failed" (MongoDB Atlas)
```bash
# Check your connection string
# Make sure username and password are correct
# Whitelist your IP address in MongoDB Atlas
```

#### "Connection refused" (Local MongoDB)
```bash
# Make sure MongoDB service is running
# Check MongoDB logs for errors
# Try connecting with mongosh to debug
```

## 📁 Project Structure Reference

```
soulsync-ai/
├── backend/                    # Python FastAPI backend
│   ├── api/                   # API route handlers
│   ├── auth/                  # Authentication logic
│   ├── core/                  # Core services (AI, etc.)
│   ├── db/                    # Database connections
│   ├── memory/                # Memory management
│   ├── processing/            # NLP processing
│   ├── retrieval/             # RAG engine
│   ├── suggestion/            # Suggestion engine
│   ├── tasks/                 # Task management
│   ├── utils/                 # Utility functions
│   └── main.py               # Application entry point
│
├── soulsync-frontend/         # React frontend
│   ├── src/
│   │   ├── components/        # Reusable UI components
│   │   ├── pages/             # Page components
│   │   ├── context/           # React context providers
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # Business logic
│   │   └── api/               # API client
│   ├── public/                # Static assets
│   └── package.json           # Node dependencies
│
├── .env                       # Environment configuration
├── .env.example              # Environment template
├── requirements.txt          # Python dependencies
├── README.md                 # Project documentation
└── CONTRIBUTING.md           # Contribution guidelines
```

## 🎯 Next Steps

### For First-Time Users
1. Read the main [README.md](../README.md) for feature overview
2. Review the [ARCHITECTURE.md](ARCHITECTURE.md) to understand system design
3. Try out different features: chat, voice mode, tasks, insights

### For Developers
1. Read [CONTRIBUTING.md](../CONTRIBUTING.md) for coding standards
2. Set up your development environment (IDE, extensions, etc.)
3. Explore the codebase starting from `backend/main.py` and `src/App.jsx`
4. Make your first change and test it

### For Deployment
1. Review the [Deployment Guide](DEPLOYMENT.md) (if available)
2. Set up production environment variables
3. Configure MongoDB Atlas for production
4. Deploy to your preferred platform (AWS, GCP, Azure, etc.)

## 📞 Getting Help

If you encounter issues not covered in this guide:

1. **Check existing documentation:**
   - [Main README](../README.md)
   - [Architecture Docs](ARCHITECTURE.md)
   - [Contributing Guide](../CONTRIBUTING.md)

2. **Search GitHub Issues:**
   - [SoulSync Issues](https://github.com/intsurjeetkaran-droid/SoulSync/issues)

3. **Contact the team:**
   - Email: [your-email@example.com]
   - Discord: [invite-link]
   - Twitter: [@soulsync_ai]

## ✅ Setup Checklist

Use this checklist to ensure you've completed all setup steps:

- [ ] Python 3.11+ installed
- [ ] Node.js 20+ installed
- [ ] MongoDB installed and running
- [ ] Repository cloned
- [ ] Python virtual environment created and activated
- [ ] Backend dependencies installed
- [ ] Frontend dependencies installed
- [ ] `.env` file created from `.env.example`
- [ ] Groq API key obtained and added to `.env`
- [ ] MongoDB connection string configured
- [ ] Backend server running on port 8000
- [ ] Frontend server running on port 5173
- [ ] Able to access http://localhost:5173
- [ ] Able to login with demo credentials
- [ ] Chat functionality working
- [ ] Voice mode tested (Chrome only)

---

**Congratulations!** 🎉 You've successfully set up SoulSync AI on your local machine. You're now ready to explore, develop, and contribute to the project!

**Setup Guide Version:** 1.0  
**Last Updated:** May 7, 2026  
**Maintained By:** SoulSync Development Team