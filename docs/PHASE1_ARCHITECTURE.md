# ArchitectAI — Phase 1 Architecture

## Executive Summary

ArchitectAI is a self-evolving AI SaaS platform that converts a high-level **Product Goal** into a runnable, production-oriented application scaffold with generated frontend, backend, infrastructure, test suites, and security findings. The Phase 1 design favors **deterministic orchestration with bounded autonomy** over unconstrained agent swarms.

The core runtime is a **LangGraph StateGraph** orchestrator supervising four specialized agents:

1. **Orchestrator Agent** — decomposes the Product Goal, creates the implementation plan, manages state, and controls execution.
2. **Coder Agent** — generates and patches code artifacts in a monorepo.
3. **Tester/QA Agent** — generates tests, executes them, and emits structured bug reports.
4. **Security Auditor Agent** — scans generated code and infrastructure for OWASP-style risks and insecure defaults.

The platform exposes a **Next.js dashboard** where a user submits a Product Goal and watches live progress over **Server-Sent Events (SSE)**. A **FastAPI backend** manages jobs, persistence, agent execution, file artifacts, ZIP export, and streaming. **PostgreSQL + pgvector** stores jobs, project artifacts, execution logs, embeddings, test results, and security findings. **Redis** is used as the transient queue/event bus for agent work dispatch and fan-out.

The architecture is designed to support:

- long-running stateful workflows
- resumability and replay
- iterative coder↔tester repair loops
- retrieval over generated code/history via pgvector
- security gating before packaging/download
- future expansion to more agents, models, and deployment targets

---

## Research Notes and Current-State Context

### What the ecosystem indicates

Based on direct source review and domain knowledge:

- **LangGraph** is currently one of the strongest choices for long-running, stateful agent orchestration because it emphasizes durable execution, state transitions, interrupts, streaming, and human-in-the-loop control rather than hiding orchestration complexity behind a high-level abstraction.
- **OpenHands** validates the product direction: a practical software agent platform with SDK, CLI, GUI, API, and deployment modes.
- **SWE-agent / mini-SWE-agent** validate the code-fix loop pattern: language-model-driven issue resolution works best when constrained by tool access, repo context, execution traces, and tight iteration loops.

### Key source URLs fetched for grounding

1. `https://docs.langchain.com/oss/python/langgraph/overview`
   - Confirms LangGraph’s focus on durable execution, human-in-the-loop, statefulness, streaming, and production deployment.
2. `https://docs.all-hands.dev/`
   - Confirms practical market direction toward AI software agents exposed through SDK, CLI, GUI, API, and enterprise deployment.
3. `https://github.com/SWE-agent/SWE-agent`
   - Confirms autonomous issue-fixing architecture, repo/tool-based workflows, and benchmark-driven coding-agent design.

### Constraint encountered

The requested `ddg-search` queries were attempted but DuckDuckGo anti-bot blocking prevented retrieval. Phase 1 architecture therefore combines direct source fetches with expert synthesis from current AI-SWE patterns.

---

## System Goals

### Primary goals

- Accept a natural-language Product Goal.
- Generate a coherent full-stack application blueprint and code scaffold.
- Produce frontend, backend, infra, tests, and security review automatically.
- Detect failures and iterate automatically through bounded repair loops.
- Surface transparent progress and artifacts to the user.

### Non-goals for Phase 1

- Full autonomous production deployment to cloud providers.
- Infinite self-modification of the agent runtime.
- Multi-tenant untrusted code execution at internet scale.
- Formal verification or complete vulnerability elimination.

---

## High-Level Architecture

