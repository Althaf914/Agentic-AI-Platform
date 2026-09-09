# AgentForge AI — Complete System Documentation
## Architecture, File Topology, Endpoints, and Agentic Communication

---

## 1. Executive Summary & Core Concept

**AgentForge AI** is an enterprise-grade, agentic B2B prospect discovery platform. The system operates on a human-in-the-loop (HITL) model, automating the research lifecycle of identifying high-fit target accounts and decision makers, qualifying them against multi-dimensional scorecards, and generating tailored outbound outreach recommendations.

### Operational Philosophy
Instead of a simple static execution chain, the platform leverages a **dynamic planning graph**. A dedicated coordinator (Planner) evaluates the workspace configuration, queries the platform's vector and relational memory to exclude already-processed domains (preventing duplicate contacts and redundant API calls), and dynamically dispatches tasks to specialist agents.

```mermaid
graph TD
    A[Launch Workflow] --> B[LLM Planner]
    B --> C{Memory Checks}
    C -->|New Domains| D[Agents Pipeline Dispatch]
    C -->|Known Domains| E[Skip / Deduplicate]
    D --> F[1. Company Discovery]
    F --> G[2. Company Validation]
    G --> H[3. Decision Maker Lookup]
    H --> I[4. Contact Enrichment]
    I --> J[5. Account Qualification]
    J --> K[6. Outreach Recommendations]
    K --> L[PostgreSQL & ChromaDB Vector Store]
    L --> M[Human Review / Approvals Dashboard]
```

---

## 2. Technical Stack & Dependencies

### Backend Services (Python 3.11+)
* **Core Framework**: **FastAPI** — high-performance ASGI framework for endpoints and real-time WebSocket communication.
* **Orchestration**: **LangGraph** & **LangChain** — orchestrates agentic state loops, routing logic, and execution steps.
* **Task Queues**: **Celery** + **Redis** — processes long-running workflows asynchronously in the background.
* **ORM & Database**: **SQLAlchemy 2.0** + **Alembic** — declarative schema mappings and database migrations.
* **Vector Engine**: **ChromaDB** — local vector database storing embeddings for semantic deduplication and timeline lookups.
* **AI Embeddings**: **Sentence-Transformers** (`all-MiniLM-L6-v2`) — generates 384-dimensional vector weights.

### Frontend Application (Vite + React 18)
* **Language & Tooling**: **TypeScript**, **Vite** — rapid hot-reloading and compile-time type safety.
* **State Management**: **Zustand** — lightweight global stores synchronizing authentication and WebSocket feeds.
* **Data Fetching**: **React Query (TanStack)** — cache invalidation and query synchronization.
* **Styling & Layout**: **Tailwind CSS**, **shadcn/ui** — premium, responsive dark mode variables, cards, and grid systems.
* **Charts**: **Recharts** — renders dashboard funnels and qualification matrices.

### Databases & Cache
* **PostgreSQL 16**: Relational storage for users, workflows, companies, contacts, and approval statuses.
* **Redis 7**: Live activity caching, WebSocket pub/sub message brokers, and Celery task queues.

---

## 3. Exhaustive File-by-File Breakdown & Core Functionality

### A. Backend Workspace (`backend/`)

#### 1. Directory: `backend/config/`
* **`settings.py`**:
  * *Role*: Initializes configurations using Pydantic's `BaseSettings`.
  * *Key Symbols*: `Settings` (class).
  * *Functionality*: Loads `.env` environment variables, manages database connection strings, API tokens, and mock-data runtime flags.

#### 2. Directory: `backend/database/`
* **`session.py`**:
  * *Role*: Manages SQL engines and thread-local connection sessions.
  * *Key Symbols*: `engine`, `SessionLocal`.
  * *Functionality*: Establishes relational connections with the PostgreSQL database.
* **`init_db.py`**:
  * *Role*: Database table initializer.
  * *Key Symbols*: `init_database()`.
  * *Functionality*: Runs declarative schema setups and seeds baseline configurations.
