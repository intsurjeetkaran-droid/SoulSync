# Contributing to SoulSync AI

Thank you for your interest in contributing to SoulSync AI! This document provides guidelines and instructions for developers who want to work on this project.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Structure](#code-structure)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Resources](#resources)

## 🚀 Getting Started

### Prerequisites

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime
- **MongoDB** - Primary database (local or Atlas)
- **Redis** - Optional caching layer
- **Git** - Version control

### Initial Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/SoulSync.git
   cd SoulSync/soulsync-ai
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   cd soulsync-frontend
   npm install
   cd ..
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and database credentials
   ```

5. **Start the development servers:**
   ```bash
   # Terminal 1 - Backend
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   
   # Terminal 2 - Frontend
   cd soulsync-frontend
   npm run dev
   ```

## 🔄 Development Workflow

### Branch Strategy

- **main** - Production-ready code
- **develop** - Integration branch for features
- **feature/*** - New features (e.g., `feature/voice-enhancement`)
- **bugfix/*** - Bug fixes (e.g., `bugfix/memory-leak`)
- **hotfix/*** - Urgent production fixes

### Creating a New Feature

1. **Create a new branch:**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** following the coding standards below.

3. **Test your changes** thoroughly.

4. **Commit with meaningful messages:**
   ```bash
   git add .
   git commit -m "feat: add new voice mode animations
   
   - Added sphere pulsing effect
   - Improved visual feedback
   - Fixed audio sync issues
   
   Closes #123"
   ```

5. **Push and create a Pull Request:**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📁 Code Structure

### Backend (`/backend`)

```
backend/
├── main.py                 # FastAPI app entry point
├── api/                    # API route handlers
│   ├── chat.py            # /chat endpoint (main conversation flow)
│   ├── voice.py           # /voice endpoints (STT/TTS)
│   ├── tasks.py           # /tasks endpoints (CRUD)
│   ├── memory.py          # /memory endpoints
│   ├── suggestion.py      # /suggestions endpoints
│   ├── processing.py      # /processing endpoints
│   ├── optimization.py    # Performance optimization endpoints
│   ├── unique_features.py # Special feature endpoints
│   └── payment.py         # Payment endpoints (disabled)
├── auth/                   # Authentication & authorization
│   └── routes.py          # /auth endpoints (signup/login)
├── core/                   # Core services
│   └── ai_service.py      # Groq API client & AI generation
├── db/                     # Database layer
│   ├── config.py          # Database configuration
│   ├── mongo/             # MongoDB connection & operations
│   │   ├── connection.py  # Motor async client
│   │   └── operations.py  # CRUD operations
│   └── redis/             # Redis caching layer
│       └── cache.py       # Cache management
├── memory/                 # Memory management
│   └── memory_manager.py  # Conversation & fact storage
├── processing/             # NLP & data processing
│   ├── extractor.py       # Memory extraction from text
│   ├── mood_predictor.py  # Emotion detection
│   ├── intent_detector.py # User intent classification
│   └── language_detector.py # Language identification
├── retrieval/              # RAG (Retrieval-Augmented Generation)
│   ├── rag_engine.py      # Main RAG pipeline
│   └── vector_store.py    # FAISS vector operations
├── suggestion/             # Smart suggestions
│   └── suggestion_engine.py # Pattern analysis & recommendations
├── tasks/                  # Task management
│   ├── task_manager.py    # Task CRUD operations
│   └── task_detector.py   # Auto-detect tasks from text
├── utils/                  # Utility functions
│   ├── cache.py           # Response caching
│   ├── voice_tts.py       # Text-to-speech (edge-tts)
│   └── voice_stt.py       # Speech-to-text (Whisper)
└── config.py              # Application configuration
```

### Frontend (`/soulsync-frontend/src`)

```
src/
├── main.jsx               # React entry point
├── App.jsx               # Main application component
├── App.css               # Global styles
├── api/                  # API service layer
│   └── soulsync.js       # API client with axios
├── components/           # Reusable UI components
│   ├── ChatInput.jsx     # Message input component
│   ├── ChatWindow.jsx    # Chat history display
│   ├── Header.jsx        # Top navigation bar
│   ├── InsightPanel.jsx  # Insights sidebar
│   ├── TaskPanel.jsx     # Tasks sidebar
│   ├── VoiceMode.jsx     # Voice interaction UI
│   ├── MessageRenderer.jsx # Message formatting
│   └── NotificationBanner.jsx # System notifications
├── context/              # React context providers
│   └── AuthContext.jsx   # Authentication state
├── hooks/                # Custom React hooks
│   └── useTaskReminder.js # Task notification hook
├── pages/                # Page components
│   ├── Landing.jsx       # Landing page
│   ├── Login.jsx         # Login page
│   └── Signup.jsx        # Registration page
└── services/             # Business logic services
    ├── notifications.js  # Notification system
    └── taskReminder.js   # Task reminder service
```

## 📝 Coding Standards

### Python (Backend)

1. **Style Guide:** Follow [PEP 8](https://pep8.org/)
2. **Type Hints:** Use type annotations for all function parameters and returns
3. **Docstrings:** Every module, class, and public function must have a docstring
4. **Logging:** Use the `logging` module, not `print()`
5. **Error Handling:** Use specific exceptions, never bare `except:`

**Example:**
```python
"""
Module: memory_manager.py
Purpose: Manages conversation storage and retrieval from MongoDB.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger("soulsync.memory")

async def save_conversation(
    user_id: str,
    user_message: str,
    ai_response: str
) -> Dict[str, str]:
    """
    Save a conversation turn to the database.
    
    Args:
        user_id: Unique user identifier
        user_message: The user's input message
        ai_response: The AI's generated response
    
    Returns:
        Dictionary containing saved message IDs
    
    Raises:
        ValueError: If user_id is empty
        ConnectionError: If database is unavailable
    """
    if not user_id:
        raise ValueError("user_id cannot be empty")
    
    try:
        # Implementation here
        logger.info(f"Saved conversation for user {user_id}")
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Failed to save conversation: {e}")
        raise
```

### JavaScript/React (Frontend)

1. **Style Guide:** Follow [Airbnb React/JSX Style Guide](https://github.com/airbnb/javascript/tree/master/react)
2. **Components:** Use functional components with hooks
3. **PropTypes:** Use PropTypes or TypeScript for type checking
4. **Comments:** Add JSDoc comments for complex logic
5. **Error Boundaries:** Wrap critical components in error boundaries

**Example:**
```javascript
/**
 * ChatInput Component
 * Handles user message input with auto-resize and send functionality.
 * 
 * @param {Function} onSend - Callback when message is sent
 * @param {boolean} isLoading - Whether the AI is processing
 * @param {string} prefill - Initial text to populate input with
 */
const ChatInput = ({ onSend, isLoading, prefill }) => {
  const [message, setMessage] = useState('');
  
  /**
   * Handle form submission
   * @param {Event} e - Form submit event
   */
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;
    
    try {
      await onSend(message);
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };
  
  // Component JSX...
};
```

## 🧪 Testing

### Running Tests

```bash
# Backend tests (using pytest)
pytest backend/tests/

# Frontend tests (using Jest)
cd soulsync-frontend
npm test
```

### Writing Tests

**Backend (Python):**
```python
# tests/test_chat.py
import pytest
from backend.api.chat import chat

@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test the main chat endpoint."""
    request = ChatRequest(
        user_id="test_user",
        message="Hello, how are you?"
    )
    response = await chat(request)
    assert response.response is not None
    assert len(response.response) > 0
```

**Frontend (JavaScript):**
```javascript
// components/ChatInput.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import ChatInput from './ChatInput';

test('sends message when submit is clicked', () => {
  const onSend = jest.fn();
  render(<ChatInput onSend={onSend} isLoading={false} />);
  
  const input = screen.getByPlaceholderText(/type a message/i);
  const button = screen.getByRole('button', { name: /send/i });
  
  fireEvent.change(input, { target: { value: 'Hello' } });
  fireEvent.click(button);
  
  expect(onSend).toHaveBeenCalledWith('Hello');
});
```

## 📤 Submitting Changes

### Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Code follows the style guide
- [ ] All new features have tests
- [ ] Existing tests pass
- [ ] Documentation is updated
- [ ] No console errors or warnings
- [ ] Changes work on both desktop and mobile
- [ ] Commit messages are clear and descriptive

### Pull Request Template

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
Describe how you tested your changes.

## Screenshots (if applicable)
Add screenshots of UI changes.

## Related Issues
Closes #123
```

## 📚 Resources

### Documentation

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [Groq API Documentation](https://console.groq.com/docs)

### Architecture Decisions

- **Why MongoDB?** Flexible schema for storing diverse conversation data
- **Why FastAPI?** High performance, async support, automatic OpenAPI docs
- **Why React?** Component-based UI, large ecosystem, excellent developer experience
- **Why Groq?** Sub-second AI responses with Llama models

### Getting Help

- **GitHub Issues:** Report bugs and request features
- **Discussions:** Ask questions and share ideas
- **Email:** Contact the maintainers for urgent matters

## 🎯 First Contribution

If you're new to the project, look for issues labeled:
- `good first issue` - Perfect for beginners
- `help wanted` - Need extra hands
- `documentation` - Improve docs and comments

Welcome to the SoulSync community! 🚀