```text
+--------------------+        SSE/REST        +-------------------------+
|  Next.js Dashboard | <--------------------> |      FastAPI API        |
| - Product Goal UI  |                        | - Job orchestration API |
| - Live progress    |                        | - Artifact API          |
| - File viewer      |                        | - ZIP export            |
| - Results panels   |                        | - SSE event stream      |
+---------+----------+                        +------------+------------+
          |                                                |
          |                                                |
          |                                    invokes / persists / streams
          |                                                |
          v                                                v
                                  +----------------------------------------+
                                  |      LangGraph Orchestrator Runtime     |
                                  |----------------------------------------|
                                  | StateGraph                             |
                                  | - intake                               |
                                  | - planning                             |
                                  | - codegen                              |
                                  | - test                                 |
                                  | - security                             |
                                  | - repair loop                          |
                                  | - package                              |
                                  +-----+---------------+------------------+
                                        |               |
                              task/event |               | retrieval/history
                                        v               v
                               +----------------+   +----------------------+
                               |     Redis      |   | PostgreSQL + pgvector|
                               | queue/eventbus |   | jobs/artifacts/logs  |
                               +----------------+   | embeddings/findings  |
                                                    +----------+-----------+
                                                               |
                                                               |
                                                               v
                                                     +---------------------+
                                                     | Monorepo Workspace   |
                                                     | frontend/backend/etc |
                                                     | tests/docker/nginx   |
                                                     +---------------------+
```

---

## Component Breakdown

### 1) Frontend Dashboard (Next.js)

**Responsibilities**
- Accept Product Goal submission.
- Show job lifecycle and live event stream.
- Render plan, generated file tree, code previews, test status, logs, and security findings.
- Allow ZIP download of generated project.
- Support human approvals in future phases.

**Key views**
- New Project form
- Job progress timeline
- Artifact explorer
- Test results page
- Security findings page
- Download/export panel

**Why Next.js**
- Strong developer ecosystem.
- Easy SSR/CSR hybrid for dashboards.
- Excellent routing and React-based component ecosystem.
- Good fit with streaming UI and authenticated SaaS patterns.

### 2) FastAPI Backend

**Responsibilities**
- REST API for job creation, inspection, artifacts, and export.
- SSE endpoint for real-time event streaming.
- Agent runtime invocation and job lifecycle coordination.
- Persistence of state snapshots, logs, test outputs, and findings.
- Packaging generated project into ZIP.

**Why FastAPI over Django**
- Lower ceremony and faster iteration for agent platforms.
- First-class async support for long-running IO-heavy workflows.
- Strong Pydantic model validation for agent message contracts.
- Easier SSE and lightweight service composition.
- Better fit for API-first orchestration than full-stack MVC.

### 3) LangGraph Orchestrator Agent

**Responsibilities**
- Convert Product Goal into architecture plan and task graph.
- Maintain global job state.
- Route work to specialized agents.
- Enforce loop bounds, retries, stop conditions, and policy gates.
- Decide whether bug reports go back to Coder or fail the job.
- Trigger packaging only after quality gates pass.

**Why LangGraph over AutoGen / ad-hoc agent loops**
- Explicit state graph makes workflows auditable.
- Durable execution and resumability are core features.
- Better control of conditional transitions and bounded loops.
- Easier productionization than prompt-only conversational swarms.
- Cleaner support for interrupts, replay, checkpoints, and human approval.

### 4) Coder Agent

**Responsibilities**
- Generate monorepo files from task specs.
- Apply patches based on structured bug reports.
- Produce manifests describing generated files and assumptions.
- Consult retrieval context from prior artifacts/embeddings.

**Internal sub-capabilities**
- scaffold generation
- file-level code synthesis
- patch generation
- migration generation
- dependency updates
- changelog emission

### 5) Tester / QA Agent

**Responsibilities**
- Generate Playwright tests for UI workflows.
- Generate Pytest unit and integration tests for backend.
- Run tests in isolated containers.
- Capture tracebacks, console logs, screenshots, traces, and structured failure metadata.
- Emit bug reports normalized for the Coder Agent.

**Test outputs**
- pass/fail counts
- failing test IDs
- stack traces
- browser console logs
- screenshots
- Playwright traces
- coverage summary (optional in Phase 1.1)

### 6) Security Auditor Agent

**Responsibilities**
- Analyze generated code and configs against OWASP Top 10 patterns.
- Run static analyzers: `bandit`, `eslint-plugin-security` / `eslint-security`, dependency audits, secret scanning.
- Detect insecure defaults in Docker, Nginx, CORS, auth, and DB config.
- Produce structured findings with severity, CWE/OWASP mapping, evidence, and suggested remediation.

### 7) PostgreSQL + pgvector

**Responsibilities**
- Persist job metadata and execution state.
- Store artifact manifests and content metadata.
- Store vector embeddings for generated code chunks, plans, bug reports, and prior fixes.
- Enable retrieval to improve patching and consistency.