* **`seeds.py`**:
  * *Role*: Presets and mock data seed script.
  * *Key Symbols*: `seed_presets()`, `seed_mock_leads()`.
  * *Functionality*: Populates target industry lists, ICP filters, and initial dashboard telemetry records.

#### 3. Directory: `backend/models/`
* **`base.py`**: Declares SQLAlchemy's meta Declarative Base class.
* **`user.py`**: Defines the `User` model, mapping login credentials and roles (`admin`, `sales`, `viewer`).
* **`company.py`**: Defines the `Company` model (name, domain, industry, size, scoring weights, and approval status).
* **`contact.py`**: Defines the `Contact` model (name, title, email, phone number, and persona matching details).
* **`recommendation.py`**: Defines the `Recommendation` model (outreach message template, priority tier, and suggested outreach channel).
* **`approval.py`**: Defines the `Approval` model, tracking HITL decisions (`pending`, `approved`, `rejected`, comments, and reviewer ID).
* **`workflow.py`**: Defines the `Workflow` model (run status, active agent logs, configuration parameters).
* **`configuration.py`**: Defines the `Configuration` model (presets for ICPs, personas, and score card weights).
* **`memory.py`**: Defines the `MemoryEntry` model, storing relational mapping indices for ChromaDB embeddings.

#### 4. Directory: `backend/schemas/`
* **`auth.py`**: Pydantic models for register inputs, login tokens, and active user payloads.
* **`campaign.py`**: Pydantic models mapping campaign setup parameters.
* **`configuration.py`**: Validates custom configurations for ICP criteria and scoring weights.
* **`prospect.py`**: Defines API validation filters, details scorecard matrices, and contact arrays.
* **`approval.py`**: Validates request inputs for decisions (`approved`, `rejected`, rejection reasons, schedule queues).
* **`workflow.py`**: Standardizes workflow task status tracking and logs schemas.
* **`memory.py`**: Validates semantic search requests and timeline responses.

#### 5. Directory: `backend/routers/`
* **`auth.py`**: Exposes register/login endpoints. Resolves OAuth2 tokens.
* **`campaigns.py`**: Creates, updates, and fetches active campaign configurations.
* **`dashboard.py`**: Aggregates metrics (e.g. total companies discovered, validated rates, qualified funnels).
* **`prospects.py`**: Handles pagination, keyword searches, and detailed profile scorecards.
* **`approvals.py`**: Manages the review queue, processing approvals and rejections instantly.
* **`workflows.py`**: Dispatches workflow runs, pauses tasks, and reads agent execution logs.
* **`debug.py`**: Health metrics diagnostic endpoints.

#### 6. Directory: `backend/services/`
* **`auth_service.py`**: Handles password hashing (`bcrypt`), login validation, and JWT token signatures.
* **`approval_service.py`**: Saves human review decisions, schedules outreach queues, and writes processed results to vector memory.

#### 7. Directory: `backend/agents/`
* **`base.py`**: Implements `BaseAgent`. Handles WebSocket event dispatches (`emit()`), database sessions, and starts run logs.
* **`company_discovery.py`**: Launches search queries on SerpAPI to locate domains matching campaign ICP targets.
* **`validation_agent.py`**: Coordinates the 12-check company validation pipeline.
* **`decision_maker.py`**: Queries search results to identify decision-makers matching the configured target personas.
* **`contact_enrichment.py`**: Resolves contact emails via Hunter.io.
* **`qualification.py`**: Evaluates company metrics against the 8-dimension scorecard weights.
* **`recommendation_memory.py`**: Generates custom outreach copy based on detected triggers, logs entries in the PostgreSQL memory database, and inserts vector embeddings into ChromaDB.
* **`search_strategy_agent.py`**: Translates raw ICP specifications into refined search strings.

#### 8. Directory: `backend/planner/`
* **`planner.py`**: Builds the LangGraph state graph. Coordinates agent nodes and routes executions.

