```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Experience Layer (Vercel)                       │
│  Next.js Viewer (Three.js/WebXR)                                            │
│  • Prompt form + progress UI                                                │
│  • Scene preview (GLB + optional .splat)                                    │
│  • Download buttons (GLB/FBX/MP3/MP4)                                       │
└───────────────────────────────▲───────────────────────────────┬─────────────┘
                                │ HTTPS (REST/JSON)             │ Signed URLs (CDN)
                                │                                │
┌───────────────────────────────┴───────────────────────────────▼─────────────┐
│                           API & Orchestration Layer (Docker)                │
│  FastAPI Gateway                                                             │
│  • /v1/generations (create/status/result)                                    │
│  • Auth/rate-limit/safety filters                                            │
│                                                                              │
│  Orchestrator (Celery)                                                       │
│  • Stage graph: planning → env → motion → audio → sync → package             │
│  • Retries, idempotency, per‑stage caching                                   │
│                                                                              │
│  State & Metadata                                                            │
│  • SQLite/Postgres (jobs, manifests)                                         │
│  • Redis (queues, ephemeral status, cache keys)                              │
└───────────────────────────────▲───────────────────────────────┬─────────────┘
                                │ Celery tasks (AMQP/Redis)     │
                                │                                │
┌───────────────────────────────┴───────────────────────────────▼─────────────┐
│                      GPU Workers (Docker on GPU-capable host)               │
│  env-gen worker                                                             │
│  • SDXL (style refs) → TripoSR/Zero123++ (image→3D) → mesh cleanup/bake     │
│  • (optional) background 3D Gaussian Splat                                  │
│                                                                              │
│  motion-gen worker                                                           │
│  • Text→motion diffusion → retarget → foot IK → clip export                 │
│                                                                              │
│  audio-gen worker                                                            │
│  • Text→music + SFX → stem mix → loudness normalization                      │
│                                                                              │
│  packager worker                                                             │
│  • Compose scene GLB + char FBX/GLB + MP3/WAV + MP4 flythrough               │
│  • Build manifest.json                                                       │
└───────────────────────────────▲───────────────────────────────┬─────────────┘
                                │ Artifact upload               │ Manifest read
                                │ (SDK/S3 API)                  │ (HTTPS)
┌───────────────────────────────┴───────────────────────────────▼─────────────┐
│                 Artifact Storage & Delivery (Project-budget choices)        │
│  Cloudflare R2 (object storage, $0 egress)  →  Public CDN links             │
│  • /jobs/{id}/scene.glb                                                     │
│  • /jobs/{id}/character.glb / .fbx                                          │
│  • /jobs/{id}/music.mp3 / sfx.wav                                           │
│  • /jobs/{id}/render.mp4                                                    │
│  • /jobs/{id}/manifest.json                                                 │
└─────────────────────────────────────────────────────────────────────────────┘