**Why pgvector over Pinecone**
- Co-locates operational and semantic data in one system.
- Lower operational complexity and cost for Phase 1.
- Simpler transactional consistency with artifacts and job state.
- Avoids external dependency for early-stage platform.
- Adequate performance for project-scale retrieval.

### 8) Redis Queue/Event Bus

**Responsibilities**
- Short-lived queue for agent tasks.
- Pub/sub for progress events and worker updates.
- Rate control and dispatch fan-out.

**Why Redis**
- Lightweight, fast, familiar.
- Ideal for transient work dispatch and event fan-out.
- Complements PostgreSQL rather than replacing it.

### 9) Monorepo Workspace Generator

**Responsibilities**
- Create standardized folder structure.
- Maintain generated file tree and manifests.
- Support consistent packaging and test execution.

**Proposed monorepo structure**

```text
/project-root
  /frontend                # Next.js app
  /backend                 # FastAPI service
  /tests
    /e2e                   # Playwright
    /backend               # Pytest
  /infra
    docker-compose.yml
    /nginx
      nginx.conf
    /scripts
  /docs
  /.architectai
    plan.json
    manifests/
    run_logs/
    checkpoints/
```

---

## Inter-Agent Communication Protocol

All agents communicate through a canonical message envelope persisted in PostgreSQL and optionally mirrored through Redis.

### Message Envelope

```json
{
  "message_id": "uuid",
  "job_id": "uuid",
  "trace_id": "uuid",
  "parent_message_id": "uuid|null",
  "sender": "orchestrator|coder|tester|security|system",
  "recipient": "orchestrator|coder|tester|security|broadcast",
  "message_type": "TASK_SPEC|PLAN|CODE_PATCH|TEST_REPORT|SECURITY_REPORT|STATE_UPDATE|ERROR|APPROVAL_REQUEST",
  "status": "queued|in_progress|completed|failed",
  "priority": "low|normal|high|critical",
  "timestamp": "ISO-8601",
  "payload": {},
  "artifacts": [
    {
      "artifact_id": "uuid",
      "path": "frontend/app/page.tsx",
      "kind": "source_code|test|log|trace|report|config"
    }
  ],
  "meta": {
    "attempt": 1,
    "loop_iteration": 0,
    "model": "gpt-5.x|claude-opus|etc",
    "token_budget": 120000
  }
}
```

### Core Payload Types

#### TASK_SPEC
```json
{
  "task_id": "uuid",
  "title": "Generate backend auth module",
  "objective": "Implement JWT auth with refresh tokens",
  "acceptance_criteria": [
    "login endpoint exists",
    "JWT validation middleware exists",
    "tests pass"
  ],
  "constraints": [
    "FastAPI",
    "PostgreSQL",
    "no plaintext secrets"
  ],
  "input_artifacts": ["plan.json"],
  "output_targets": ["backend/app/api/auth.py"]
}
```

#### TEST_REPORT
```json
{
  "suite": "playwright|pytest",
  "summary": {
    "passed": 18,
    "failed": 2,
    "skipped": 1
  },
  "failures": [
    {
      "bug_id": "uuid",
      "title": "Signup form returns 500",
      "severity": "high",
      "repro_steps": ["open /signup", "submit valid form"],
      "expected": "user created and redirected",
      "actual": "500 Internal Server Error",
      "evidence": {
        "traceback": "...",
        "console_logs": ["..."],
        "screenshot_path": "tests/artifacts/signup-fail.png"
      },
      "suspected_files": ["backend/app/api/users.py"]
    }
  ]
}
```

#### SECURITY_REPORT
```json
{
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 3,
    "low": 4
  },
  "findings": [
    {
      "finding_id": "uuid",
      "title": "Potential SQL injection in search endpoint",
      "severity": "high",
      "owasp": "A03:2021-Injection",
      "cwe": "CWE-89",
      "file": "backend/app/api/search.py",
      "line": 41,
      "evidence": "string interpolation in raw SQL",
      "recommendation": "Use parameterized queries via SQLAlchemy"
    }
  ]
}
```

### Protocol Principles

- Orchestrator is the **single source of truth** for workflow state.
- Agents never mutate global state directly; they emit messages and artifacts.
- Every repair loop iteration increments `loop_iteration`.
- Tester and Security findings are normalized into machine-actionable structures.
- All reports are replayable and attributable via `trace_id`.