#### 9. Directory: `backend/workflow_engine/`
* **`celery_app.py`**: Configures Celery workers.
* **`engine.py`**: Runs workflow tasks, executes graph nodes, and formats execution metrics.
* **`events.py`**: Standardizes WebSocket event payloads (e.g., `company_discovered`, `company_validated`).
* **`websocket_manager.py`**: Manages active connection sockets.

#### 10. Directory: `backend/memory/`
* **`shared_memory.py`**: Interacts with PostgreSQL and ChromaDB to verify duplicate accounts.
* **`vector_db.py`**: ChromaDB connection wrapper.

#### 11. Directory: `backend/tools/`
* **`email_finder.py`**: Interacts with Hunter.io's Email Finder API.
* **`web_search.py`**: SerpAPI Google search wrapper. Cleans search titles to return accurate company names.
* **`mock_data.py`**: Generates mock datasets when API keys are missing.
* **`mock_dataset.py`**: Static fallback lists.

#### 12. Main Gateway
* **`main.py`**: The FastAPI application entrypoint. Configures middleware, registers routes, and handles WebSocket events.

#### 13. Directory: `backend/tests/`
* **`conftest.py`**: Defines pytest fixtures (e.g. SQLite database, mock clients, test users, seed companies).
* **`test_agents.py`**: Unit tests for the discovery, validation, decision-maker, and qualification agents.
* **`test_memory.py`**: Tests ChromaDB vector insertions and duplicate checks.
* **`test_planner.py`**: Tests LangGraph routing logic.
* **`test_workflows.py`**: Tests end-to-end Celery workflow executions.
* **`test_approvals.py`**: Tests approvals endpoints (approving, rejecting, listing).

---

### B. Frontend Workspace (`frontend/src/`)

#### 1. Directory: `frontend/src/api/`
* **`auth.ts`**: Calls `/auth/login` and `/auth/register` endpoints.
* **`configurations.ts`**: Manages ICP templates, scoring configs, and persona setups.
* **`workflows.ts`**: Starts workflows and queries running logs.
* **`prospects.ts`**: Queries lists, filters, and detailed scorecard data.
* **`approvals.ts`**: Submits approval or rejection decisions.

#### 2. Directory: `frontend/src/store/`
* **`authStore.ts`**: Manages active JWT tokens, session logins, and user role records.
* **`workflowStore.ts`**: Collects real-time WebSocket logs and updates running workflow statuses.

#### 3. Directory: `frontend/src/hooks/`
* **`useAuth.ts`**: Wraps authentication mutations.
* **`useProspects.ts`**: Fetches lists of prospects and scorecard profiles.
* **`useWorkflow.ts`**: Handles starting workflows and listening to WebSocket feeds.
* **`useApprovals.ts`**: Fetches the reviews queue and submits approval/rejection decisions.

#### 4. Directory: `frontend/src/pages/`
* **`Dashboard.tsx`**: Renders analytical charts, metrics, and live feeds.
* **`ICPBuilder.tsx`**: A wizard to configure ICP target segments.
* **`Personas.tsx`**: Displays target buying-committee configurations.
* **`WorkflowLauncher.tsx`**: Launcher page with preset config parameters and sequential pipeline maps.
* **`WorkflowViewer.tsx`**: Displays a live, horizontal flow graph with active node indicators.
* **`Prospects.tsx`**: Displays prospects, dual-row filters, and details.
* **`ProspectDetail.tsx`**: Displays 8-dimension scorecards and outreach templates.
* **`Approvals.tsx`**: Human review queue with Pending, Approved, and Rejected cards.
* **`Memory.tsx`**: Interface for vector-based semantic searches.
* **`Settings.tsx`**: Profile settings.
* **`Login.tsx`**: Renders the login form.

