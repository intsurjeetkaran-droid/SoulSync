# SoulSync AI - System Architecture

This document provides a comprehensive overview of SoulSync AI's system architecture, designed to help developers understand how different components interact and data flows through the system.

## 📋 Table of Contents

- [System Overview](#system-overview)
- [High-Level Architecture](#high-level-architecture)
- [Data Flow](#data-flow)
- [Component Details](#component-details)
- [Database Schema](#database-schema)
- [API Design](#api-design)
- [Deployment Architecture](#deployment-architecture)
- [Security Considerations](#security-considerations)

## 🎯 System Overview

SoulSync AI is a **personal AI companion system** that learns from user interactions, remembers conversations, and provides personalized responses. The system is built on a **microservices-inspired architecture** with clear separation of concerns.

### Key Characteristics

- **Stateless Backend**: FastAPI services that can scale horizontally
- **Persistent Memory**: MongoDB for long-term storage of conversations and user data
- **Vector Search**: FAISS for semantic memory retrieval (RAG)
- **Real-time Communication**: WebSocket support for voice mode
- **Caching Layer**: Redis for improved performance
- **Multi-language Support**: English, Hindi, and Hinglish

## 🏗️ High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                         │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  Web Browser    │         │  Mobile App     │           │
│  │  (React + Vite) │         │  (Future)       │           │
│  └────────┬────────┘         └────────┬────────┘           │
└───────────┼───────────────────────────┼───────────────────┘
            │                           │
            │         HTTP/HTTPS        │
            │         WebSocket         │
            ▼                           ▼
┌─────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Nginx Reverse Proxy                     │   │
│  │  • SSL Termination    • Load Balancing               │   │
│  │  • Rate Limiting      • CORS Handling                │   │
└──┼─────────────────────────────────────────────────────┘   │
   │                                                          │
   ▼                                                          │
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              FastAPI Backend Services                │   │
│  │                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │   │
│  │  │  Auth Service│  │  Chat Service│  │Task Service│ │   │
│  │  │  • JWT       │  │  • RAG        │  │• CRUD     │ │   │
│  │  │  • OAuth     │  │  • Memory     │  │• Detection│ │   │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │   │
│  │                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌───────────┐ │   │
│  │  │ Voice Service│  │Processing Svc│  │Suggestion │ │   │
│  │  │  • STT       │  │  • NLP        │  │Service    │ │   │
│  │  │  • TTS       │  │  • Extraction │  │• Analytics│ │   │
│  │  └──────────────┘  └──────────────┘  └───────────┘ │   │
│  └─────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────────────────────┘
            │
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                      DATA LAYER                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   MongoDB    │  │    Redis     │  │    FAISS     │     │
│  │  (Primary)   │  │  (Cache)     │  │  (Vectors)   │     │
│  │              │  │              │  │              │     │
│  │ • Users      │  │ • Responses  │  │ • Embeddings │     │
│  │ • Chats      │  │ • Sessions   │  │ • Similarity │     │
│  │ • Tasks      │  │ • Rate Limit │  │ • Search     │     │
│  │ • Memories   │  │              │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Groq API   │  │  Edge TTS    │  │  Whisper     │     │
│  │              │  │              │  │              │     │
│  │ • AI Chat    │  │ • Voice Gen  │  │ • STT Model  │     │
│  │ • Embeddings │  │ • Neerja     │  │ • Transcribe │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└───────────────────────────────────────────────────────────┘
```

## 🔄 Data Flow

### 1. User Message Processing Flow

```
User Input (Text/Voice)
    ↓
[API Gateway] → Rate Limiting & Auth Check
    ↓
[Chat Service] → Intent Detection
    ↓
├─→ Personal Info Store → Save to MongoDB
├─→ Task Command → Task Service → Create Task
├─→ Query → RAG Engine → Retrieve Memories
└─→ Normal Chat → Continue
    ↓
[RAG Engine] → Vector Search (FAISS) + Keyword Search
    ↓
[AI Service] → Groq API → Generate Response
    ↓
[Memory Service] → Save Conversation to MongoDB
    ↓
[Task Detector] → Auto-create Tasks (if applicable)
    ↓
[Response Cache] → Cache Result (Redis)
    ↓
Return Response to Client
```

### 2. Voice Mode Flow

```
User Speaks → Web Speech API (Browser)
    ↓
Audio Blob → Backend /voice/transcribe
    ↓
[Whisper STT] → Transcribe Audio → Text
    ↓
[Chat Processing] → Same as text flow
    ↓
AI Response Text → /voice/speak
    ↓
[Edge TTS] → Generate Audio (Neerja Voice)
    ↓
Return Audio Stream → Browser → Play
    ↓
Auto-listen Again (Loop)
```

## 🧩 Component Details

### Backend Services

#### 1. **Auth Service** (`/backend/auth`)
- **Purpose**: Handle user authentication and authorization
- **Key Functions**:
  - User registration and login
  - JWT token generation and validation
  - Password hashing with bcrypt
  - Session management
- **Dependencies**: MongoDB (users collection)

#### 2. **Chat Service** (`/backend/api/chat.py`)
- **Purpose**: Main conversation handler
- **Key Functions**:
  - Process user messages
  - Orchestrate RAG pipeline
  - Save conversations
  - Return structured responses
- **Flow**: Intent Detection → RAG → AI Generation → Memory Storage

#### 3. **RAG Engine** (`/backend/retrieval/rag_engine.py`)
- **Purpose**: Retrieval-Augmented Generation for personalized responses
- **Key Functions**:
  - Intent-aware routing
  - Vector similarity search (FAISS)
  - Keyword-based fallback search
  - Memory context injection
- **Components**:
  - `vector_store.py`: FAISS index management
  - `rag_engine.py`: Main orchestration logic

#### 4. **Memory Service** (`/backend/memory/memory_manager.py`)
- **Purpose**: Manage conversation history and personal facts
- **Key Functions**:
  - Save/retrieve conversations
  - Store personal information (name, preferences, etc.)
  - Manage chat history context
- **Data Model**: Conversations, Messages, Memories (personal facts)

#### 5. **Processing Service** (`/backend/processing/`)
- **Purpose**: NLP and data extraction
- **Components**:
  - `intent_detector.py`: Classify user intent (4 types)
  - `extractor.py`: Extract structured data from text
  - `mood_predictor.py`: Detect emotions and log mood
  - `language_detector.py`: Identify language (EN/HI/Hinglish)

#### 6. **Task Service** (`/backend/tasks/`)
- **Purpose**: Task management and auto-detection
- **Components**:
  - `task_manager.py`: CRUD operations for tasks
  - `task_detector.py`: NLP-based task detection from messages
- **Features**: Priority levels, due dates, auto-creation

#### 7. **Voice Service** (`/backend/utils/voice_*.py`)
- **Purpose**: Speech-to-text and text-to-speech
- **Components**:
  - `voice_stt.py`: Whisper-based transcription
  - `voice_tts.py`: Edge TTS with Microsoft Neerja voice
- **Features**: Natural Indian English female voice

#### 8. **Suggestion Service** (`/backend/suggestion/suggestion_engine.py`)
- **Purpose**: Generate personalized insights and recommendations
- **Key Functions**:
  - Analyze activity patterns
  - Detect emotional trends
  - Generate actionable suggestions
- **Tools**: Pandas for statistical analysis

### Frontend Components

#### 1. **Main Application** (`App.jsx`)
- **Purpose**: Central orchestrator for the UI
- **Key State**:
  - Messages array
  - User authentication state
  - Sidebar visibility
  - Voice mode status
- **Key Handlers**:
  - `handleSend()`: Process user messages
  - `handleLogout()`: User logout
  - `handleVoiceMessageSent()`: Voice mode callback

#### 2. **Chat Components**
- **ChatWindow**: Display conversation history with message bubbles
- **ChatInput**: Text input with auto-resize and send button
- **MessageRenderer**: Format messages (markdown, links, etc.)

#### 3. **Voice Mode** (`VoiceMode.jsx`)
- **Purpose**: Full-screen voice interaction UI
- **Features**:
  - Animated sphere with state-based colors
  - Web Speech API integration
  - Real-time transcription display
  - Auto-listen loop

#### 4. **Sidebar Components**
- **TaskPanel**: Display and manage tasks
- **InsightPanel**: Show analytics and suggestions
- **Tab System**: Switch between tasks and insights

#### 5. **Authentication** (`AuthContext.jsx`)
- **Purpose**: Global authentication state management
- **Features**:
  - JWT token storage
  - User info persistence
  - Protected route handling

## 🗄️ Database Schema

### MongoDB Collections

#### 1. **users**
```javascript
{
  _id: ObjectId,
  user_id: String (unique),
  email: String (unique),
  password: String (hashed),
  name: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

#### 2. **conversations**
```javascript
{
  _id: ObjectId,
  conversation_id: String (unique),
  user_id: String,
  title: String,
  first_message_at: DateTime,
  last_message_at: DateTime,
  message_count: Number
}
```

#### 3. **messages**
```javascript
{
  _id: ObjectId,
  message_id: String (unique),
  conversation_id: String,
  user_id: String,
  role: String (user/assistant),
  content: String,
  created_at: DateTime,
  metadata: {
    intent: String,
    language: String,
    emotion: String
  }
}
```

#### 4. **memories** (Personal Facts)
```javascript
{
  _id: ObjectId,
  memory_id: String (unique),
  user_id: String,
  key: String,
  value: String,
  context: String,
  confidence: Number,
  created_at: DateTime
}
```

#### 5. **tasks**
```javascript
{
  _id: ObjectId,
  task_id: String (unique),
  user_id: String,
  title: String,
  description: String,
  status: String (pending/completed/deleted),
  priority: String (high/medium/low),
  due_date: String,
  source: String (auto/manual),
  created_at: DateTime,
  completed_at: DateTime
}
```

#### 6. **activities**
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

#### 7. **mood_logs**
```javascript
{
  _id: ObjectId,
  log_id: String (unique),
  user_id: String,
  mood: String,
  intensity: Number,
  note: String,
  created_at: DateTime
}
```

### Redis Cache Structure

```
soulsync:cache:chat:{user_id}:{message_hash} → AI response
soulsync:session:{user_id} → User session data
soulsync:rate_limit:{user_id}:{timestamp} → Rate limiting
```

### FAISS Vector Index

```
Index Structure:
- Dimension: 384 (all-MiniLM-L6-v2 embeddings)
- Metric: Cosine similarity
- Index Type: Flat (L2)
- Stored per user_id for isolation
```

## 🔌 API Design

### RESTful Endpoints

#### Authentication
```
POST   /api/v1/auth/signup      - Create account
POST   /api/v1/auth/login       - Login
GET    /api/v1/auth/me          - Get current user
POST   /api/v1/auth/logout      - Logout
```

#### Chat
```
POST   /api/v1/chat             - Send message (main endpoint)
GET    /api/v1/health           - Health check
```

#### Voice
```
POST   /api/v1/voice/transcribe - Speech to text
POST   /api/v1/voice/speak      - Text to speech (audio stream)
GET    /api/v1/voice/voices     - List available voices
```

#### Tasks
```
POST   /api/v1/tasks            - Create task
GET    /api/v1/tasks/{user_id}  - List tasks
PUT    /api/v1/tasks/{id}       - Update task
DELETE /api/v1/tasks/{id}       - Delete task
```

#### Memory
```
GET    /api/v1/memory/chat      - Get chat history
GET    /api/v1/memory/facts     - Get personal facts
POST   /api/v1/memory/facts     - Store personal fact
DELETE /api/v1/memory/facts    - Delete fact
```

#### Suggestions
```
GET    /api/v1/suggestions/{user_id} - Get suggestions
GET    /api/v1/analysis/{user_id}    - Full analysis
```

### Response Format

```json
{
  "success": true,
  "data": { /* response data */ },
  "message": "Human-readable message",
  "timestamp": "2026-05-07T10:30:00Z"
}
```

### Error Format

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Detailed error message"
  }
}
```

## 🚀 Deployment Architecture

### Docker Containerization

```dockerfile
# Backend Container
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Frontend Container
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci && npm run build
COPY . .
CMD ["nginx", "-g", "daemon off;"]
```

### Kubernetes Deployment

```yaml
# Backend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: soulsync-backend
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: backend
        image: soulsync-backend:latest
        env:
        - name: MONGODB_URL
          valueFrom:
            secretKeyRef:
              name: soulsync-secrets
              key: mongodb-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"

# Frontend Deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: soulsync-frontend
spec:
  replicas: 2
  template:
    spec:
      containers:
      - name: frontend
        image: soulsync-frontend:latest
        ports:
        - containerPort: 80
```

### Scaling Strategy

- **Horizontal Pod Autoscaler**: Scale based on CPU/memory usage
- **Database Sharding**: User-based sharding for MongoDB
- **Redis Cluster**: For high-availability caching
- **Load Balancer**: Nginx for traffic distribution

## 🔒 Security Considerations

### Authentication & Authorization
- JWT tokens with 7-day expiration
- bcrypt password hashing (cost factor 12)
- CORS configuration for allowed origins
- Rate limiting per user (60 requests/minute)

### Data Protection
- HTTPS/TLS for all communications
- MongoDB authentication and encryption at rest
- Redis AUTH for cache access
- Environment variables for sensitive data

### Input Validation
- Pydantic models for request validation
- Sanitization of user inputs
- SQL injection prevention (using MongoDB driver)
- XSS prevention (React escapes by default)

### API Security
- API key validation for external services
- Request signing for internal services
- Audit logging for sensitive operations
- Regular security dependency updates

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging for production
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized log aggregation (ELK stack recommended)

### Metrics
- Request rate and latency
- Error rates by endpoint
- Database query performance
- Cache hit/miss ratios
- Memory and CPU usage

### Health Checks
```python
GET /health  # Basic health check
GET /health/detailed  # Detailed system health
GET /health/db  # Database connectivity
GET /health/redis  # Redis connectivity
```

## 🔄 Future Enhancements

### Planned Architecture Improvements
1. **Event-Driven Architecture**: Message queue (RabbitMQ/Kafka) for async processing
2. **Microservices Split**: Separate services for auth, chat, tasks, etc.
3. **GraphQL API**: Alternative to REST for flexible queries
4. **WebSocket Support**: Real-time notifications and updates
5. **CDN Integration**: For static assets and media
6. **Multi-region Deployment**: For global low-latency access

### Technology Upgrades
1. **Vector Database**: Migrate from FAISS to Pinecone/Weaviate
2. **Message Queue**: Redis Streams or Apache Kafka
3. **Container Orchestration**: Advanced Kubernetes features
4. **Service Mesh**: Istio for service-to-service communication
5. **Observability**: OpenTelemetry for distributed tracing

---

**Document Version**: 1.0  
**Last Updated**: May 7, 2026  
**Maintained By**: SoulSync Development Team