---

## LangGraph State Machine

### State Model

```python
class ArchitectAIState(TypedDict):
    job_id: str
    product_goal: str
    requirements: dict
    architecture_plan: dict
    task_backlog: list
    active_task: dict | None
    generated_artifacts: list
    test_reports: list
    security_reports: list
    bug_backlog: list
    repair_iteration: int
    max_repair_iterations: int
    quality_gate_passed: bool
    security_gate_passed: bool
    packaging_ready: bool
    final_bundle_path: str | None
    status: str
    event_log: list
    errors: list
```

### States and Transitions

1. **INTAKE**
   - Input validation
   - Normalize Product Goal
   - Create job record
   - Transition → `PLAN`

2. **PLAN**
   - Produce system blueprint, backlog, acceptance criteria, architecture decisions
   - Store plan and initial artifacts
   - Transition → `GENERATE`

3. **GENERATE**
   - Dispatch task specs to Coder Agent
   - Write code artifacts/manifests
   - Transition → `TEST`

4. **TEST**
   - Generate and run Pytest + Playwright suites
   - If failures exist → `EVALUATE_REPAIR`
   - Else → `SECURITY_SCAN`

5. **EVALUATE_REPAIR**
   - If `repair_iteration < max_repair_iterations` and failures are patchable → `PATCH`
   - Else → `FAILED_REVIEW`

6. **PATCH**
   - Send structured bug reports to Coder Agent
   - Apply patch set
   - Increment repair counter
   - Transition → `RETEST`

7. **RETEST**
   - Re-run relevant tests first, then full regression if needed
   - If failures remain → `EVALUATE_REPAIR`
   - Else → `SECURITY_SCAN`

8. **SECURITY_SCAN**
   - Run static analysis and config scanning
   - If blocking findings exist → `SECURITY_PATCH`
   - Else → `PACKAGE`

9. **SECURITY_PATCH**
   - Route findings to Coder Agent with remediation instructions
   - Transition → `RETEST_SECURITY`

10. **RETEST_SECURITY**
    - Re-run affected tests + security scans
    - If blocking findings remain and repair limit exceeded → `FAILED_REVIEW`
    - Else if clear → `PACKAGE`

11. **PACKAGE**
    - Generate ZIP bundle, manifests, summary report
    - Transition → `COMPLETE`

12. **FAILED_REVIEW**
    - Persist incomplete result with failure reasons and partial artifacts
    - Transition → `COMPLETE_WITH_WARNINGS`

13. **COMPLETE / COMPLETE_WITH_WARNINGS**
    - Final state

### Transition Diagram

```text
INTAKE
  -> PLAN
  -> GENERATE
  -> TEST
       -> if pass -> SECURITY_SCAN
       -> if fail -> EVALUATE_REPAIR
EVALUATE_REPAIR
  -> if patchable and under limit -> PATCH -> RETEST -> EVALUATE_REPAIR/SECURITY_SCAN
  -> else -> FAILED_REVIEW
SECURITY_SCAN
  -> if blocking findings -> SECURITY_PATCH -> RETEST_SECURITY -> SECURITY_SCAN/PACKAGE
  -> else -> PACKAGE
PACKAGE -> COMPLETE
FAILED_REVIEW -> COMPLETE_WITH_WARNINGS
```

### Recommended loop guardrails

- `max_repair_iterations = 3` in Phase 1
- stop patching same file after repeated oscillation without net improvement
- require bug deduplication before each patch iteration
- permit targeted retest before full regression to reduce cost

---

## Technology Stack Decisions and Justifications

### Orchestration: LangGraph

**Chosen:** LangGraph  
**Rejected alternatives:** AutoGen, CrewAI, pure Celery pipelines, ad-hoc async loops

**Why**
- Explicit state machine semantics.
- Durable checkpoints and resumability.
- Better for bounded workflows than free-form multi-agent chat.
- Cleaner integration with interrupt/review patterns.
- Easier observability of state transitions.

### Backend API: FastAPI

**Chosen:** FastAPI  
**Rejected alternatives:** Django, Flask

**Why**
- Pydantic-native request/response contracts.
- Async-first design matches long-running orchestration.
- Strong developer ergonomics for API-heavy systems.
- Lightweight enough for microservice evolution later.

