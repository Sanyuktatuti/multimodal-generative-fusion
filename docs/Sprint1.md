# Sprint 1 — Prompt → Scene Plan (Deep Dive Guide)

This guide explains the full implementation of Sprint 1 so a brand‑new teammate can run it end‑to‑end. It covers schemas, the LLM planner with fallbacks, API routes, worker pipeline, configuration, dependencies, and troubleshooting.

---

## What Sprint 1 delivers

- Pydantic schema for a structured Scene Plan
- Planner service that turns natural language prompts into a validated `ScenePlan` (LLM-backed)
- Fallback chain (OpenAI → Anthropic → Together/Llama) with automatic retries
- API endpoint `/v1/plan` that returns a `scene_plan` JSON
- Worker planning stage that writes the plan to disk and advances job status
- Config and docker-compose updates to inject secrets from `.env`

---

## Files added/updated

- `shared/schemas/scene_plan.py` — Pydantic (v2) schema definitions
- `apps/api/services/planner_client.py` — Planner orchestrator and providers
- `apps/api/routes/planning.py` — Planner HTTP endpoint
- `workers/orchestrator/tasks.py` — Planning stage in Celery pipeline (uses LLM planner)
- `infra/compose/docker-compose.yaml` — load `.env` for API/worker
- `requirements.txt` — HTTP/LLM deps
- `docs/Sprint1.md` — this document

---

## 1) Scene Plan Schema (Pydantic v2)

File: `shared/schemas/scene_plan.py`

Key types:
- `EnvSpec`: theme, weather, time of day
- `ObjectSpec`: typed objects with instance counts and tags
- `CharacterSpec`: humanoid rig + motion description
- `CameraSpec`: path + bounded duration
- `AudioSpec`: music/SFX hints
- `ScenePlan`: ties all of the above with length bounds for `objects`

Notes:
- Uses `Field(..., min_length, max_length)` for list constraints (Pydantic v2)
- Default values keep plans robust even with minimal inputs

---

## 2) Planner service with fallbacks

File: `apps/api/services/planner_client.py`

- Orchestrator: `PlannerOrchestrator` builds a provider chain based on which keys exist in `.env`.
  - Primary: `OpenAIProvider` (JSON mode via `response_format = { type: "json_object" }`)
  - Fallback 1: `AnthropicProvider`
  - Fallback 2: `TogetherProvider` (generic chat API for Llama‑hosted models)
- All providers:
  - Receive the schema (via `ScenePlan.model_json_schema()`)
  - Are instructed to return ONLY a JSON object (no markdown fences)
  - Parse JSON, with a final fence‑strip retry if necessary
  - Retries are implemented via `tenacity` with exponential backoff
- The orchestrator validates outputs against the schema and auto‑repairs missing essentials:
  - Ensures `camera` and `audio` defaults if provider omitted them
- Failure behavior:
  - If all providers fail, raises `PlannerProviderError`

Environment variables used:
- `OPENAI_API_KEY`, `OPENAI_MODEL` (default `gpt-4o-mini`)
- `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (default `claude-3-5-sonnet-20240620`)
- `TOGETHER_API_KEY`, `TOGETHER_MODEL` (default `meta-llama-3.1-70b-instruct`)
- Optional base URLs for proxies: `OPENAI_BASE_URL`, `ANTHROPIC_BASE_URL`, `TOGETHER_BASE_URL`

---

## 3) API route — `/v1/plan`

File: `apps/api/routes/planning.py`

- Accepts: `{ "prompt": string, "seed": int }`
- Calls `PlannerOrchestrator().plan(prompt)`
- Returns: `{ "scene_plan": <ScenePlan as JSON> }`
- Errors: 502 with upstream failure reasons (without leaking secrets)

Example curl:
```bash
curl -s -X POST http://localhost:8000/v1/plan \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"misty cyberpunk alley at night; light rain; orbit camera"}' | jq .
```

---

## 4) Worker — planning stage in the pipeline

File: `workers/orchestrator/tasks.py`

- Status stored in Redis as structured JSON: `{ status, detail? }`
- Steps:
  1. Set status to `planning`
  2. Run LLM planner (`asyncio.run(planner.plan(prompt))`)
  3. Persist plan to `/tmp/<job_id>_plan.json`
  4. Set status `planned` with `{ plan_path }`
  5. For Sprint 1, mark `done` (next sprints will call env generator)
- On error: sets status `error` with `{ stage: "planning", message }`

---

## 5) Config & Secrets

- `.env` (not committed) must include at least one provider key, ideally OpenAI:
```
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
# Optional fallbacks
ANTHROPIC_API_KEY=sk-ant-...
TOGETHER_API_KEY=...
```
- `infra/compose/docker-compose.yaml` now loads `.env` for `api` and `worker`.
- Provider choices for later stages live in `shared/config/model_env.yaml` (used by generators in future sprints).

---

## 6) Dependencies

File: `requirements.txt` (appended)
- `httpx`, `tenacity`, `openai>=1.30.0`, `anthropic>=0.30.0`, `pyyaml`

Install locally:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 7) How to run (local venv)

1) Start Redis (compose):
```bash
make redis
```
2) API and worker (two terminals):
```bash
make api
# new terminal
make worker
```
3) Planner test:
```bash
curl -s -X POST http://localhost:8000/v1/plan \
  -H 'Content-Type: application/json' \
  -d '{"prompt":"misty cyberpunk alley at night; light rain; orbit camera"}' | jq .
```
4) Job flow test:
```bash
JOB=$(curl -s -X POST http://localhost:8000/v1/generations -H 'Content-Type: application/json' -d '{"prompt":"misty cyberpunk alley; light rain; dolly"}')
JID=$(python3 -c 'import json,sys; print(json.loads(open(0).read())["job_id"])' <<< "$JOB")
for i in $(seq 1 8); do curl -s http://localhost:8000/v1/generations/$JID/status; echo; sleep 1; done
```

---

## 8) How to run (Docker Compose)

```bash
docker compose -f infra/compose/docker-compose.yaml up --build
# Then use the same curl tests as above (port 8000)
```

---

## 9) Troubleshooting

- 502 from `/v1/plan`:
  - Check `OPENAI_API_KEY` (or fallbacks) in `.env`
  - Inspect API logs; provider retries are automatic
- Stuck `queued` status:
  - Ensure worker is running and connected to Redis
- JSON parse errors from providers:
  - We strip code fences and re-parse; schema validation will surface errors
- Port already in use:
  - Kill old `uvicorn` processes or change port; `make down` for docker services

---

## 10) Why this design is LLMOps-ready

- Stable planner interface and fallbacks ensure availability and easy provider swaps
- Schema‑first planning keeps outputs deterministic and validates early
- Structured statuses and persisted plan enable observability and retries
- `.env` driven secrets and compose wiring keep local/dev simple; production can inject via secret managers

This completes Sprint 1 (full). Next sprints consume `ScenePlan` to generate environments, motion, and audio assets.
