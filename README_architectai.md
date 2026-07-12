# ArchitectAI 🤖

> Describe your app. Watch it build itself.

[![Python](https://img.shields.io/badge/python-3.11+-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green)]()
[![Next.js](https://img.shields.io/badge/Next.js-15-black)]()
[![LangGraph](https://img.shields.io/badge/LangGraph-agentic-purple)]()
[![Docker](https://img.shields.io/badge/Docker-compose-blue)]()

## What is ArchitectAI?

ArchitectAI turns plain-language product goals into tested, security-reviewed, downloadable project bundles. It uses a LangGraph pipeline with specialized sub-agents (Orchestrator, Coder, Tester, SecurityAuditor) to plan → generate → test → patch → audit → package software automatically.

## Quick Start

### Option 1: Docker (recommended)

```bash
cp .env.example .env
# Edit .env with your OPENAI_API_KEY
docker compose up --build
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Option 2: Local Development

**Prerequisites:** Python 3.11+, Node.js 18+, Redis (optional)

```bash
# 1. Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Environment Variables

Copy `.env.example` to `.env`:

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | ✅ | OpenAI API key for LLM agents |
| `DATABASE_URL` | ❌ | Database URL (defaults to SQLite) |
| `REDIS_URL` | ❌ | Redis URL for SSE streaming (graceful fallback) |
| `CORS_ORIGINS` | ❌ | Allowed CORS origins |
| `SECRET_KEY` | ❌ | Application secret key |

## Architecture

```
User → [Product Goal] → FastAPI → LangGraph Pipeline
                                     ├── Plan (Orchestrator Agent)
                                     ├── Generate (Coder Agent)
                                     ├── Test (Tester Agent) ←→ Patch Loop
                                     ├── Security (Auditor Agent) ←→ Patch Loop
                                     └── Package (Bundle Service) → ZIP Download
```

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript + Tailwind CSS 4 |
| Backend | FastAPI + Python 3.11+ (async) |
| Orchestration | LangGraph StateGraph |
| Database | PostgreSQL / SQLite |
| Queue & Events | Redis (SSE streaming) |
| Deployment | Docker Compose |

## API

Full OpenAPI docs at `/docs` when running. Key endpoints:

| Route | Method | Description |
|---|---|---|
| `/api/v1/projects` | POST | Create project |
| `/api/v1/projects` | GET | List projects |
| `/api/v1/projects/{id}/jobs` | POST | Launch generation |
| `/api/v1/jobs/{id}/events/stream` | GET | SSE event stream |
| `/api/v1/jobs/{id}/bundle` | GET | Download ZIP bundle |
| `/api/v1/stats` | GET | Platform statistics |
| `/health` | GET | Health check |

## License

MIT