### Frontend: Next.js

**Chosen:** Next.js + TypeScript  
**Rejected alternatives:** Remix, plain React SPA

**Why**
- Mature dashboard development ecosystem.
- Easy auth, routing, server components, API integration.
- Strong fit for artifact viewers and live progress dashboards.

### Database: PostgreSQL + pgvector

**Chosen:** PostgreSQL 16 + pgvector  
**Rejected alternatives:** Pinecone, Weaviate-only, SQLite-only

**Why**
- Single datastore for relational + vector needs.
- Easier consistency between artifacts and embeddings.
- Lower cost and fewer moving parts.
- Sufficient for generated-project retrieval workloads.

### Queue/Event Bus: Redis

**Chosen:** Redis  
**Rejected alternatives:** RabbitMQ, Kafka

**Why**
- Simple operationally.
- Fast pub/sub and task queue semantics.
- Good enough for Phase 1 scale.

### Frontend Testing: Playwright

**Chosen:** Playwright  
**Rejected alternatives:** Cypress, Selenium

**Why**
- Excellent reliability for modern apps.
- Rich trace, screenshot, video, and console capture.
- Better cross-browser automation and debugging artifacts.

### Backend Testing: Pytest

**Chosen:** Pytest  
**Rejected alternatives:** unittest, nose

**Why**
- Strong plugin ecosystem.
- Expressive fixtures and parametrization.
- Best-in-class Python testing ergonomics.

### Security Scanning

**Chosen:** bandit, pip-audit, eslint security plugin, npm audit, secret scanning  
**Why**
- Covers common Python/JS risks cheaply and locally.
- Good baseline for OWASP-oriented checks.
- Easy automation inside CI-style workflow.

### Reverse Proxy: Nginx

**Chosen:** Nginx  
**Why**
- Stable reverse proxy for frontend/backend routing.
- Easy gzip, rate-limits, TLS termination patterns.
- Familiar for Docker Compose local deployment.

### Containerization: Docker Compose

**Chosen:** Docker Compose  
**Rejected alternatives:** Kubernetes initially

**Why**
- Fastest path to reproducible local and small-team deployment.
- Good enough for Phase 1 single-node architecture.
- Clear future migration path to Kubernetes if product scales.

---

## Detailed Data Flow

```text
[1] User submits Product Goal
    -> POST /api/v1/projects

[2] FastAPI creates job record
    -> persists initial state in PostgreSQL
    -> publishes job_started event
    -> invokes LangGraph orchestrator

[3] Orchestrator PLAN state
    -> builds requirements + backlog + architecture plan
    -> stores plan artifact and embeddings
    -> streams planning events over SSE

[4] Orchestrator GENERATE state
    -> sends TASK_SPEC messages to Coder Agent
    -> Coder writes monorepo files
    -> artifact metadata stored in PostgreSQL
    -> code chunks embedded into pgvector

[5] Orchestrator TEST state
    -> Tester generates Playwright/Pytest suites
    -> tests execute in isolated environment
    -> logs/screenshots/traces persisted

[6a] If tests fail
    -> Tester emits TEST_REPORT
    -> Orchestrator normalizes bug backlog
    -> Coder receives patch tasks
    -> patch artifacts persisted
    -> relevant tests re-run

[6b] If tests pass
    -> Security Auditor runs scans
    -> findings persisted and streamed

[7a] If blocking security issues exist
    -> findings routed to Coder Agent
    -> remediation patch generated
    -> affected tests + scans re-run

[7b] If security gate passes
    -> project packaged as ZIP
    -> summary report generated

[8] Dashboard consumes SSE stream
    -> renders progress timeline, artifacts, test results, security findings
    -> user downloads ZIP bundle
```

---

## Database Schema

### 1) `projects`

```sql
CREATE TABLE projects (
  id UUID PRIMARY KEY,
  name TEXT NOT NULL,
  product_goal TEXT NOT NULL,
  status TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  owner_id UUID NULL,
  current_job_id UUID NULL,
  metadata JSONB NOT NULL DEFAULT '{}'
);
```

### 2) `jobs`

