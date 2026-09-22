# AgentForge AI

## Team Members

| Name | Email | Roll Number |
| :--- | :--- | :--- |
| **Gopu Rama Krishna Reddy** | rkreddyg115@gmail.com | 23071A7226 |
| **Gajula Abhiram** | abhiramgajula9@gmail.com | 23071A6914 |

## Project Overview

A reusable, premium Agentic AI Platform for intelligent B2B prospect discovery. Dynamically discovers, validates, enriches, and scores companies matching your Ideal Customer Profile (ICP) — then generates personalized outreach recommendations for human review.

---

## 🌟 Modern UI & UX Highlights

The platform is designed with a premium, responsive dark mode theme and incorporates the following advanced visual and interaction patterns:
* **Unified Queue & Decision Tabs** — Approvals are structured under a clean, full-width single-column list with distinct **Pending**, **Approved**, and **Rejected** queues. Includes dynamic toggling between **Card View** and **Table View** configurations.
* **12-Column Responsive Card Grids** — Information is laid out using multi-column grids that separate company metrics (logo, size, qualification score, tier) from the **Primary Contact Profile Card** widget and collapsible outreach templates.
* **Dual-Row Filter Panels** — The Prospects filter bar is structured as a two-row responsive grid (campaigns, keywords, and sorts on top; score sliders, tier pills, and status checkboxes below) to prevent clumsy wrapping.
* **Instant Decision Sync** — Corrected routing path parameters ensure approval and rejection choices commit instantly and refresh local cache stores without needing browser updates.
* **Accessible Pastel Accents** — Tuned qualification scores and low metrics from generic red to soft, high-contrast rose colors (`rose-400` / `rose-500/10`) for maximum visual harmony against space-blue backgrounds.

---

## Quick Start (5 minutes)

### Prerequisites