#### 5. Directory: `frontend/src/components/`
* **`layout/Sidebar.tsx`**: Main sidebar navigation.
* **`layout/TopBar.tsx`**: Top header displaying active presets, profiles, and theme toggles.
* **`layout/Layout.tsx`**: Root wrapper injecting top and side navigation blocks.
* **`dashboard/ActivityFeed.tsx`**: Renders live running logs.
* **`dashboard/FunnelChart.tsx`**: Funnel metrics charts.

#### 6. Directory: `frontend/src/types/`
* **`auth.ts`**: TypeScript definitions for users and roles.
* **`config.ts`**: Types for configurations.
* **`workflow.ts`**: Types for workflows and logs.
* **`prospect.ts`**: Types for companies and scorecards.
* **`approval.ts`**: Types for approvals.
* **`memory.ts`**: Types for vectors and search entries.

---

## 4. API Endpoints Reference Handbook

All endpoints are prefixed with `/api/v1` and require Bearer JWT authorization tokens.

### A. Authentication `/auth`
* `POST /auth/register`: Registers a new user.
* `POST /auth/login`: Authenticates credentials (username, password) and returns a JWT access token.

### B. Configurations `/configurations`
* `GET /configurations`: Lists all active presets.
* `POST /configurations`: Saves new campaign presets (ICP, Persona, or Scoring weights).

### C. Prospects `/prospects`
* `GET /prospects`: Returns filtered prospect lists.
* `GET /prospects/{id}`: Returns detailed profile dashboards (including 8-dimension scorecards and recommendation details).

### D. Approvals `/approvals`
* `GET /approvals`: Returns pending, approved, or rejected items.
* `POST /approvals/{approval_id}`: Records an outreach decision. Updates database records instantly.
  ```json
  // Request Payload (Approve)
  {
    "status": "approved",
    "comment": "Proceed with LinkedIn outreach",
    "channel": "linkedin",
    "scheduled_at": "2026-06-30T09:00:00Z"
  }
  ```

### E. Workflows `/workflows`
* `POST /workflows/launch`: Launches a background workflow.
* `GET /workflows/{id}`: Fetches active agent logs.

---

## 5. Detailed Data Flow & Agentic Communication

When a workflow runs, the backend database state updates in real-time, which is synchronized with the React frontend via WebSockets.

```
Relational Tables (PostgreSQL)  <---- [Celery Worker] ---->  Vector Weights (ChromaDB)
           |                                                      ^
           | (SQLAlchemy updates)                                  | (Embeddings)
           v                                                      |
    [FastAPI Router] ---- (Socket Emits) ----> [React (Zustand Store)]
```

### Agent Communication Diagram (LangGraph Routing)
```mermaid
stateDiagram-v2
    [*] --> SearchStrategy : Workflow Launch
    SearchStrategy --> CompanyDiscovery : Refined Search Queries
    CompanyDiscovery --> CompanyValidation : Found Company List
    
    state CompanyValidation {
        [*] --> Reachability
        Reachability --> HTTPSEnforced
        HTTPSEnforced --> BlacklistCheck
        BlacklistCheck --> ParallelChecks
    }
    
    CompanyValidation --> DecisionMaker : Validated Accounts
    DecisionMaker --> ContactEnrichment : Target Executives Matching Personas
    ContactEnrichment --> AccountQualification : Verified Outbound Details
    AccountQualification --> OutreachRecommendations : Qualification Scores
    OutreachRecommendations --> MemorySync : Outreach Recommendations
    MemorySync --> [*] : human_review Queue
```

---

## 6. Setup Configuration Variables

Define these variables in your `backend/.env` file:

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (`postgresql://user:pass@localhost:5432/db`). |
| `REDIS_URL` | Redis connection string (`redis://localhost:6379/0`). |
| `CHROMADB_HOST` | ChromaDB vector engine host. |
| `GROQ_API_KEY` | Groq API Key (required for LLM features). |
| `SERPAPI_KEY` | SerpApi Key (optional - falls back to mock). |
| `HUNTER_API_KEY` | Hunter.io API Key (optional - falls back to mock). |
| `USE_MOCK_DATA` | Force mock mode (`true`/`false`). |