```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  status TEXT NOT NULL,
  current_state TEXT NOT NULL,
  repair_iteration INT NOT NULL DEFAULT 0,
  max_repair_iterations INT NOT NULL DEFAULT 3,
  quality_gate_passed BOOLEAN NOT NULL DEFAULT FALSE,
  security_gate_passed BOOLEAN NOT NULL DEFAULT FALSE,
  final_bundle_path TEXT NULL,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL,
  error_summary TEXT NULL,
  state_snapshot JSONB NOT NULL DEFAULT '{}'
);
```

### 3) `artifacts`

```sql
CREATE TABLE artifacts (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  path TEXT NOT NULL,
  kind TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  size_bytes BIGINT NOT NULL,
  storage_uri TEXT NOT NULL,
  created_by_agent TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'
);
CREATE UNIQUE INDEX idx_artifacts_job_path_version ON artifacts(job_id, path, version);
```

### 4) `agent_messages`

```sql
CREATE TABLE agent_messages (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  trace_id UUID NOT NULL,
  parent_message_id UUID NULL,
  sender TEXT NOT NULL,
  recipient TEXT NOT NULL,
  message_type TEXT NOT NULL,
  status TEXT NOT NULL,
  priority TEXT NOT NULL DEFAULT 'normal',
  payload JSONB NOT NULL,
  meta JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_agent_messages_job_id ON agent_messages(job_id);
CREATE INDEX idx_agent_messages_trace_id ON agent_messages(trace_id);
```

### 5) `test_runs`

```sql
CREATE TABLE test_runs (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  suite_type TEXT NOT NULL,
  status TEXT NOT NULL,
  passed INT NOT NULL DEFAULT 0,
  failed INT NOT NULL DEFAULT 0,
  skipped INT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL,
  logs_uri TEXT NULL,
  trace_uri TEXT NULL,
  summary JSONB NOT NULL DEFAULT '{}'
);
```

### 6) `bug_reports`

```sql
CREATE TABLE bug_reports (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  test_run_id UUID NULL REFERENCES test_runs(id) ON DELETE SET NULL,
  title TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  repro_steps JSONB NOT NULL DEFAULT '[]',
  expected_behavior TEXT NULL,
  actual_behavior TEXT NULL,
  traceback TEXT NULL,
  console_logs JSONB NOT NULL DEFAULT '[]',
  suspected_files JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL,
  metadata JSONB NOT NULL DEFAULT '{}'
);
```

### 7) `security_findings`

```sql
CREATE TABLE security_findings (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  tool_name TEXT NOT NULL,
  severity TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  owasp_category TEXT NULL,
  cwe_id TEXT NULL,
  file_path TEXT NULL,
  line_number INT NULL,
  recommendation TEXT NULL,
  status TEXT NOT NULL DEFAULT 'open',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  metadata JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX idx_security_findings_job_id ON security_findings(job_id);
CREATE INDEX idx_security_findings_severity ON security_findings(severity);
```

### 8) `embeddings`

```sql
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE embeddings (
  id UUID PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  artifact_id UUID NULL REFERENCES artifacts(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  source_ref TEXT NOT NULL,
  chunk_index INT NOT NULL,
  content TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_embeddings_job_id ON embeddings(job_id);
```

### 9) `event_stream`

```sql
CREATE TABLE event_stream (
  id BIGSERIAL PRIMARY KEY,
  job_id UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_event_stream_job_id_id ON event_stream(job_id, id);
```

### Vector retrieval use cases

- retrieve similar prior code chunks before patching
- retrieve prior bug reports for recurring failure classes
- retrieve architecture plan sections while generating files
- retrieve security remediation examples for vulnerable patterns

---

## API Contract

Base path: `/api/v1`

### 1) Create Project / Start Generation

**POST** `/projects`

Request:
```json
{
  "name": "AI CRM",
  "product_goal": "Build a SaaS CRM for small sales teams with auth, contacts, deal tracking, and analytics dashboard."
}
```

Response:
```json
{
  "project_id": "uuid",
  "job_id": "uuid",
  "status": "queued"
}
```

### 2) List Projects

**GET** `/projects`

Response:
```json
{
  "items": [
    {
      "project_id": "uuid",
      "name": "AI CRM",
      "status": "in_progress",
      "created_at": "2026-04-05T01:00:00Z"
    }
  ]
}
```

### 3) Get Project Summary

