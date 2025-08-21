```
[Public Internet]
      │
      ▼
 ┌──────────┐        HTTPS            ┌───────────────────────────┐
 │  Vercel  │ ──────────────────────► │ FastAPI + Celery (Docker) │
 │ (Viewer) │                         │  Small VM (Render/Fly)    │
 └──────────┘                         └───────────┬───────────────┘
                                                 AMQP/Redis
                                                   │
                                                   ▼
                                  ┌────────────────────────────────┐
                                  │   GPU Workers (Docker)         │
                                  │   • env-gen  • motion-gen      │
                                  │   • audio-gen • packager       │
                                  │   (Modal / Lambda / Paperspace)│
                                  └────────────────┬───────────────┘
                                                   │ SDK (S3/R2)
                                                   ▼
                                    ┌─────────────────────────────┐
                                    │ Cloudflare R2 (Artifacts)  │
                                    │  + public CDN links        │
                                    └─────────────────────────────┘
