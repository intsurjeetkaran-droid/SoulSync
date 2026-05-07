# SoulSync AI - Documentation Hub

Welcome to the central documentation hub for SoulSync AI! This directory contains comprehensive guides and references for developers, contributors, and users.

## 📚 Available Documentation

### 🚀 Getting Started

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Complete step-by-step setup instructions for local development | All developers |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | Guidelines for contributing to the project | Contributors |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System architecture and design decisions | Developers, Architects |

### 🏗️ Technical Documentation

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| API Reference | REST API documentation (auto-generated at `/docs`) | Frontend developers |
| Database Schema | MongoDB collections and data models | Backend developers |
| Deployment Guide | Production deployment instructions | DevOps, Senior developers |

### 📖 User Guides

| Document | Description | Target Audience |
|----------|-------------|-----------------|
| [README.md](../README.md) | Project overview and features | All users |
| Feature Guide | Detailed feature explanations | End users |
| Voice Mode Guide | How to use voice interaction | End users |

## 🎯 Quick Navigation

### For First-Time Contributors

1. **Start Here:** [SETUP_GUIDE.md](SETUP_GUIDE.md) - Get your development environment running
2. **Learn the Code:** [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system design
3. **Follow Standards:** [CONTRIBUTING.md](../CONTRIBUTING.md) - Learn coding standards and workflows
4. **Make Your First Change:** Pick a `good first issue` from GitHub

### For Experienced Developers

- **API Docs:** http://localhost:8000/docs (Swagger UI)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- **Code Structure:** See [Project Structure](#project-structure) below

### For System Administrators

- **Deployment:** Production deployment guide (if available)
- **Monitoring:** Logging and observability setup
- **Security:** Security considerations and best practices

## 📁 Project Structure

```
soulsync-ai/
├── docs/                           # 📚 Documentation (you are here)
│   ├── README.md                  # This file - documentation hub
│   ├── SETUP_GUIDE.md             # Local development setup
│   ├── ARCHITECTURE.md            # System architecture
│   └── DEPLOYMENT.md              # Production deployment (if available)
│
├── backend/                        # 🐍 Python FastAPI backend
│   ├── main.py                    # Application entry point
│   ├── api/                       # API route handlers
│   ├── auth/                      # Authentication system
│   ├── core/                      # Core services (AI, etc.)
│   ├── db/                        # Database layer
│   ├── memory/                    # Memory management
│   ├── processing/                # NLP processing
│   ├── retrieval/                 # RAG engine
│   ├── suggestion/                # Suggestion engine
│   ├── tasks/                     # Task management
│   └── utils/                     # Utility functions
│
├── soulsync-frontend/              # ⚛️ React frontend
│   ├── src/
│   │   ├── App.jsx               # Main application component
│   │   ├── components/            # Reusable UI components
│   │   ├── pages/                 # Page components
│   │   ├── context/               # React context providers
│   │   ├── hooks/                 # Custom React hooks
│   │   ├── services/              # Business logic
│   │   └── api/                   # API client
│   └── public/                    # Static assets
│
├── .env                           # Environment configuration
├── .env.example                   # Configuration template
├── requirements.txt               # Python dependencies
├── README.md                      # Main project README
└── CONTRIBUTING.md                # Contribution guidelines
```

## 🔍 Finding Information

### Backend Development

| Topic | Where to Find |
|-------|---------------|
| API endpoints | [ARCHITECTURE.md](ARCHITECTURE.md#api-design) or `/docs` endpoint |
| Database models | [ARCHITECTURE.md](ARCHITECTURE.md#database-schema) |
| Authentication | `backend/auth/` directory |
| AI integration | `backend/core/ai_service.py` |
| Memory system | `backend/memory/` and `backend/retrieval/` |
| Task management | `backend/tasks/` directory |

### Frontend Development

| Topic | Where to Find |
|-------|---------------|
| Component structure | `soulsync-frontend/src/components/` |
| API client | `soulsync-frontend/src/api/soulsync.js` |
| State management | `soulsync-frontend/src/context/` |
| Styling | Tailwind CSS + Framer Motion |
| Routing | React Router DOM in `App.jsx` |

### DevOps & Deployment

| Topic | Where to Find |
|-------|---------------|
| Environment setup | [SETUP_GUIDE.md](SETUP_GUIDE.md) |
| Docker setup | `docker/` directory |
| Kubernetes | `k8s/` directory |
| Configuration | `.env.example` |

## 🛠️ Development Tools

### Required Tools

- **Python 3.11+** - Backend runtime
- **Node.js 20+** - Frontend runtime
- **MongoDB 6.0+** - Database
- **Git** - Version control

### Recommended Tools

- **VS Code** - Code editor with Python and React extensions
- **Postman** or **Insomnia** - API testing
- **MongoDB Compass** - Database GUI
- **Docker** - Containerization

### Browser Requirements

- **Chrome** - Required for Voice Mode (Web Speech API)
- **Any modern browser** - For general usage

## 📞 Getting Help

### Documentation Resources

1. **This Documentation Hub** - You're here!
2. **Main README** - [README.md](../README.md)
3. **Setup Guide** - [SETUP_GUIDE.md](SETUP_GUIDE.md)
4. **Architecture Docs** - [ARCHITECTURE.md](ARCHITECTURE.md)
5. **Contributing Guide** - [CONTRIBUTING.md](../CONTRIBUTING.md)

### Community Resources

- **GitHub Issues** - [Report bugs or request features](https://github.com/intsurjeetkaran-droid/SoulSync/issues)
- **GitHub Discussions** - Ask questions and share ideas
- **Email** - Contact the maintainers

### Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| Can't start backend | Check [SETUP_GUIDE.md](SETUP_GUIDE.md#troubleshooting-common-issues) |
| MongoDB connection failed | Verify MongoDB is running and connection string is correct |
| Frontend can't connect to backend | Check `VITE_API_URL` in frontend `.env` |
| API errors | Check backend logs and Swagger docs at `/docs` |

## 📝 Documentation Maintenance

### For Contributors

When adding new features or making changes:

1. **Update relevant documentation** if the change affects:
   - API endpoints
   - Database schema
   - Configuration
   - Setup process

2. **Add inline comments** for:
   - Complex algorithms
   - Non-obvious code sections
   - Public functions and classes

3. **Update this index** if you add new documentation files

### Documentation Standards

- Use clear, concise language
- Include code examples where helpful
- Add cross-references to related docs
- Keep formatting consistent
- Update when code changes

## 🔄 Documentation Updates

This documentation is maintained by the SoulSync development team. Last updated:

- **Setup Guide:** May 7, 2026
- **Architecture Docs:** May 7, 2026
- **Contributing Guide:** May 7, 2026
- **This Index:** May 7, 2026

---

**Need help?** Check the [SETUP_GUIDE.md](SETUP_GUIDE.md) for getting started, or reach out to the team for assistance.

**Want to contribute?** Read [CONTRIBUTING.md](../CONTRIBUTING.md) to learn how to get involved!