**GET** `/projects/{project_id}`

Response:
```json
{
  "project_id": "uuid",
  "name": "AI CRM",
  "product_goal": "...",
  "status": "in_progress",
  "current_job_id": "uuid",
  "latest_summary": {
    "current_state": "TEST",
    "repair_iteration": 1
  }
}
```

### 4) Get Job Details

**GET** `/jobs/{job_id}`

Response:
```json
{
  "job_id": "uuid",
  "status": "in_progress",
  "current_state": "GENERATE",
  "repair_iteration": 0,
  "quality_gate_passed": false,
  "security_gate_passed": false,
  "plan": {},
  "metrics": {
    "artifacts": 84,
    "test_runs": 1,
    "security_findings": 0
  }
}
```

### 5) SSE Progress Stream

**GET** `/jobs/{job_id}/events/stream`

Response: `text/event-stream`

Event example:
```text
event: state_update
data: {"job_id":"uuid","state":"TEST","timestamp":"..."}

event: artifact_created
data: {"path":"frontend/app/page.tsx","kind":"source_code"}

event: test_failed
data: {"failed":2,"bug_ids":["uuid1","uuid2"]}
```

### 6) Get Job Event History

**GET** `/jobs/{job_id}/events`

Query params:
- `after_id` optional
- `limit` default 100

Response:
```json
{
  "items": [
    {
      "id": 101,
      "event_type": "state_update",
      "payload": {"state": "PLAN"},
      "created_at": "..."
    }
  ]
}
```

### 7) List Artifacts

**GET** `/jobs/{job_id}/artifacts`

Response:
```json
{
  "items": [
    {
      "artifact_id": "uuid",
      "path": "backend/app/main.py",
      "kind": "source_code",
      "version": 1,
      "size_bytes": 2411
    }
  ]
}
```

### 8) Get Artifact Content

**GET** `/artifacts/{artifact_id}`

Response:
```json
{
  "artifact_id": "uuid",
  "path": "backend/app/main.py",
  "kind": "source_code",
  "content": "from fastapi import FastAPI ...",
  "metadata": {}
}
```

### 9) Get Test Results

**GET** `/jobs/{job_id}/tests`

Response:
```json
{
  "summary": {
    "total_runs": 2,
    "latest_status": "failed"
  },
  "runs": [
    {
      "test_run_id": "uuid",
      "suite_type": "pytest",
      "passed": 24,
      "failed": 2,
      "trace_uri": "/storage/traces/run1.zip"
    }
  ]
}
```

### 10) Get Bug Reports

**GET** `/jobs/{job_id}/bugs`

Response:
```json
{
  "items": [
    {
      "bug_id": "uuid",
      "title": "Signup form returns 500",
      "severity": "high",
      "status": "open",
      "suspected_files": ["backend/app/api/users.py"]
    }
  ]
}
```

### 11) Get Security Findings

**GET** `/jobs/{job_id}/security`

Response:
```json
{
  "summary": {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 4
  },
  "items": [
    {
      "finding_id": "uuid",
      "severity": "high",
      "owasp_category": "A03:2021-Injection",
      "file_path": "backend/app/api/search.py",
      "recommendation": "Use parameterized queries"
    }
  ]
}
```

### 12) Download ZIP Bundle

**GET** `/jobs/{job_id}/bundle`

Response:
- `application/zip`
- 404 until packaging is complete

### 13) Retry Job from Failed State

**POST** `/jobs/{job_id}/retry`

Request:
```json
{
  "from_state": "PATCH"
}
```

Response:
```json
{
  "job_id": "uuid",
  "status": "queued",
  "resume_from": "PATCH"
}
```

### 14) Approve / Override Finding (Phase 1.1+)

**POST** `/jobs/{job_id}/approvals`

Request:
```json
{
  "type": "security_exception",
  "target_id": "finding_uuid",
  "reason": "accepted for prototype"
}
```

Response:
```json
{
  "status": "recorded"
}
```

---

## Security Considerations

### Platform security

- sandbox agent execution in containers with restricted filesystem scope
- isolate generated project execution from control plane
- never expose Docker socket directly to agents
- use least-privilege service accounts
- segregate control-plane DB from generated app DB if moving beyond local mode
- sign ZIP bundles and include manifest hashes
- add rate limits and auth to all APIs
- store secrets via environment injection, not prompts or source files
- maintain audit logs for every agent action and artifact version