- **Python 3.11+** — [python.org](https://python.org)
- **Node.js 18+** — [nodejs.org](https://nodejs.org)
- **Docker Desktop** — [docker.com](https://docker.com)
- **Git** — [git-scm.com](https://git-scm.com)

### One-command setup

```bash
git clone https://github.com/RamaKrishnasadisha/Agentic-AI-Platform.git
cd agentforge-ai
make setup
```

This single command:
1. Copies `backend/.env.example` → `backend/.env` (won't overwrite existing)
2. Starts **PostgreSQL 16**, **Redis 7**, and **ChromaDB** via Docker
3. Installs Python dependencies in the backend virtualenv
4. Runs database migrations (`alembic upgrade head`) + seeds demo data
5. Installs frontend npm packages

### Start developing

```bash
make dev
```

Opens the FastAPI backend at **http://localhost:8000** (interactive Swagger docs at `/docs`) and the Vite frontend dev server at **http://localhost:5173**.

### Demo login

| Email | Password | Role |
|-------|----------|------|
| `admin@agentforge.ai` | `password123` | Admin (full access) |
| `sales@agentforge.ai` | `password123` | Sales (run workflows, approve) |
| `viewer@agentforge.ai` | `password123` | Viewer (read-only) |

### Demo walkthrough

| Time | Step | What to show |
|------|------|-------------|
| 0:00 | **Login** | Sign in as `admin@agentforge.ai` / `password123` |
| 0:30 | **New Campaign** | Click "New Campaign" → complete ICP wizard → Launch |
| 1:00 | **Workflow Viewer** | Watch the dynamic node graph light up as specialist agents execute in sequence |
| 2:00 | **Dashboard** | View metrics, company status funnels, and tech stack distributions |
| 2:30 | **Prospects** | Use the dual-row filter grid to filter by score > 70, open detail view with 8-dimension scorecard |
| 3:30 | **Approvals** | Make instant outreach reviews (approve/reject) in the Pending queue |
| 4:00 | **Memory** | Search for a company, see timeline entries and ChromaDB vector embeddings |
| 4:30 | **New Preset** | Switch to the Cybersecurity preset → start new workflow |

---

## With Real APIs (recommended for production)

Set these in `backend/.env` for richer data:

| API | What it provides | Free tier | Where to get it |
|-----|-----------------|-----------|-----------------|
| **Groq** | LLM-powered scoring & recommendations | Free | [console.groq.com](https://console.groq.com) |
| **SerpApi** | Real-time company discovery & LinkedIn lookups | 100 searches/month | [serpapi.com](https://serpapi.com) |
| **Hunter.io** | Email finding & confidence verification | 100 lookups/month | [hunter.io](https://hunter.io) |
| **Anthropic** | Claude-powered agent reasoning (optional) | API credits | [anthropic.com](https://anthropic.com) |

Without API keys, **mock data is automatically used** — the platform runs fully functional with realistic demo companies.

---

## Architecture

```
                    ┌────────────────────────────┐
                    │     Planner (LangGraph)     │
                    │  Dynamically schedules      │
                    │  agents based on ICP + mem  │
                    └──────────┬─────────────────┘
                               │
            ┌───────────────────┼───────────────────┐
            ▼                   ▼                   ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
     │  Discovery   │──▶│  Validation  │──▶│  Decision Maker  │
     │  (SerpApi /  │   │  (domain +   │   │  (executive +    │
     │   mock)      │   │   fit check) │   │   persona match) │
     └──────────────┘   └──────────────┘   └────────┬─────────┘
                                                    ▼
     ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
     │  Outreach    │◀──│  Qualification│◀──│  Enrichment      │
     │  Templates   │   │  8-dim score │   │  (Hunter +       │
     │  + Memory    │   │  0-100 each  │   │   LinkedIn)      │
     └──────┬───────┘   └──────────────┘   └──────────────────┘
            ▼
     ┌──────────────┐
     │ Human Review │──▶ Memory (PostgreSQL + ChromaDB)
     │ Approvals    │      for dedup + semantic search
     └──────────────┘
```

### Key concepts

- **LLM-powered Planner** — dynamically decides which specialist agents to run based on the workflow configuration, skipping redundant work.
- **6 Specialist Agents** — Discovery → Validation (12-check pipeline) → Decision Maker → Contact Enrichment → Qualification → Outreach & Memory.
- **8-Dimension Scorecard** — industry_match, location_match, hiring_signals, tech_stack_match, funding_stage, revenue_tier, employee_range, decision_makers_found — weighted per campaign.
- **Clean Brand Extraction** — Filters search result page titles against target domain prefixes to isolate real company brand names.
- **Shared Memory** — PostgreSQL (structured data), ChromaDB (semantic vector search for deduplication), Redis (live workflow state + Celery broker).
- **Human Approval Loop** — no outreach without review; approve/reject/skip with comments.
- **Real-time WebSockets** — frontend shows each agent transitioning idle → running → completed/failed.

### Tech stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, TypeScript, Tailwind CSS, React Query, Recharts, Framer Motion, Zustand |
| **Backend** | FastAPI, LangGraph, SQLAlchemy, Pydantic, WebSockets, Celery |
| **Databases** | PostgreSQL 16 (structured), Redis 7 (cache + broker), ChromaDB (vector embeddings) |
| **AI** | Groq (default), Anthropic Claude (optional), sentence-transformers (embeddings) |

---

## Other commands

| Command | What it does |
|---------|-------------|
| `make dev-backend` | Start backend only (port 8000) |
| `make dev-frontend` | Start frontend only (port 5173) |
| `make test` | Run backend test suite (pytest) |
| `make logs` | Tail Docker logs |
| `make db-shell` | Open PostgreSQL shell |
| `make db-migrate message="desc"` | Generate an Alembic migration |
| `make db-upgrade` | Apply pending migrations |
| `make clean` | Remove Docker volumes (destroy data) |
| `make help` | Show all commands |

---

## Project structure

```
agentforge-ai/
├── backend/
│   ├── agents/          # 6 specialist agents + base class
│   ├── planner/         # LLM planner + LangGraph state
│   ├── workflow_engine/ # Engine, Celery runner, WebSocket events
│   ├── memory/          # SharedMemory, Redis state, ChromaDB client
│   ├── tools/           # Web search, company lookup, email finder, mock data
│   ├── routers/         # FastAPI routers (auth, workflows, prospects, etc.)
│   ├── schemas/         # Pydantic request/response models
│   ├── models/          # SQLAlchemy ORM models
│   ├── services/        # Business logic layer
│   ├── config/          # Settings + 3 presets
│   ├── database/        # Session, seeds, migrations
│   ├── prompts/         # LLM system prompts
│   └── tests/           # Pytest suite
├── frontend/
│   ├── src/pages/       # Pages (Dashboard, Prospects, Approvals, etc.)
│   ├── src/components/  # Reusable components
│   ├── src/hooks/       # Custom React hooks
│   ├── src/store/       # Zustand stores
│   ├── src/api/         # API client modules
│   └── src/types/       # TypeScript interfaces
├── docker-compose.yml   # PostgreSQL + Redis + ChromaDB
├── Makefile             # Dev commands
└── README.md
```

---

## Environment variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://agentforge:agentforge_secret@localhost:5432/agentforge_db` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `CHROMADB_HOST` | ChromaDB host | `localhost` |
| `CHROMADB_PORT` | ChromaDB port | `8001` |
| `JWT_SECRET` | Secret for JWT signing | (change in production) |
| `JWT_EXPIRE_MINUTES` | Token expiry | `1440` |
| `GROQ_API_KEY` | Groq API key (free) | (required for LLM features) |
| `SERPAPI_KEY` | SerpApi key (100 free/mo) | (optional — falls back to mock) |
| `HUNTER_API_KEY` | Hunter.io key (100 free/mo) | (optional — falls back to mock) |
| `USE_MOCK_DATA` | Force mock data mode | `false` |
| `MOCK_COMPANY_COUNT` | Number of mock companies | `20` |
| `FRONTEND_URL` | CORS origin | `http://localhost:5173` |

---

