<div align="center">

# 🧠 SoulSync AI

### *"An AI that understands you, grows with you, and supports your life."*

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Built by [Surjeet Karan](https://github.com/surjeetkaran) · April 23, 2026**

</div>

---

## 📌 Table of Contents

1. [What is SoulSync AI?](#-what-is-soulsync-ai)
2. [Key Features](#-key-features)
3. [How It Works](#-how-it-works--workflow)
4. [Tech Stack](#-tech-stack)
5. [Project Structure](#-project-structure)
6. [Local Run Guide](#-local-run-guide)
7. [Environment Setup](#-environment-setup)
8. [API Reference](#-api-reference)
9. [Database Schema](#-database-schema)
10. [Test Scripts](#-test-scripts)
11. [Performance](#-performance--optimization)
12. [Deployment](#-deployment)
13. [Developers](#-developers)

---

## 🧠 What is SoulSync AI?

SoulSync AI is a **personal AI companion system** that learns from your daily life, remembers your conversations, understands your emotions, and provides deeply personalized responses, advice, and task management.

Unlike traditional chatbots that forget everything after each session, SoulSync AI builds a **long-term memory model** of you — growing smarter and more personal with every interaction.

> **Core Concept:** `User shares life → AI learns → AI adapts → AI improves support`

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
  - *"You're on a productivity streak — document what's working!"*

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
- **Hinglish support** — understands Hindi words written in Roman script
- **Language-aware prompts** — system instructions adapt to detected language
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
- Database connection pooling (2–10 connections)
- FAISS vector search with relevance threshold filtering

### 🌐 9. Modern Web Interface
- Built with **React + Vite + Tailwind CSS + Framer Motion**
- Emerald/amber/charcoal premium color palette
- Animated landing page with use-case carousel
- Real-time chat with typing indicator
- Task panel with priority sorting
- Insights panel with emotion charts
- Multi-language support (English, Hindi, Hinglish)
- Clean chat window on every login (session-isolated state)

### 🐳 10. Production-Ready Deployment
- Full **Docker Compose** setup (3 services)
- **Kubernetes** manifests for scaling
- Nginx reverse proxy for frontend
- Health checks on all services

---

## 🔄 How It Works — Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│              USER SENDS A MESSAGE (text input)                  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         LANGUAGE DETECTION               │
          │  Detect: English, Hindi, or Hinglish    │
          │  Pattern-based (instant, no API call)   │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │           INTENT DETECTION               │
          │  Classify: personal_info_store           │
          │            personal_info_query           │
          │            task_command                  │
          │            normal_chat                   │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         MEMORY PROCESSING                │
          │  Extract: emotion, activity, status,     │
          │  productivity → Save to MongoDB           │
          │  Personal facts → memories collection    │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         VECTOR STORE (FAISS)             │
          │  Embed message → Store in user's         │
          │  personal FAISS index on disk            │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │           RAG RETRIEVAL                  │
          │  Personal facts (DB) + FAISS top-5       │
          │  + keyword fallback if FAISS misses      │
          │  + chronological recall for "first X"    │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         AI RESPONSE (Groq API)           │
          │  llama-3.3-70b-versatile + memory ctx   │
          │  + language instruction + chat history   │
          │  → personalized response in user's lang  │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │           TASK AUTO-DETECTION            │
          │  Intent = task_command only              │
          │  → Auto-create tasks with priority       │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         SAVE TO MEMORY (DB)              │
          │  Store conversation turn in MongoDB      │
          │  + add to FAISS vector index             │
          └────────────────────┬────────────────────┘
                               │
          ┌────────────────────▼────────────────────┐
          │         FRONTEND DISPLAY                 │
          │  Response + memories recalled + tasks    │
          │  created + intent shown in React UI      │
          └─────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

### Backend
| Technology | Version | Purpose |
|---|---|---|
| Python | 3.11+ | Core language |
| FastAPI | 0.136.0 | REST API framework |
| Groq API | llama-3.3-70b-versatile | AI response generation (cloud, sub-second) |
| sentence-transformers | 3.4.1 | Text embeddings for RAG (all-MiniLM-L6-v2) |
| FAISS | 1.13.0 | Vector similarity search |
| MongoDB | 6+ | Persistent memory storage (Atlas cloud) |
| motor | 3.6.0 | MongoDB async Python driver |
| pymongo | 4.9.x | MongoDB sync Python driver |
| Pandas | 3.0.2 | Pattern analysis |
| NumPy | 2.4.3 | Numerical processing |
| python-jose | 3.5.0 | JWT token generation & verification |
| passlib + bcrypt | 1.7.4 / 4.0.1 | Password hashing |
| redis | 5.2.1 | Response caching (optional) |
| edge-tts | latest | Microsoft Neerja neural TTS (Indian female voice) |
| openai-whisper | 20231117 | Speech recognition |
| python-dotenv | 1.0.1 | Environment config |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | 5.x | Build tool |
| Tailwind CSS | 3.4.x | Styling (emerald/amber/charcoal palette) |
| Framer Motion | latest | Animations — landing page, carousel, voice sphere |
| React Router DOM | latest | Client-side routing (landing / login / signup / app) |
| Axios | latest | API calls with JWT auto-injection |
| Lucide React | latest | Icons |
| react-hot-toast | latest | Notifications |

### Infrastructure
| Technology | Purpose |
|---|---|
| Docker | Containerization |
| Docker Compose | Local multi-service orchestration |
| Kubernetes | Production deployment + scaling |
| Nginx | Frontend serving + API proxy |

---

## 📁 Project Structure

```
SoulSync/                           ← Repository root
│
├── README.md                       ← This file
├── credentials.txt                 ← Demo user credentials (generated by seed script)
├── details.txt                     ← Complete non-technical project explanation
├── .gitignore
│
├── soulsync-ai/                    ← Main application folder
│   │
│   ├── backend/                    ← Python FastAPI backend
│   │   ├── main.py                 ← App entry point, router registration, DB init
│   │   │
│   │   ├── auth/
│   │   │   ├── models.py           ← User CRUD, bcrypt hashing
│   │   │   ├── routes.py           ← POST /auth/signup, /auth/login, GET /auth/me
│   │   │   ├── security.py         ← JWT create/decode, bcrypt hash/verify
│   │   │   └── dependencies.py     ← FastAPI JWT dependency (get_current_user)
│   │   │
│   │   ├── core/
│   │   │   ├── ai_service.py       ← Groq API client, generate_response(), language-aware
│   │   │   └── model.py            ← Re-exports generate_response (backward compat)
│   │   │
│   │   ├── memory/
│   │   │   ├── database.py         ← MongoDB connection & indexes
│   │   │   ├── schema.py           ← MongoDB collection schemas
│   │   │   ├── memory_manager.py   ← Save/fetch memories, chat history, earliest recall
│   │   │   └── personal_info.py    ← Structured key/value facts store
│   │   │
│   │   ├── retrieval/
│   │   │   ├── embedder.py         ← Text → 384-dim vectors (all-MiniLM-L6-v2)
│   │   │   ├── vector_store.py     ← FAISS index per user (disk-persisted)
│   │   │   └── rag_engine.py       ← Intent-aware RAG pipeline
│   │   │
│   │   ├── processing/
│   │   │   ├── extractor.py        ← Rule-based extraction (emotion, activity, status)
│   │   │   ├── activity_store.py   ← Save/fetch structured activity data
│   │   │   ├── intent_detector.py  ← 4-intent classifier (store/query/task/chat)
│   │   │   ├── language_detector.py← Multi-language detection (English/Hindi/Hinglish)
│   │   │   ├── mood_predictor.py   ← Mood logging + pattern prediction
│   │   │   └── scorer.py           ← Memory importance scoring (0-15 scale)
│   │   │
│   │   ├── suggestion/
│   │   │   ├── analyzer.py         ← Pandas pattern analysis
│   │   │   └── suggestion_engine.py← Rule-based suggestion generation
│   │   │
│   │   ├── tasks/
│   │   │   ├── task_detector.py    ← Strict NLP task detection
│   │   │   └── task_manager.py     ← Task CRUD + auto-create from chat
│   │   │
│   │   ├── utils/
│   │   │   ├── cache.py            ← LRU response cache (200 entries, 10min TTL)
│   │   │   ├── db_pool.py          ← MongoDB connection pool
│   │   │   ├── voice_stt.py        ← Whisper STT
│   │   │   └── voice_tts.py        ← edge-tts (Neerja) + pyttsx3 fallback
│   │   │
│   │   └── api/
│   │       ├── chat.py             ← POST /chat (intent-aware RAG + memory + tasks)
│   │       ├── memory.py           ← POST /save-memory, GET /get-memory
│   │       ├── processing.py       ← POST /process-memory, GET /get-activities
│   │       ├── suggestion.py       ← GET /suggestions, GET /analysis
│   │       ├── tasks.py            ← Full task CRUD + auto-detect
│   │       ├── voice.py            ← Voice endpoints (future use)
│   │       ├── optimization.py     ← Cache stats, model info
│   │       └── unique_features.py  ← Memory scoring, mood logging
│   │
│   ├── soulsync-frontend/          ← React + Tailwind CSS frontend
│   │   ├── src/
│   │   │   ├── App.jsx             ← Main app layout + session reset
│   │   │   ├── main.jsx            ← Router, AuthProvider
│   │   │   ├── context/
│   │   │   │   └── AuthContext.jsx ← JWT auth state, login/signup/logout
│   │   │   ├── api/
│   │   │   │   └── soulsync.js     ← Axios client with JWT auto-injection
│   │   │   ├── pages/
│   │   │   │   ├── Landing.jsx     ← Landing page (hero, features, carousel, CTA)
│   │   │   │   ├── Login.jsx       ← Login form
│   │   │   │   └── Signup.jsx      ← Signup form with password strength meter
│   │   │   └── components/
│   │   │       ├── Header.jsx      ← Logo + user info + logout
│   │   │       ├── ChatWindow.jsx  ← Message bubbles + typing indicator
│   │   │       ├── ChatInput.jsx   ← Text input + send button
│   │   │       ├── TaskPanel.jsx   ← Task list + create/complete/delete
│   │   │       ├── InsightPanel.jsx← Emotion bars + suggestions
│   │   │       └── UseCaseCarousel.jsx ← Landing page carousel
│   │   ├── package.json
│   │   └── vite.config.js
│   │
│   ├── scripts/
│   │   ├── seed_users.py           ← Seed 5 demo users with full data
│   │   └── verify_seed.py          ← Verify seeded data counts
│   │
│   ├── data/
│   │   └── vectors/                ← FAISS index files per user (auto-created)
│   │
│   ├── docker/
│   │   ├── Dockerfile.backend
│   │   ├── Dockerfile.frontend
│   │   └── nginx.conf
│   │
│   ├── k8s/
│   │   ├── namespace.yaml
│   │   ├── configmap.yaml
│   │   ├── postgres-pvc.yaml
│   │   ├── postgres-deployment.yaml
│   │   ├── backend-deployment.yaml
│   │   ├── frontend-deployment.yaml
│   │   └── deploy.sh
│   │
│   ├── .env                        ← DB + Groq + JWT config (update before running)
│   ├── requirements.txt            ← Python dependencies
│   ├── docker-compose.yml
│   ├── start_backend.bat           ← CMD startup script (enforces venv)
│   └── start_backend.ps1           ← PowerShell startup script (enforces venv)
│
└── soulsync_env/                   ← Python virtual environment (not in repo, create locally)
```

---

## 🚀 Local Run Guide

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node -v` |
| MongoDB Atlas | Cloud account | [Create free cluster](https://www.mongodb.com/cloud/atlas) |

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/intsurjeetkaran-droid/SoulSync.git
cd SoulSync
```

---

### Step 2 — Create & Activate Virtual Environment

```bash
# Create venv
python -m venv soulsync_env

# Windows CMD
soulsync_env\Scripts\activate

# Windows PowerShell
.\soulsync_env\Scripts\Activate.ps1

# Mac / Linux
source soulsync_env/bin/activate
```

---

### Step 3 — Install Python Dependencies

```bash
pip install -r soulsync-ai/requirements.txt
```

---

### Step 4 — Configure Environment

Edit `soulsync-ai/.env` with your MongoDB Atlas connection string:

```env
# Groq API Key
GROQ_API_KEY=your_groq_api_key_here

# JWT Auth
JWT_SECRET_KEY=soulsync-super-secret-jwt-key-change-in-production-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# MongoDB Atlas (Primary Database)
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/soulsync_db?retryWrites=true&w=majority
MONGODB_DB=soulsync_db

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379
REDIS_TTL_CHAT=600
REDIS_TTL_SESSION=86400
REDIS_TTL_DEFAULT=300
```

> **Get MongoDB Atlas:** Create a free cluster at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
> 
> **Get Groq API Key:** Get a free key at [console.groq.com](https://console.groq.com)

---

### Step 5 — Seed Demo Users (one time only)

```bash
cd soulsync-ai
python scripts/seed_users.py
```

This creates **5 ready-to-use demo accounts** with memories, tasks, mood history, and personal info pre-loaded. Credentials are saved to `credentials.txt` at the project root.

---

### Step 6 — Start Backend (Terminal 1)

**Option A — Use the startup script (recommended, enforces venv automatically):**

```bash
# Windows CMD
soulsync-ai\start_backend.bat

# Windows PowerShell
powershell -ExecutionPolicy Bypass -File soulsync-ai\start_backend.ps1
```

**Option B — Manual (activate venv first):**

```bash
.\soulsync_env\Scripts\activate
cd soulsync-ai
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

> ⚠️ **The backend must always run inside `soulsync_env`.** The startup scripts enforce this automatically. If you run with system Python, packages like `groq`, `psycopg2`, and `jose` will be missing.

✅ Backend: **http://localhost:8000**
📖 Swagger docs: **http://localhost:8000/docs**

---

### Step 7 — Start Frontend (Terminal 2)

```bash
cd soulsync-ai\soulsync-frontend
npm install        # first time only
npm run dev
```

✅ Frontend: **http://localhost:5173**

---

### Step 8 — Open & Login

1. Go to **http://localhost:5173**
2. You land on the **Landing Page** — click **Get Started** or **Sign In**
3. Use any credential from `credentials.txt`, e.g.:
   - Email: `rohit@soulsync.ai` · Password: `rohit123`
4. You are redirected to the **Chat App** with all your data loaded

---

### Quick Start (all steps at a glance)

```bash
# Terminal 1 — Backend
powershell -ExecutionPolicy Bypass -File soulsync-ai\start_backend.ps1

# Terminal 2 — Frontend
cd soulsync-ai\soulsync-frontend
npm run dev
```

Then open **http://localhost:5173**

---

## ⚙️ Environment Setup

### `.env` File (soulsync-ai/.env)

```env
# Groq API
GROQ_API_KEY=your_groq_api_key_here

# JWT Auth
JWT_SECRET_KEY=soulsync-super-secret-jwt-key-change-in-production-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080

# MongoDB Atlas (Primary Database)
MONGODB_URL=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/soulsync_db?retryWrites=true&w=majority
MONGODB_DB=soulsync_db

# Redis (Optional - for caching)
REDIS_URL=redis://localhost:6379
REDIS_TTL_CHAT=600
REDIS_TTL_SESSION=86400
REDIS_TTL_DEFAULT=300
```

### MongoDB Collections (auto-created on first run)

| Collection | Purpose |
|---|---|
| `users` | Registered users with auth data |
| `conversations` | Conversation sessions (one per month per user) |
| `messages` | All chat messages (user + assistant) |
| `memories` | Personal facts (key/value pairs) |
| `tasks` | User tasks with priority and status |
| `activities` | Structured extracted data (emotion, activity, status) |
| `mood_logs` | Mood tracking entries |
| `memory_collections` | Typed life events (32 collection types) |

---

## 📊 API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account → returns JWT token |
| POST | `/api/v1/auth/login`  | Login with email + password → returns JWT token |
| GET  | `/api/v1/auth/me`     | Get current user profile (requires Bearer token) |

---

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chat` | Send message → get AI response with RAG + memory |
| GET | `/api/v1/health` | Health check |

**Chat Request Body:**
```json
{
  "user_id": "user_001",
  "message": "I had a tough day today",
  "use_memory": true,
  "use_rag": true
}
```

**Chat Response:**
```json
{
  "user_id": "user_001",
  "message": "I had a tough day today",
  "response": "I'm sorry to hear that...",
  "memory_used": true,
  "rag_used": true,
  "retrieved_memories": [...],
  "tasks_created": [...],
  "intent": "normal_chat",
  "stored_fact": null
}
```

---

### Memory

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/save-memory` | Save a message to memory |
| GET | `/api/v1/get-memory/{user_id}` | Fetch recent memories |

---

### Processing

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/process-memory` | Extract structured data from text |
| GET | `/api/v1/get-activities/{user_id}` | Fetch structured activities |
| GET | `/api/v1/emotion-summary/{user_id}` | Get emotion frequency counts |

---

### Suggestions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/suggestions/{user_id}` | Get smart suggestions |
| GET | `/api/v1/analysis/{user_id}` | Get full pattern analysis |

---

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/tasks` | Create a task manually |
| GET | `/api/v1/tasks/{user_id}` | List all tasks |
| PUT | `/api/v1/tasks/{id}/complete` | Mark task as completed |
| DELETE | `/api/v1/tasks/{id}` | Delete a task |
| POST | `/api/v1/tasks/auto-detect` | Detect + create tasks from text |

---

### Voice

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/voice/transcribe` | Upload audio file → transcribed text (Whisper) |
| POST | `/api/v1/voice/speak` | Text → WAV audio bytes (pyttsx3 TTS) |
| POST | `/api/v1/voice/chat` | Full pipeline: audio in → AI response → audio out |
| GET  | `/api/v1/voice/voices` | List available TTS voices on this system |

> **Note:** Voice endpoints are available but currently not integrated in the frontend UI. Voice mode is disabled in the current version.

---

### Optimization

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/optimize/cache-stats` | View response cache stats |
| POST | `/api/v1/optimize/cache-clear` | Clear response cache |
| GET | `/api/v1/optimize/pool-stats` | View DB connection pool stats |
| GET | `/api/v1/optimize/model-info` | Model + device + ONNX info |
| POST | `/api/v1/optimize/export-onnx` | Export model to ONNX (background) |

---

## 🗄️ Database Schema

```sql
-- Users table (with auth columns)
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    user_id    VARCHAR(100) UNIQUE NOT NULL,
    name       VARCHAR(200),
    email      VARCHAR(255) UNIQUE,
    password   VARCHAR(255),          -- bcrypt hashed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Memories table (all conversations, permanent)
CREATE TABLE memories (
    id               SERIAL PRIMARY KEY,
    user_id          VARCHAR(100) NOT NULL,
    role             VARCHAR(20) NOT NULL,   -- 'user' or 'assistant'
    message          TEXT NOT NULL,
    importance_score INT DEFAULT 5,          -- 0-15 scale
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Personal info table (structured key/value facts)
CREATE TABLE personal_info (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) NOT NULL,
    key         VARCHAR(100) NOT NULL,   -- 'name', 'goal', 'job', etc.
    value       TEXT NOT NULL,
    source_text TEXT,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, key),
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Activities table (structured extracted data)
CREATE TABLE activities (
    id           SERIAL PRIMARY KEY,
    user_id      VARCHAR(100) NOT NULL,
    raw_text     TEXT NOT NULL,
    emotion      VARCHAR(100),
    activity     VARCHAR(200),
    status       VARCHAR(100),
    productivity VARCHAR(50),
    summary      TEXT,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Tasks table
CREATE TABLE tasks (
    id         SERIAL PRIMARY KEY,
    user_id    VARCHAR(100) NOT NULL,
    title      TEXT NOT NULL,
    due_date   VARCHAR(100),
    priority   VARCHAR(20) DEFAULT 'medium',
    status     VARCHAR(20) DEFAULT 'pending',
    source     VARCHAR(20) DEFAULT 'manual',  -- 'manual' or 'auto'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Mood logs table
CREATE TABLE mood_logs (
    id          SERIAL PRIMARY KEY,
    user_id     VARCHAR(100) NOT NULL,
    mood        VARCHAR(50) NOT NULL,
    mood_score  INT NOT NULL,           -- 1-10
    note        TEXT,
    day_of_week VARCHAR(10),
    hour_of_day INT,
    source      VARCHAR(20) DEFAULT 'manual',
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
```

---

## 🧪 Test Scripts

```bash
# Always run from the soulsync-ai/ folder with venv active
.\soulsync_env\Scripts\activate
cd soulsync-ai

# Seed demo users (run this first)
python scripts\seed_users.py

# Verify seeded data
python scripts\verify_seed.py
```

---

## ⚡ Performance

| Metric | Value |
|---|---|
| Groq API response (avg) | 0.3 – 0.7 s |
| Embedding (all-MiniLM-L6-v2) | ~15 ms per text |
| FAISS search (top-5) | < 5 ms |
| Language detection | < 1 ms (pattern-based) |
| Cache hit rate | ~83% |
| Cache size | 200 entries (LRU) |
| Cache TTL | 10 minutes |
| DB pool connections | 2 – 10 |
| Embedding dimension | 384 |
| Supported languages | English, Hindi, Hinglish |

---

## 🐳 Deployment

### Docker Compose (Recommended for local production)

```bash
cd soulsync-ai

# Build and start all services
docker-compose up --build

# Stop all services
docker-compose down
```

Services started:
- `soulsync-postgres` → PostgreSQL 16 on port 5432
- `soulsync-backend`  → FastAPI on port 8000
- `soulsync-frontend` → Nginx on port 80

Open: **http://localhost**

---

### Kubernetes (Production scaling)

```bash
# Prerequisites: kubectl + minikube installed

minikube start
bash k8s/deploy.sh
```

Access:
- Frontend: **http://localhost:30080**
- Backend:  **http://localhost:8000**

---

### Docker Build Only

```bash
# Backend image
docker build -f docker/Dockerfile.backend -t soulsync-backend:latest .

# Frontend image
docker build -f docker/Dockerfile.frontend -t soulsync-frontend:latest .
```

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
| 4 | Personal Info Store | 🟢 Complete | MongoDB memories collection, upsert |
| 5 | Intent Detection | 🟢 Complete | Regex classifier — 5 intents |
| 6 | Memory Processing | 🟢 Complete | Rule-based NLP, activity extraction |
| 7 | Retrieval (RAG) | 🟢 Complete | FAISS top-5, keyword fallback, earliest recall |
| 8 | Suggestion Engine | 🟢 Complete | Pandas, NumPy, rule-based logic |
| 9 | Task Module | 🟢 Complete | Strict NLP detection, MongoDB CRUD |
| 10 | Authentication | 🟢 Complete | JWT, bcrypt, signup/login/me |
| 11 | Frontend App | 🟢 Complete | React, Vite, Tailwind, Framer Motion |
| 12 | Landing Page | 🟢 Complete | Hero, Features, Use-Case Carousel, CTA |
| 13 | Voice Mode | 🟢 Complete | edge-tts (Neerja), Web Speech API |
| 14 | Deployment | 🟢 Complete | Docker, Kubernetes, Nginx, venv enforcement |

---

## 🔐 Privacy & Security

- Passwords are **bcrypt-hashed** — never stored in plain text
- **JWT authentication** — every API request requires a valid token
- Each user's memory is **fully isolated** — no cross-user data leakage
- **MongoDB Atlas** — cloud database with encryption at rest
- User can delete any memory or task at any time
- API endpoints validate all inputs with Pydantic
- CORS configured (tighten `allow_origins` in production)

---

## 🚀 Future Roadmap

- [x] Multi-user support with JWT authentication
- [x] Groq API integration (replaced local models)
- [x] Multi-language support (English, Hindi, Hinglish)
- [x] Automatic language detection (pattern-based)
- [x] Intent detection (store / query / task / chat)
- [x] Structured personal info memory
- [x] Chronological memory recall ("what was my first experience?")
- [x] Premium landing page with animations
- [x] Clean chat window on every login (session-isolated state)
- [x] Venv enforcement (startup scripts)
- [ ] Voice Mode (Whisper + pyttsx3 available, UI integration pending)
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