### Generated-code security checks

- OWASP Top 10 pattern analysis
- dependency vulnerability scanning (`pip-audit`, `npm audit`)
- static code checks (`bandit`, JS security lint rules)
- secret scanning for accidental credential leakage
- CORS, cookie, auth, and session configuration review
- ORM parameterization checks for injection risks
- SSRF/file-upload/path-traversal heuristics
- unsafe deserialization and command execution detection

### Agent safety controls

- bounded repair loops to prevent endless self-modification
- restricted tool allowlist per agent role
- schema-validated messages only
- reject direct shell access except through orchestrated worker environment
- store patch diffs and rationale for replayability
- add human review mode for high-severity security findings

### SaaS multitenancy considerations for later phases

- tenant-scoped object storage and DB row-level isolation
- per-tenant execution environments
- strict quota enforcement for tokens, jobs, storage, and test runtime
- artifact encryption at rest

---

## Estimated Implementation Complexity

| Component | Complexity | Notes |
|---|---:|---|
| Next.js dashboard | Medium | Mostly CRUD + streaming UI + file viewers |
| FastAPI API layer | Medium | Straightforward if agent runtime boundaries are clean |
| LangGraph orchestrator | High | Core product complexity; state design is critical |
| Coder agent | High | Requires robust prompt contracts, file manifests, and patch discipline |
| Tester/QA agent | High | Reliable test generation + execution + failure normalization is non-trivial |
| Security auditor | Medium-High | Tool integration is easy; useful remediation quality is harder |
| PostgreSQL schema + persistence | Medium | Standard backend engineering with vector support |
| Redis event/queue layer | Low-Medium | Simple operationally |
| ZIP packaging/export | Low | Mostly file orchestration |
| Docker Compose infra | Medium | Straightforward but must support consistent dev/test execution |
| Retrieval / embeddings layer | Medium | Worth it for patch quality and dedupe |
| Observability / tracing | Medium | Essential for debugging agent workflows |

### Highest-risk areas

1. flaky test generation and brittle E2E automation
2. patch loops that regress previously passing behavior
3. uncontrolled prompt/tool sprawl in the Coder Agent
4. insufficient state normalization between agents
5. security scanner false positives overwhelming the repair loop

---

## Recommended Phase 1 Build Order

### Milestone A — Control Plane Skeleton
- FastAPI service
- PostgreSQL schema
- Next.js submission UI
- SSE event stream
- basic job lifecycle

### Milestone B — Orchestrator + Coder
- LangGraph state machine
- monorepo scaffold generation
- artifact manifests
- simple file generation for frontend/backend/infra

### Milestone C — QA Loop
- pytest generation and execution
- playwright generation and execution
- structured bug reports
- coder patch loop

### Milestone D — Security Gate
- bandit/npm audit/eslint security checks
- security finding normalization
- remediation loop

### Milestone E — Retrieval + UX Polish
- pgvector embeddings
- similar-fix retrieval
- improved dashboard drill-downs
- ZIP packaging and final reports

---

## Phase 1 Opinionated Defaults

- backend framework generated by default: **FastAPI**
- frontend framework generated by default: **Next.js App Router**
- auth default: JWT access + refresh token pattern for generated apps
- ORM default: SQLAlchemy 2.x + Alembic
- frontend data layer: TanStack Query
- UI library default: shadcn/ui or minimal Tailwind component set
- backend tests: Pytest
- frontend tests: Playwright
- queue: Redis
- DB: PostgreSQL + pgvector
- reverse proxy: Nginx

---

## Summary

ArchitectAI should be built as a **stateful, auditable, bounded multi-agent system** rather than a free-form autonomous coding bot. LangGraph provides the right execution substrate; FastAPI and Next.js provide a pragmatic control plane; PostgreSQL + pgvector and Redis keep the stack efficient and local-first.

The essential insight is that the product’s moat is not raw code generation. It is the **closed-loop system** that can:

- plan coherently,
- generate consistently,
- test aggressively,
- patch iteratively,
- scan for security risks,
- and expose all of that transparently to the user.

That makes ArchitectAI viable as a Self-Evolving AI SaaS Platform rather than just another code generator.
