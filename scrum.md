# 🎬 Multimodal Fusion — Text to Scene Pipeline

## 🧭 High-level Roadmap (Build Order)

- **Sprint 0** — Repo & Dev Environment  
- **Sprint 1** — Prompt → Scene Plan (LLM planner)  
- **Sprint 2** — Environment Generation (image→3D fast path)  
- **Sprint 3** — Web Viewer & Hosting (GLB/Splat)  
- **Sprint 4** — Character + Motion (text→motion + retarget)  
- **Sprint 5** — Audio (music + SFX) & Timeline Sync  
- **Sprint 6** — Packaging, Downloads, & Job Orchestration  
- **Sprint 7** — Cost Guardrails, Caching, and Polish  
- *(Optional)* **Sprint 8** — “Heavy Path” Text→3D for hero assets  

---

## 🚀 Sprint Details

### Sprint 0 — Repo & Dev Environment
**Goal**: working skeleton you can run end-to-end “hello world”.  
**Deliverables**:
- Monorepo with `apps/`, `workers/`, `infra/`
- Local run via `docker compose up`
- Minimal REST API with job creation & status endpoints  

**Tech**: FastAPI, Celery + Redis, Docker Compose, SQLite, Next.js + Three.js  
**DoD**:  
- `POST /v1/generations` → returns job_id  
- `GET /v1/generations/:id/status` → queued/running/done  

---

### Sprint 1 — Prompt → Scene Plan (LLM planner)
**Goal**: deterministic scene JSON from text.  
**Deliverables**: JSON schema + LLM function-calling → validated scene graph.  
**DoD**:  
- API returns `scene_plan.json` with env, objects, character, camera, audio.  

---

### Sprint 2 — Environment Generation
**Goal**: fast, cheap 3D environment generation.  
**Deliverables**: SDXL reference board + TripoSR/Zero123++ per-asset → GLB.  
**DoD**: Worker produces `scene.glb` and/or `background.splat`.  

---

### Sprint 3 — Web Viewer & Hosting
**Goal**: shareable scene URL with realtime preview.  
**Deliverables**: Next.js viewer, orbit controls, perf stats, hosting via Vercel + Cloudflare R2.  
**DoD**: Viewer runs 60fps; loads assets by JOB_ID.  

---

### Sprint 4 — Character + Motion
**Goal**: animated character placed in scene.  
**Deliverables**: avatar generation, text→motion, retarget, IK.  
**DoD**: Viewer shows realistic character motion synced with scene.  

---

### Sprint 5 — Audio (Music + SFX) & Sync
**Goal**: synced music + ambience.  
**Deliverables**: text→music, SFX events, mixer → mp3/wav.  
**DoD**: Viewer streams synced audio with animation.  

---

### Sprint 6 — Packaging & Orchestration
**Goal**: stable pipeline + artifacts.  
**Deliverables**: job graph, signed URLs, downloads (GLB/FBX/MP3/MP4).  
**DoD**: `/v1/generations/:id/result` returns viewer_url + downloads.  

---

### Sprint 7 — Cost Guardrails & Polish
**Goal**: cost ≈ $0.17–$0.20 per job.  
**Deliverables**: cache, quotas, resolution caps, prompt safety filters.  
**DoD**: 100 fast-path jobs complete within budget.  

---

### Sprint 8 (Optional) — Heavy Path Text→3D
**Goal**: bespoke high-fidelity hero props.  
**Deliverables**: diffusion text→3D hero assets with PBR + LOD.  
**DoD**: Ultra detail prop generated with cost estimator (~$2/job).  

---

## 📦 Suggested Repo Structure

multimodal-fusion/
apps/
api/ # FastAPI, routers, schemas
viewer/ # Next.js + Three.js
workers/
orchestrator/ # stage graph, retries
env_gen/ # SDXL, TripoSR/Zero123++, splats
motion_gen/ # text→motion, retarget, IKs
audio_gen/ # text→music, SFX, mix
packager/ # GLB/FBX/MP4, manifest publish
models/ # weights, converters
infra/
docker/ # Dockerfiles
compose/ # docker-compose.yaml
scripts/ # seed, migrate, tests
shared/
schemas/ # scene JSON, manifest
utils/ # IO, hashing, logging
README.md


---

## 🔌 External Services (budget defaults)
- GPU: Modal pay-per-second or Colab Pro  
- Storage: Cloudflare R2 (cheap, zero egress)  
- Frontend: Vercel (free)  
- Auth: Clerk/Supabase Auth or simple tokens  
- DB: SQLite → Postgres (if multi-user)  

---

## ✅ Acceptance Demo (after Sprint 6)
Prompt: *“misty cyberpunk alley at night; neon kanji; detective walking slowly; rain; lo-fi minor 80 bpm.”*  
- Stage-by-stage job progress  
- Viewer loads meshes + splat + character + synced music/SFX  
- Downloads: GLB/FBX/MP3/MP4  
- Cost shown: ~$0.18 (fast path)  

---

## 🧠 Risks & Mitigations
- **Geometry quality** → curated base kit + mesh cleanup  
- **Motion artifacts** → foot locking + slower cycles  
- **Viewer performance** → Draco/meshopt, mipmaps, fewer draw calls  
- **Cost creep** → strict fast path defaults, quotas, caching  
