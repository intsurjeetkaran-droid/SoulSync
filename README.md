# 🧠 SoulSync AI

### *"An AI that understands you, grows with you, and supports your life."*

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![MongoDB](https://img.shields.io/badge/MongoDB-6.0-47A248)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Built by [Surjeet Karan](https://github.com/surjeetkaran) · April 23, 2026**

---

## 📌 Table of Contents

1. [What is SoulSync AI?](#-what-is-soulsync-ai)
2. [Quick Start](#-quick-start)
3. [Key Features](#-key-features)
4. [Tech Stack](#-tech-stack)
5. [Architecture Overview](#-architecture-overview)
6. [Project Structure](#-project-structure)
7. [Complete Setup Guide](#-complete-setup-guide)
8. [Environment Configuration](#-environment-configuration)
9. [API Reference](#-api-reference)
10. [Database Schema](#-database-schema)
11. [Development Guidelines](#-development-guidelines)
12. [Deployment](#-deployment)
13. [Troubleshooting](#-troubleshooting)
14. [Contributing](#-contributing)
15. [Developers](#-developers)

---

## 🧠 What is SoulSync AI?

SoulSync AI is a **personal AI companion system** that learns from your daily life, remembers your conversations, understands your emotions, and provides deeply personalized responses, advice, and task management.

Unlike traditional chatbots that forget everything after each session, SoulSync AI builds a **long-term memory model** of you — growing smarter and more personal with every interaction.

> **Core Concept:** `User shares life → AI learns → AI adapts → AI improves support`

### Key Capabilities

- **🧠 Intelligent Memory** — Remembers every conversation permanently
- **🔍 Smart Retrieval** — Uses RAG (Retrieval-Augmented Generation) for context
- **🎯 Task Management** — Auto-detects and manages tasks from conversations
- **📊 Insights** — Analyzes patterns in your emotions and activities
- **🌐 Multi-Language** — Supports English, Hindi, and Hinglish
- **🔐 Secure Auth** — JWT-based authentication with bcrypt password hashing

---

## 🚀 Quick Start

### Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.11+ | Backend runtime |
| Node.js | 20+ | Frontend runtime |
| MongoDB | 6.0+ | Database (local or Atlas) |
| Git | Latest | Version control |

### 5-Minute Setup

```bash
# 1. Clone repository
git clone https://github.com/intsurjeetkaran-droid/SoulSync.git
cd SoulSync

# 2. Create Python virtual environment
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux: source venv/bin/activate

# 3. Install dependencies
pip install -r soulsync-ai/requirements.txt
cd soulsync-ai/soulsync-frontend && npm install && cd ../..

# 4. Configure environment
cp soulsync-ai/.env.example soulsync-ai/.env
# Edit .env with your MongoDB and Groq API keys

# 5. Start backend (Terminal 1)
cd soulsync-ai
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# 6. Start frontend (Terminal 2)
cd soulsync-ai/soulsync-frontend
npm run dev

# 7. Open browser
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

> **Need detailed instructions?** See [Complete Setup Guide](#-complete-setup-guide) below.

---

## ✨ Key Features

### 🧠 1. Intelligent Memory Engine
- Stores every conversation permanently in MongoDB
- **Short-term memory** — recent conversation context (last 5 turns)
- **Long-term memory** — all past conversations, searchable by meaning
- **Behavioral memory** — structured patterns extracted from your messages
- Memory is never lost between sessions

### 🔍 2. Retrieval-Augmented Generation (RAG)
- Before every response, searches your entire conversation history
- Uses **FAISS vector search** to find semantically similar past memories
- Injects relevant memories into the AI prompt for personalized responses
- Example: You say *"I'm tired again"* → SoulSync recalls *"You mentioned feeling tired and skipping gym on Tuesday"*

### 🧩 3. Memory Processing & Extraction
- Automatically extracts structured data from your raw messages
- Detects: **emotion**, **activity**, **status**, **productivity level**
- Example:
  ```
  Input:  "I felt tired and skipped gym today"
  Output: { emotion: "tired", activity: "gym", status: "missed", productivity: "low" }
  ```

### 💡 4. Smart Suggestion Engine
- Analyzes your activity patterns using **Pandas**
- Detects recurring habits, emotional trends, and productivity cycles
- Generates actionable, personalized suggestions:
  - *"You've skipped gym 3 times this week — try a 15-min walk instead"*
  - *"Stress detected multiple times — try 5-min breathing exercises"*

### ✅ 5. Intelligent Task Manager
- **Auto-detects tasks** from natural language in your messages
- Supports priority levels: High / Medium / Low
- Supports due dates: today, tomorrow, Friday, next week, etc.
- Example: *"I need to finish my report by Friday"* → Task created automatically
- Full CRUD: create, complete, delete tasks

### 🌐 6. Multi-Language Support
- **Automatic language detection** — detects English, Hindi (Devanagari), and Hinglish
- **Pattern-based detection** — instant recognition without API calls
- **Natural responses** — AI responds in the same language you use
- Examples:
  - English: "I'm feeling stressed today"
  - Hindi: "मुझे आज तनाव हो रहा है"
  - Hinglish: "Aaj mujhe bahut tension hai"

### 📊 7. Insights Dashboard
- Real-time emotion breakdown with visual bars
- Dominant mood detection
- Personalized suggestions panel
- All powered by your actual conversation data

### ⚡ 8. Performance & Caching
- **Groq API** — sub-second AI responses (avg 0.3–0.7s)
- LRU response cache (200 entries, 10-min TTL)
- MongoDB connection pooling (2–10 connections)
- FAISS vector search with relevance threshold filtering

### 🎨 9. Modern Web Interface
- Built with **React + Vite + Tailwind CSS + Framer Motion**
- Premium color palette with smooth animations
- Responsive design for desktop and mobile
- Real-time chat with typing indicator
- Task panel with priority sorting

### 🐳 10. Production-Ready Deployment
- Full **Docker Compose** setup
- **Kubernetes** manifests for scaling
- Nginx reverse proxy for frontend
- Health checks on all services

---

## 🛠 Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| FastAPI | 0.136.0 | REST API framework |
| Groq API | llama-3.3-70b-versatile | AI response generation |
| sentence-transformers | 3.4.1 | Text embeddings (all-MiniLM-L6-v2) |
| FAISS | 1.13.0 | Vector similarity search |
| MongoDB | 6.0+ | Primary database |
| motor | 3.6.0 | MongoDB async Python driver |
| Pandas | 3.0.2 | Pattern analysis |
| python-jose | 3.5.0 | JWT tokens |
| passlib + bcrypt | 1.7.4 / 4.0.1 | Password hashing |
| redis | 5.2.1 | Response caching (optional) |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | 5.x | Build tool |
| Tailwind CSS | 3.4.x | Styling |
| Framer Motion | latest | Animations |
| React Router DOM | latest | Client-side routing |
| Axios | latest | API calls with JWT |
| Lucide React | latest | Icons |
| react-hot-toast | latest | Notifications |

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Docker Compose | Local orchestration |
| Kubernetes | Production deployment |
| Nginx | Frontend serving + API proxy |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLIENT LAYER                            │
│              React + Vite + Tailwind CSS                     │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP/HTTPS
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    API GATEWAY LAYER                         │
│              Nginx Reverse Proxy (optional)                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  APPLICATION LAYER                           │
│              FastAPI Backend Services                        │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │    Auth    │ │    Chat    │ │    Tasks   │ │   Voice   │ │
│  │  Service   │ │  Service   │ │  Service   │ │  Service  │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌───────────┐ │
│  │ Processing │ │  Retrieval │ │ Suggestion │ │  Memory   │ │
│  │  Service   │ │  (RAG)     │ │  Service   │ │  Service  │ │
│  └────────────┘ └────────────┘ └────────────┘ └───────────┘ │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                       DATA LAYER                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   MongoDB    │  │    Redis     │  │    FAISS     │      │
│  │  (Primary)   │  │  (Cache)     │  │  (Vectors)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Groq API   │  │  Edge TTS    │  │  Whisper     │      │
│  │  (AI Chat)   │  │   (TTS)      │  │   (STT)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User sends message** → Frontend → Backend API
2. **Language Detection** → Identify English/Hindi/Hinglish
3. **Intent Detection** → Classify: store/query/task/chat
4. **Memory Processing** → Extract emotion, activity, status
5. **RAG Retrieval** → FAISS vector search + keyword fallback
6. **AI Generation** → Groq API with memory context
7. **Task Detection** → Auto-create tasks if applicable
8. **Save to Memory** → Store conversation in MongoDB
9. **Return Response** → Frontend displays with insights

---

## 📁 Project Structure

```
SoulSync/
├── README.md                       ← This file (single source of truth)
├── details.txt                     ← Non-technical project explanation
├── credentials.txt                 ← Demo user credentials (generated)
├── .gitignore
│
└── soulsync-ai/                    ← Main application folder
    │
    ├── backend/                    ← Python FastAPI backend
    │   ├── main.py                 ← App entry point
    │   ├── api/                    ← API route handlers
    │   │   ├── chat.py             ← POST /chat (main endpoint)
    │   │   ├── voice.py            ← Voice endpoints
    │   │   ├── tasks.py            ← Task CRUD
    │   │   ├── memory.py           ← Memory endpoints
    │   │   ├── suggestion.py       ← Insights endpoints
    │   │   ├── processing.py       ← Processing endpoints
    │   │   ├── optimization.py     ← Performance endpoints
    │   │   ├── unique_features.py  ← Special features
    │   │   └── payment.py          ← Payment endpoints (disabled)
    │   ├── auth/                   ← Authentication
    │   │   └── routes.py           ← /auth endpoints
    │   ├── core/                   ← Core services
    │   │   └── ai_service.py       ← Groq API client
    │   ├── db/                     ← Database layer
    │   │   ├── mongo/              ← MongoDB connection
    │   │   └── redis/              ← Redis caching
    │   ├── memory/                 ← Memory management
    │   │   └── memory_manager.py   ← Conversation storage
    │   ├── processing/             ← NLP processing
    │   │   ├── extractor.py        ← Memory extraction
    │   │   ├── intent_detector.py  ← Intent classification
    │   │   ├── language_detector.py← Language detection
    │   │   └── mood_predictor.py   ← Mood logging
    │   ├── retrieval/              ← RAG engine
    │   │   ├── rag_engine.py       ← Main RAG pipeline
    │   │   └── vector_store.py     ← FAISS operations
    │   ├── suggestion/             ← Smart suggestions
    │   │   └── suggestion_engine.py← Pattern analysis
    │   ├── tasks/                  ← Task management
    │   │   ├── task_manager.py     ← Task CRUD
    │   │   └── task_detector.py    ← Auto-detection
    │   └── utils/                  ← Utilities
    │       ├── logging_config.py   ← Logging configuration
    │       ├── cache.py            ← Response caching
    │       ├── voice_tts.py        ← Text-to-speech
    │       └── voice_stt.py        ← Speech-to-text
    │
    ├── soulsync-frontend/          ← React frontend
    │   ├── src/
    │   │   ├── App.jsx             ← Main application
    │   ├── main.jsx               ← Entry point
    │   │   ├── api/                ← API client
    │   │   │   └── soulsync.js     ← Axios with JWT
    │   │   ├── components/         ← UI components
    │   │   │   ├── ChatWindow.jsx  ← Chat display
    │   │   │   ├── ChatInput.jsx   ← Message input
    │   │   │   ├── Header.jsx      ← Navigation
    │   │   │   ├── TaskPanel.jsx   ← Tasks sidebar
    │   │   │   ├── InsightPanel.jsx← Insights sidebar
    │   │   │   └── VoiceMode.jsx   ← Voice UI
    │   │   ├── context/            ← React context
    │   │   │   └── AuthContext.jsx ← Auth state
    │   │   ├── hooks/              ← Custom hooks
    │   │   │   └── useTaskReminder.js
    │   │   ├── pages/              ← Page components
    │   │   │   ├── Landing.jsx     ← Landing page
    │   │   │   ├── Login.jsx       ← Login page
    │   │   │   └── Signup.jsx      ← Signup page
    │   │   └── services/           ← Business logic
    │   │       ├── notifications.js
    │   │       └── taskReminder.js
    │   ├── public/                 ← Static assets
    │   └── package.json
    │
    ├── scripts/                    ← Utility scripts
    │   ├── seed_users.py           ← Create demo users
    │   └── verify_seed.py          ← Verify seeded data
    │
    ├── data/                       ← Data storage
    │   └── vectors/                ← FAISS index files
    │
    ├── docker/                     ← Docker configuration
    │   ├── Dockerfile.backend
    │   ├── Dockerfile.frontend
    │   └── nginx.conf
    │
    ├── k8s/                        ← Kubernetes manifests
    │   ├── namespace.yaml
    │   ├── configmap.yaml
    │   ├── deployments/
    │   └── deploy.sh
    │
    ├── .env                        ← Environment config
    ├── .env.example                ← Config template
    ├── requirements.txt            ← Python dependencies
    ├── docker-compose.yml          ← Docker Compose
    ├── start_backend.bat           ← Windows startup
    └── start_backend.ps1           ← PowerShell startup
```

---

## 📖 Complete Setup Guide

### Step 1: Prerequisites

Ensure you have the following installed:

```bash
# Check Python (3.11+)
python --version

# Check Node.js (20+)
node -v

# Check Git
git --version
```

### Step 2: Clone Repository

```bash
git clone https://github.com/intsurjeetkaran-droid/SoulSync.git
cd SoulSync
```

### Step 3: Set Up Python Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate
```

### Step 4: Install Dependencies

```bash
# Install Python packages
pip install -r soulsync-ai/requirements.txt

# Install Node packages
cd soulsync-ai/soulsync-frontend
npm install
cd ../..
```

### Step 5: Set Up MongoDB

#### Option A: MongoDB Atlas (Cloud - Recommended)

1. Go to [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a free account and cluster
3. Click "Connect" → "Connect your application"
4. Copy the connection string
5. Update your `.env` file

#### Option B: Local MongoDB

```bash
# macOS (with Homebrew)
brew tap mongodb/brew
brew install mongodb-community
brew services start mongodb-community

# Ubuntu/Debian
sudo apt-get install -y mongodb-org
sudo systemctl start mongod

# Windows: Download and install from mongodb.com
```

### Step 6: Configure Environment

1. Copy the example file:
   ```bash
   cp soulsync-ai/.env.example soulsync-ai/.env
   ```

2. Edit `soulsync-ai/.env`:
   ```env
   # Groq API Key (Required)
   GROQ_API_KEY=your_groq_api_key_here
   
   # MongoDB Connection
   MONGODB_URL=mongodb://localhost:27017/soulsync_db
   # OR for Atlas:
   # MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/soulsync_db
   
   # JWT Secret (Change in production!)
   JWT_SECRET_KEY=your-super-secret-jwt-key-change-in-production
   
   # Redis (Optional)
   REDIS_URL=redis://localhost:6379
   ```

3. Get your Groq API key from [console.groq.com](https://console.groq.com/keys)

### Step 7: Start Backend

```bash
# From project root, with venv active
cd soulsync-ai
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### Step 8: Start Frontend

Open a **new terminal** (keep backend running):

```bash
cd soulsync-ai/soulsync-frontend
npm run dev
```

**Expected output:**
```
➜  Local:   http://localhost:5173/
```

### Step 9: Test the Application

1. Open http://localhost:5173 in your browser
2. Click "Get Started" or "Sign In"
3. Create an account or use demo credentials from `credentials.txt`
4. Start chatting with SoulSync AI!

---

## ⚙️ Environment Configuration

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key for AI | `gsk_xxxxx...` |
| `MONGODB_URL` | MongoDB connection string | `mongodb://localhost:27017/soulsync_db` |
| `MONGODB_DB` | Database name | `soulsync_db` |
| `JWT_SECRET_KEY` | JWT signing secret | `your-secret-key` |
| `JWT_ALGORITHM` | JWT algorithm | `HS256` |
| `JWT_EXPIRE_MINUTES` | Token expiration | `10080` (7 days) |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection | `redis://localhost:6379` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Log format (text/json) | `text` |
| `ENABLE_FILE_LOGGING` | Log to file | `false` |

---

## 📊 API Reference

### Authentication

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/me` | Get current user |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chat` | Send message → AI response |
| GET | `/api/v1/health` | Health check |

**Chat Request:**
```json
{
  "user_id": "user123",
  "message": "Hello, how are you?",
  "use_memory": true,
  "use_rag": true
}
```

**Chat Response:**
```json
{
  "response": "I'm doing great! How can I help you today?",
  "retrieved_memories": [],
  "tasks_created": [],
  "intent": "normal_chat",
  "stored_fact": null
}
```

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{user_id}` | List tasks |
| PUT | `/api/v1/tasks/{id}/complete` | Complete task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

### Memory

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/memory/chat` | Get chat history |
| GET | `/api/v1/memory/facts` | Get personal facts |
| POST | `/api/v1/memory/facts` | Store personal fact |

### Suggestions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/suggestions/{user_id}` | Get suggestions |
| GET | `/api/v1/analysis/{user_id}` | Full analysis |

### Voice

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/voice/transcribe` | Speech to text |
| POST | `/api/v1/voice/speak` | Text to speech |

---

## 🗄️ Database Schema

### MongoDB Collections

#### users
```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  email: String (unique),
  password: String (hashed),
  name: String,
  created_at: DateTime
}
```

#### conversations
```javascript
{
  _id: ObjectId,
  conversation_id: String (unique),
  user_id: String,
  title: String,
  first_message_at: DateTime,
  last_message_at: DateTime
}
```

#### messages
```javascript
{
  _id: ObjectId,
  message_id: String (unique),
  conversation_id: String,
  user_id: String,
  role: String (user/assistant),
  content: String,
  created_at: DateTime
}
```

#### memories (Personal Facts)
```javascript
{
  _id: ObjectId,
  memory_id: String (unique),
  user_id: String,
  key: String,
  value: String,
  context: String,
  created_at: DateTime
}
```

#### tasks
```javascript
{
  _id: ObjectId,
  task_id: String (unique),
  user_id: String,
  title: String,
  status: String (pending/completed/deleted),
  priority: String (high/medium/low),
  due_date: String,
  created_at: DateTime
}
```

#### activities
```javascript
{
  _id: ObjectId,
  activity_id: String (unique),
  user_id: String,
  raw_text: String,
  emotion: String,
  activity: String,
  status: String,
  productivity: String,
  created_at: DateTime
}
```

---

## 👨‍💻 Development Guidelines

### Coding Standards

#### Python (Backend)
- Follow [PEP 8](https://pep8.org/) style guide
- Use type hints for all functions
- Add docstrings to all public functions
- Use the logging module (not print)
- Handle errors with specific exceptions

#### JavaScript/React (Frontend)
- Use functional components with hooks
- Add JSDoc comments for complex functions
- Follow Airbnb React/JSX style guide
- Use PropTypes for component validation

### Logging

The application uses a centralized logging system:

```python
from backend.utils.logging_config import get_logger

logger = get_logger("my_module")
logger.info("Information message")
logger.warning("Warning message")
logger.error("Error message")
```

### Git Workflow

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: description"`
3. Push to remote: `git push origin feature/your-feature`
4. Create a Pull Request on GitHub

---

## 🐳 Deployment

### Docker Compose

```bash
cd soulsync-ai
docker-compose up --build
```

Services:
- `soulsync-backend` → FastAPI on port 8000
- `soulsync-frontend` → Nginx on port 80
- `soulsync-mongodb` → MongoDB on port 27017

### Kubernetes

```bash
minikube start
bash k8s/deploy.sh
```

### Production Considerations

- Use environment variables for all secrets
- Enable HTTPS/TLS
- Set up proper monitoring and logging
- Configure backup strategies for MongoDB
- Use a production-grade Redis instance
- Set appropriate resource limits

---

## 🔧 Troubleshooting

### Common Issues

#### "ModuleNotFoundError: No module named 'backend'"
```bash
# Make sure you're in the soulsync-ai directory
cd soulsync-ai
# Activate virtual environment
source ../venv/bin/activate  # or venv\Scripts\activate on Windows
```

#### "MongoDB connection failed"
```bash
# Check if MongoDB is running
# macOS: brew services list
# Linux: sudo systemctl status mongod
# Windows: Check Services

# Start MongoDB if not running
# macOS: brew services start mongodb-community
# Linux: sudo systemctl start mongod
```

#### "GROQ_API_KEY is not set"
- Make sure your `.env` file is in the `soulsync-ai` directory
- Check that `GROQ_API_KEY` is set correctly
- Restart the backend after changing `.env`

#### "Port already in use"
```bash
# Find and kill process on port 8000 or 5173
# macOS/Linux: lsof -ti:8000 | xargs kill -9
# Windows: netstat -ano | findstr :8000
```

#### "Cannot connect to backend"
- Make sure backend is running on port 8000
- Check `VITE_API_URL` in `soulsync-frontend/.env`
- Should be: `VITE_API_URL=http://localhost:8000`

### Getting Help

1. Check the [API Documentation](http://localhost:8000/docs)
2. Review backend logs for error messages
3. Check browser console for frontend errors
4. Search [GitHub Issues](https://github.com/intsurjeetkaran-droid/SoulSync/issues)

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/your-username/SoulSync.git`
3. **Create a branch**: `git checkout -b feature/your-feature`
4. **Make changes** following our coding standards
5. **Test** your changes thoroughly
6. **Commit** with clear messages: `git commit -m "feat: add new feature"`
7. **Push** to your fork: `git push origin feature/your-feature`
8. **Create a Pull Request** on GitHub

### Contribution Guidelines

- Follow the coding standards outlined above
- Add tests for new features
- Update documentation as needed
- Keep pull requests focused and manageable
- Be respectful and constructive in discussions

### First-Time Contributors

Look for issues labeled:
- `good first issue` - Perfect for beginners
- `help wanted` - Need extra hands
- `documentation` - Improve docs

---

## 👨‍💻 Developers

<table>
  <tr>
    <td align="center">
      <b>Surjeet Karan</b><br/>
      <sub>Lead Developer & Architect</sub><br/>
      <sub>Built SoulSync AI from concept to production</sub><br/>
      <sub>📅 April 23, 2026</sub>
    </td>
  </tr>
</table>

**Responsibilities:**
- System architecture and design
- All backend modules (Core AI, Memory, RAG, Processing, Tasks, Auth)
- React frontend with Tailwind CSS and Framer Motion
- Multi-language support (English, Hindi, Hinglish)
- Groq API integration and AI persona
- RAG pipeline with FAISS vector search
- Docker + Kubernetes deployment
- Documentation

---

## 📋 Module Status

| # | Module | Status | Key Technology |
|---|---|---|---|
| 1 | Core AI (Groq) | 🟢 Complete | Groq API, llama-3.3-70b-versatile |
| 2 | Language Detection | 🟢 Complete | Pattern-based, English/Hindi/Hinglish |
| 3 | Memory System | 🟢 Complete | MongoDB, motor, permanent storage |
| 4 | Personal Info Store | 🟢 Complete | MongoDB memories collection |
| 5 | Intent Detection | 🟢 Complete | Regex classifier — 4 intents |
| 6 | Memory Processing | 🟢 Complete | Rule-based NLP extraction |
| 7 | Retrieval (RAG) | 🟢 Complete | FAISS top-5, keyword fallback |
| 8 | Suggestion Engine | 🟢 Complete | Pandas, NumPy, rule-based |
| 9 | Task Module | 🟢 Complete | NLP detection, MongoDB CRUD |
| 10 | Authentication | 🟢 Complete | JWT, bcrypt, signup/login |
| 11 | Frontend App | 🟢 Complete | React, Vite, Tailwind, Framer Motion |
| 12 | Landing Page | 🟢 Complete | Hero, Features, Carousel, CTA |
| 13 | Deployment | 🟢 Complete | Docker, Kubernetes, Nginx |

---

## 🔐 Privacy & Security

- Passwords are **bcrypt-hashed** — never stored in plain text
- **JWT authentication** — every API request requires a valid token
- Each user's memory is **fully isolated** — no cross-user data leakage
- **MongoDB** — database with encryption at rest (Atlas)
- User can delete any memory or task at any time
- API endpoints validate all inputs with Pydantic
- CORS configured for allowed origins

---

## 🚀 Future Roadmap

- [x] Multi-user support with JWT authentication
- [x] Groq API integration (sub-second responses)
- [x] Multi-language support (English, Hindi, Hinglish)
- [x] Intent detection (store / query / task / chat)
- [x] Structured personal info memory
- [x] Chronological memory recall
- [x] Premium landing page with animations
- [ ] Voice Mode UI integration
- [ ] Emotion detection from voice tone
- [ ] Deep personality modeling
- [ ] Calendar and app integrations
- [ ] AI-generated life plans
- [ ] Mobile app (React Native)
- [ ] Cloud deployment (AWS / GCP)
- [ ] Real-time WebSocket chat

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

<div align="center">

**SoulSync AI** — *Your second brain, your personal guide, your AI companion.*

Built with ❤️ by **Surjeet Karan** · April 23, 2026

</div>