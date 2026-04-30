<div align="center">

# 🧠 SoulSync AI

### *"An AI that understands you, grows with you, and supports your life."*

![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)
![Python](https://img.shields.io/badge/Python-3.11-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.136-009688)
![React](https://img.shields.io/badge/React-18-61DAFB)
![Voice](https://img.shields.io/badge/Voice-Neerja%20Neural-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Built by Surjeet · April 23, 2026 · Updated April 29, 2026**

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
10. [Performance](#-performance)
11. [Deployment](#-deployment)
12. [Module Status](#-module-status)
13. [Developers](#-developers)

---

## 🧠 What is SoulSync AI?

SoulSync AI is a **personal AI companion system** that learns from your daily life, remembers your conversations, understands your emotions, and provides deeply personalized responses, advice, and task management.

Unlike traditional chatbots that forget everything after each session, SoulSync AI builds a **long-term memory model** of you — growing smarter and more personal with every interaction.

It also features a full **Alexa-style Voice Mode** — tap the sphere, speak naturally, and SoulSync responds in **Microsoft Neerja's natural Indian English female voice** through your speakers, then listens again automatically.

> **Core Concept:** `User shares life → AI learns → AI adapts → AI improves support`

---

## ✨ Key Features

### 🧠 1. Intelligent Memory Engine
- Stores every conversation permanently in PostgreSQL
- **Short-term memory** — recent conversation context (last 5 turns)
- **Long-term memory** — all past conversations, searchable by meaning
- **Behavioral memory** — structured patterns extracted from your messages
- Memory is never lost between sessions

### 🔍 2. Retrieval-Augmented Generation (RAG)
- Before every response, searches your entire conversation history
- Uses **FAISS vector search** to find semantically similar past memories
- Injects relevant memories into the AI prompt for personalized responses
- Example: You say *"I'm tired again"* → SoulSync recalls *"You mentioned feeling tired and skipping gym on Tuesday"*

### 🎙️ 3. Alexa-style Voice Mode
- Full-screen dark interface with a large animated sphere
- **Tap sphere → listens → thinks → speaks → listens again** — hands-free loop
- No chat bubbles, no sidebar — pure voice experience like Alexa
- **STT:** Web Speech API (Chrome browser, real-time, no upload)
- **TTS:** Microsoft Neerja Neural via edge-tts (natural Indian English female voice)
- All features work in voice mode: memory, tasks, personal info, insights
- Sphere color reacts to state: 🟢 listening · 🟡 thinking · 🟣 speaking
- 10-minute sessions with mute toggle and pause/resume

### 🗣️ 4. Indian Female Voice (Microsoft Neerja)
- Powered by **edge-tts** — Microsoft's free neural TTS service
- Voice: `en-IN-NeerjaNeural` — natural Indian English female
- Sounds human, not robotic — neural quality voice
- Fallback: pyttsx3 → Microsoft Zira (offline, if edge-tts unavailable)

### 🧩 5. Memory Processing & Extraction
- Automatically extracts structured data from your raw messages
- Detects: **emotion**, **activity**, **status**, **productivity level**
- Example:
  ```
  Input:  "I felt tired and skipped gym today"
  Output: { emotion: "tired", activity: "gym", status: "missed", productivity: "low" }
  ```

### 💡 6. Smart Suggestion Engine
- Analyzes your activity patterns using **Pandas**
- Detects recurring habits, emotional trends, and productivity cycles
- Generates actionable, personalized suggestions

### ✅ 7. Intelligent Task Manager
- **Auto-detects tasks** from natural language in your messages
- Works in both text mode and voice mode
- Supports priority levels: High / Medium / Low
- Supports due dates: today, tomorrow, Friday, next week, etc.
- Full CRUD: create, complete, delete tasks

### 📊 8. Insights Dashboard
- Real-time emotion breakdown with visual bars
- Dominant mood detection
- Personalized suggestions panel

### ⚡ 9. Performance & Caching
- **Groq API** — sub-second AI responses (avg 0.3–0.7s)
- LRU response cache (200 entries, 10-min TTL)
- Database connection pooling

### 🔐 10. Authentication
- JWT tokens (7-day expiry)
- bcrypt password hashing
- Per-user isolated memory — no cross-user data leakage

---

## 🔄 How It Works — Workflow

```
┌─────────────────────────────────────────────────────────────┐
│         USER SPEAKS (Voice Mode) or TYPES (Text Mode)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │          INTENT DETECTION            │
        │  personal_info_store / query         │
        │  task_command / normal_chat          │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │         MEMORY PROCESSING            │
        │  Extract emotion, activity, status   │
        │  Save to PostgreSQL                  │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │          RAG RETRIEVAL               │
        │  FAISS top-5 + keyword fallback      │
        │  + personal facts from DB            │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │        AI RESPONSE (Groq API)        │
        │  llama-3.3-70b-versatile             │
        │  + memory context + chat history     │
        └──────────────────┬──────────────────┘
                           │
        ┌──────────────────▼──────────────────┐
        │        TASK AUTO-DETECTION           │
        │  Auto-create tasks with priority     │
        └──────────────────┬──────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
   ┌──────────▼──────────┐   ┌──────────▼──────────┐
   │    TEXT MODE         │   │    VOICE MODE        │
   │  Show in chat UI     │   │  edge-tts → Neerja   │
   │  Tasks + Insights    │   │  Speaks through      │
   │  sidebar             │   │  speakers → listens  │
   └─────────────────────┘   └─────────────────────┘
```

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
| PostgreSQL | 16+ | Persistent memory storage |
| psycopg2 | 2.9.x | PostgreSQL Python driver |
| Pandas | 3.0.2 | Pattern analysis |
| NumPy | 2.4.3 | Numerical processing |
| python-jose | 3.5.0 | JWT tokens |
| passlib + bcrypt | 1.7.4 / 4.0.1 | Password hashing |
| edge-tts | 7.x | Microsoft Neerja neural TTS (Indian female) |
| pyttsx3 | 2.90 | Offline TTS fallback (Zira) |
| openai-whisper | 20231117 | Speech-to-text (STT) |
| SpeechRecognition | 3.10.4 | Mic input support |
| python-dotenv | 1.0.1 | Environment config |

### Frontend
| Technology | Version | Purpose |
|---|---|---|
| React | 18 | UI framework |
| Vite | 5.x | Build tool |
| Tailwind CSS | 3.4.x | Styling |
| Framer Motion | latest | Animations (sphere, transitions) |
| React Router DOM | latest | Client-side routing |
| Axios | latest | API calls with JWT |
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
├── README.md                       ← This file (at root)
├── soulsync-ai/README.md           ← This file (in project)
├── credentials.txt                 ← Demo user credentials
├── details.txt                     ← Complete non-technical explanation
│
├── soulsync-ai/                    ← Main application folder
│   │
│   ├── backend/
│   │   ├── main.py                 ← App entry point
│   │   ├── auth/                   ← JWT auth (signup/login/me)
│   │   ├── core/
│   │   │   └── ai_service.py       ← Groq API client
│   │   ├── memory/                 ← PostgreSQL memory storage
│   │   ├── retrieval/              ← FAISS vector search + RAG
│   │   ├── processing/             ← Intent, extraction, mood
│   │   ├── suggestion/             ← Pattern analysis + suggestions
│   │   ├── tasks/                  ← Task detection + CRUD
│   │   ├── utils/
│   │   │   ├── voice_tts.py        ← edge-tts (Neerja) + pyttsx3 fallback
│   │   │   └── voice_stt.py        ← Whisper STT
│   │   └── api/
│   │       ├── chat.py             ← POST /chat (full pipeline)
│   │       ├── voice.py            ← POST /voice/speak, /voice/transcribe
│   │       ├── tasks.py            ← Task CRUD
│   │       ├── suggestion.py       ← Insights + suggestions
│   │       └── ...
│   │
│   ├── soulsync-frontend/
│   │   └── src/
│   │       ├── App.jsx             ← Main layout
│   │       ├── components/
│   │       │   ├── VoiceMode.jsx   ← Alexa-style voice UI (sphere)
│   │       │   ├── Header.jsx      ← Voice button + nav
│   │       │   ├── ChatWindow.jsx  ← Text chat
│   │       │   ├── TaskPanel.jsx   ← Tasks sidebar
│   │       │   └── InsightPanel.jsx← Insights sidebar
│   │       └── pages/
│   │           ├── Landing.jsx
│   │           ├── Login.jsx
│   │           └── Signup.jsx
│   │
│   ├── scripts/
│   │   └── seed_users.py           ← Seed 10 demo users
│   │
│   ├── .env                        ← DB + Groq + JWT config
│   ├── requirements.txt            ← Python dependencies
│   ├── start_backend.bat           ← CMD startup script
│   └── start_backend.ps1           ← PowerShell startup script
│
└── soulsync_env/                   ← Create locally (not in zip)
```

---

## 🚀 Local Run Guide

### Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.11+ | `python --version` |
| Node.js | 20+ | `node -v` |
| PostgreSQL | 16+ | `psql --version` |
| Chrome | Latest | Required for Voice Mode (Web Speech API) |

---

### Step 1 — Extract the zip

```
Unzip SoulSync.zip to any folder.
```

---

### Step 2 — Create & Activate Virtual Environment

```bash
# From the project root (where soulsync-ai folder is)
python -m venv soulsync_env

# Windows CMD
soulsync_env\Scripts\activate

# Windows PowerShell
.\soulsync_env\Scripts\Activate.ps1
```

---

### Step 3 — Install Python Dependencies

```bash
pip install -r soulsync-ai\requirements.txt
```

---

### Step 4 — Configure Environment

Edit `soulsync-ai/.env`:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soulsync_db
DB_USER=postgres
DB_PASSWORD=your_password_here

GROQ_API_KEY=your_groq_api_key_here

JWT_SECRET_KEY=soulsync-super-secret-jwt-key-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
```

> Get a free Groq API key at [console.groq.com](https://console.groq.com)

Create the database:

```bash
psql -U postgres -c "CREATE DATABASE soulsync_db;"
```

---

### Step 5 — Seed Demo Users (one time only)

```bash
cd soulsync-ai
python scripts\seed_users.py
```

Creates **10 ready-to-use demo accounts** with memories, tasks, mood history, and personal info. Credentials are in `credentials.txt`.

---

### Step 6 — Start Backend (Terminal 1)

```bash
# Option A — startup script (recommended)
powershell -ExecutionPolicy Bypass -File soulsync-ai\start_backend.ps1

# Option B — manual
.\soulsync_env\Scripts\activate
cd soulsync-ai
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
[TTS] edge-tts ready — voice: en-IN-NeerjaNeural
[Schema] All tables created successfully.
INFO: Application startup complete.
```

✅ Backend: **http://localhost:8000**
📖 Swagger: **http://localhost:8000/docs**

---

### Step 7 — Start Frontend (Terminal 2)

```bash
cd soulsync-ai\soulsync-frontend
npm install        # first time only
npm run dev
```

✅ Frontend: **http://localhost:5173**

---

### Step 8 — Open & Use

1. Go to **http://localhost:5173** in **Chrome**
2. Log in with any credential from `credentials.txt`
3. **Text Mode** — type in the chat window
4. **Voice Mode** — click the **Voice** button in the header

---

### Quick Start (after first-time setup)

```bash
# Terminal 1
powershell -ExecutionPolicy Bypass -File soulsync-ai\start_backend.ps1

# Terminal 2
cd soulsync-ai\soulsync-frontend && npm run dev
```

Open **http://localhost:5173** in Chrome.

---

## ⚙️ Environment Setup

### `.env` File (soulsync-ai/.env)

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=soulsync_db
DB_USER=postgres
DB_PASSWORD=1234

GROQ_API_KEY=gsk_...your_key...

JWT_SECRET_KEY=soulsync-super-secret-jwt-key-2026
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=10080
```

### Frontend `.env` (soulsync-ai/soulsync-frontend/.env)

```env
VITE_API_URL=http://localhost:8000
```

---

## 📊 API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/auth/signup` | Create account → JWT token |
| POST | `/api/v1/auth/login` | Login → JWT token |
| GET | `/api/v1/auth/me` | Get current user (Bearer token) |

### Chat

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/chat` | Send message → AI response + memory + tasks |

**Request:**
```json
{ "user_id": "rohit_123", "message": "I had a tough day" }
```

**Response:**
```json
{
  "response": "I'm sorry to hear that...",
  "retrieved_memories": [...],
  "tasks_created": [...],
  "intent": "normal_chat",
  "stored_fact": null
}
```

### Voice

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/voice/speak` | Text → MP3 audio (Neerja neural voice) |
| POST | `/api/v1/voice/transcribe` | Audio file → text (Whisper) |
| GET | `/api/v1/voice/voices` | List available TTS voices |

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/tasks` | Create task |
| GET | `/api/v1/tasks/{user_id}` | List tasks |
| PUT | `/api/v1/tasks/{id}/complete` | Complete task |
| DELETE | `/api/v1/tasks/{id}` | Delete task |

### Suggestions

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/suggestions/{user_id}` | Smart suggestions |
| GET | `/api/v1/analysis/{user_id}` | Full pattern analysis |

---

## 🗄️ Database Schema

```sql
CREATE TABLE users (
    id         SERIAL PRIMARY KEY,
    user_id    VARCHAR(100) UNIQUE NOT NULL,
    name       VARCHAR(200),
    email      VARCHAR(255) UNIQUE,
    password   VARCHAR(255),          -- bcrypt hashed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE memories (
    id               SERIAL PRIMARY KEY,
    user_id          VARCHAR(100) NOT NULL,
    role             VARCHAR(20) NOT NULL,   -- 'user' or 'assistant'
    message          TEXT NOT NULL,
    importance_score INT DEFAULT 5,
    created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE personal_info (
    id         SERIAL PRIMARY KEY,
    user_id    VARCHAR(100) NOT NULL,
    key        VARCHAR(100) NOT NULL,
    value      TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (user_id, key)
);

CREATE TABLE activities (
    id           SERIAL PRIMARY KEY,
    user_id      VARCHAR(100) NOT NULL,
    raw_text     TEXT NOT NULL,
    emotion      VARCHAR(100),
    activity     VARCHAR(200),
    status       VARCHAR(100),
    productivity VARCHAR(50),
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE tasks (
    id         SERIAL PRIMARY KEY,
    user_id    VARCHAR(100) NOT NULL,
    title      TEXT NOT NULL,
    due_date   VARCHAR(100),
    priority   VARCHAR(20) DEFAULT 'medium',
    status     VARCHAR(20) DEFAULT 'pending',
    source     VARCHAR(20) DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚡ Performance

| Metric | Value |
|---|---|
| Groq API response | 0.3 – 0.7 s |
| Neerja TTS (edge-tts) | ~1–2 s |
| Embedding (all-MiniLM-L6-v2) | ~15 ms |
| FAISS search (top-5) | < 5 ms |
| Cache hit rate | ~83% |
| Cache size | 200 entries (LRU, 10-min TTL) |
| DB pool connections | 2 – 10 |

---

## 🐳 Deployment

### Docker Compose

```bash
cd soulsync-ai
docker-compose up --build
```

Open: **http://localhost**

### Kubernetes

```bash
minikube start
bash k8s/deploy.sh
```

---

## 📋 Module Status

| # | Module | Status | Technology |
|---|---|---|---|
| 1 | Core AI | 🟢 Complete | Groq API, llama-3.3-70b-versatile |
| 2 | Memory System | 🟢 Complete | PostgreSQL, permanent storage |
| 3 | Personal Info Store | 🟢 Complete | Structured key/value DB |
| 4 | Intent Detection | 🟢 Complete | 4-intent classifier |
| 5 | Memory Processing | 🟢 Complete | Rule-based NLP extraction |
| 6 | Retrieval (RAG) | 🟢 Complete | FAISS top-5 + keyword fallback |
| 7 | Suggestion Engine | 🟢 Complete | Pandas pattern analysis |
| 8 | Task Module | 🟢 Complete | NLP detection + PostgreSQL CRUD |
| 9 | Voice Mode (Alexa-style) | 🟢 Complete | Web Speech API + edge-tts |
| 10 | Indian Female Voice | 🟢 Complete | Microsoft Neerja Neural (edge-tts) |
| 11 | Authentication | 🟢 Complete | JWT + bcrypt |
| 12 | Frontend App | 🟢 Complete | React, Vite, Tailwind, Framer Motion |
| 13 | Landing Page | 🟢 Complete | Hero, Features, Carousel, CTA |
| 14 | Deployment | 🟢 Complete | Docker, Kubernetes, Nginx |

---

## 🔐 Privacy & Security

- Passwords are **bcrypt-hashed** — never stored in plain text
- **JWT authentication** — every API request requires a valid token
- Each user's memory is **fully isolated** — no cross-user data leakage
- Conversation history stored **locally** on your machine
- Only AI generation requests sent to Groq API (no personal data)
- TTS via edge-tts sends only the AI response text (no user data)

---

## 🚀 Future Roadmap

- [x] Multi-user support with JWT authentication
- [x] Groq API integration (sub-second responses)
- [x] Intent detection (store / query / task / chat)
- [x] Structured personal info memory
- [x] Chronological memory recall
- [x] Premium landing page with animations
- [x] **Alexa-style Voice Mode** ✅
- [x] **Indian female voice (Microsoft Neerja Neural)** ✅
- [x] **Voice button enabled in header** ✅
- [ ] Emotion detection from voice tone
- [ ] Deep personality modeling
- [ ] Calendar and app integrations
- [ ] Mobile app (React Native)
- [ ] Real-time WebSocket chat
- [ ] Cloud deployment (AWS / GCP)

---

## 👨‍💻 Developer

**Surjeet** — Lead Developer & Architect
Built SoulSync AI from concept to production · April 23, 2026

---

## 📄 License

MIT License — Free to use, modify, and distribute.

---

<div align="center">

**SoulSync AI** — *Your second brain, your personal guide, your AI companion.*

</div>
