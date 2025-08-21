# Sprint 0 — Project Scaffolding (Deep Dive Guide)

Welcome! This guide explains everything we built and how it all fits together so a brand‑new teammate can run the project end‑to‑end in minutes.

---

## What we built in Sprint 0

- A monorepo skeleton with:
  - API service (`FastAPI`) exposing a minimal generations API
  - Worker service (`Celery`) simulating a 5s job and updating status in `Redis`
  - Local orchestration via `Docker Compose` and via a Python virtual env (venv)
  - A web viewer (`Next.js`) that can create a job and poll its status
  - A `Makefile` to make common workflows one command
  - Proper `.gitignore`, `.env.example`, and sensible defaults

This verifies the architecture and the execution flow before adding any AI models.

---

## Repository layout

```
multimodal-generative-fusion/
  apps/
    api/                # FastAPI app
      main.py           # Endpoints + Redis/Celery integration + CORS
    viewer/             # Next.js app (simple UI to create/poll jobs)
      pages/index.js
      package.json
      next.config.js
  workers/
    orchestrator/
      tasks.py          # Celery task: simulates 5s job and updates Redis
  infra/
    compose/
      docker-compose.yaml  # API + Worker + Redis (local dev)
  shared/
    schemas/            # (placeholder) shared Pydantic schemas
  docs/
    README.md           # This document
  .env.example          # Copy to .env and adjust if needed
  Makefile              # Dev convenience commands
  Dockerfile            # Base Python image for api/worker
  requirements.txt      # Python deps for api/worker
```

---

## Core components

- API (FastAPI)
  - `POST /v1/generations` — creates a job ID, sets status to `queued`, enqueues Celery task
  - `GET /v1/generations/{job_id}/status` — reads current status from Redis
  - CORS enabled for local viewer (`http://localhost:3000`) by default; configurable via `CORS_ALLOW_ORIGINS`

- Worker (Celery)
  - Consumes jobs from Redis broker
  - Simulates compute with a 5s sleep
  - Updates Redis status: `queued → running → done`

- Redis
  - Used both as Celery broker/result backend and status store

- Viewer (Next.js)
  - Simple UI to type a prompt, create a job, and poll status every second

---

## Environment variables

Create a `.env` by copying `.env.example`:

```
cp .env.example .env
```

Defaults (from `.env.example`):

- `REDIS_HOST=localhost`
- `REDIS_PORT=6379`
- `REDIS_BROKER_DB=0`
- `REDIS_BACKEND_DB=1`
- `REDIS_STATUS_DB=0`
- `CORS_ALLOW_ORIGINS=http://localhost:3000` (optional override)

The API and the worker both load these via `python-dotenv`.

---

## How to run — three ways

### Option A: Everything via Docker Compose (quickest start)

- Requirements: Docker Desktop running
- Command:

```
make up
```

This builds and starts:
- API at `http://localhost:8000`
- Worker connected to Redis
- Redis at `localhost:6379`

Logs:
```
make logs
```
Stop:
```
make down
```

### Option B: Hybrid (Redis in Docker, API + Worker in venv)

- Start Redis only:
```
make redis
```
- Create venv and install deps:
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Run API and worker locally (two terminals or use the Makefile):
```
# Terminal A
make api

# Terminal B
make worker
```

### Option C: Viewer (Next.js)

- In a separate terminal:
```
cd apps/viewer
npm install
npm run dev
```
- Open `http://localhost:3000`

The page lets you enter a prompt, click “Create Job,” and shows status updates live.

---

## Makefile targets (what they do)

- `make up` — Build + start API, worker, Redis (Docker compose)
- `make down` — Stop and remove compose services
- `make logs` — Tail logs from compose services
- `make redis` — Start Redis only (for hybrid local dev)
- `make api` — Run API from venv using `.env` vars
- `make worker` — Run Worker from venv using `.env` vars
- `make dev` — Run API and Worker concurrently from venv (requires `make redis` first)

---

## API walkthrough

- Create a job
```
curl -s -X POST http://localhost:8000/v1/generations \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"misty cyberpunk alley"}'
# → { "job_id": "...", "status": "queued" }
```

- Poll status
```
JOB_ID=...  # paste the job_id from above
curl -s http://localhost:8000/v1/generations/$JOB_ID/status
# → { "job_id": "...", "status": "running" | "done" }
```

Status transitions are driven by the worker’s Celery task.

---

## Code highlights

- `apps/api/main.py`
  - Loads `.env` and reads Redis host/ports
  - Adds CORS middleware
  - Endpoints enqueue Celery task and read status from Redis

- `workers/orchestrator/tasks.py`
  - Loads `.env`, configures Celery broker/backend
  - `run_pipeline(job_id, prompt)` updates Redis: `running → sleep(5) → done`

- `infra/compose/docker-compose.yaml`
  - Defines services for `api`, `worker`, and `redis`

- `apps/viewer/pages/index.js`
  - Minimal React UI: create a job, then poll `GET /status` every second

---

## Troubleshooting

- Docker not running:
  - Start Docker Desktop, then `make up` again.

- API says “unknown” status:
  - The job_id may be wrong or expired; create a new job.
  - Ensure the worker is running and connected to Redis.

- CORS errors in the browser:
  - Update `CORS_ALLOW_ORIGINS` in `.env` to match your frontend origin, or set `*` (dev only).

- Next.js not reachable at `http://localhost:3000`:
  - Ensure `npm run dev` is running in `apps/viewer` and no port conflicts.

- Redis connection issues:
  - Confirm Redis is listening on `localhost:6379` (`make redis` or `make up`).

- zsh heredoc/one‑liner woes:
  - Prefer `python3 -c 'print(...)'` one‑liners over heredoc in command substitution.

---

## What’s next (preview of Sprint 1)

- Define scene plan schema (`shared/schemas/`)
- Add LLM function-calling endpoint to generate a validated scene plan JSON
- Persist jobs and artifacts in DB (SQLite → Postgres later)

This Sprint 0 foundation makes those next steps straightforward.

---

## Contributing

- Create a feature branch, commit, and open a PR (GitHub compare link is fine).
- Keep Python code formatted and add tests as features grow.
- Avoid committing env files, caches, or build artifacts (see `.gitignore`).

Happy hacking! If you get stuck, copy errors and your last commands into a PR comment or issue.
