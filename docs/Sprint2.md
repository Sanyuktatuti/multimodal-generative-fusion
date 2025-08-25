## Sprint 2 — Environment Generation (Fast Path)

Goal: Turn a validated ScenePlan into a basic 3D environment artifact (scene.glb + manifest.json) using a fast path and wire it end-to-end through our API and workers. Includes local and SageMaker execution, immutable image lock, and S3 artifacts with presigned download URLs.

### What we built

- Orchestrated env generation end-to-end via Celery queues
- Local stub path for quick runs; cloud path via AWS SageMaker Processing
- Immutable container image tag for rollback safety
- Standard S3 artifact layout and a manifest schema
- New API routes to submit a job, check status, and fetch presigned URLs

### Code map (files touched)

- API
  - `apps/api/main.py` — mounts new envgen router
  - `apps/api/routes/envgen.py` — routes:
    - `POST /v1/generations` → submit env job (SageMaker Processing)
    - `GET /v1/generations/{task_id}/status` → Celery task state
    - `GET /v1/generations/{job_id}/presigned` → signed URLs for S3 artifacts

- Workers
  - `workers/env_gen/tasks.py` — two tasks:
    - `run_env(job_id, plan_path, provider, version)` — local provider execution (stub/fast)
    - `run_env_cloud(prompt)` — submits SageMaker Processing job (immutable ECR image)
  - `workers/orchestrator/tasks.py` — planning stage writes plan to `/app/tmp`, enqueues env task (stub path remains available)

- Providers
  - `shared/providers/env_triposr_fast.py` — fast path provider with lazy deps, creates GLB
  - `shared/providers/factory.py` — registers `("env", "sdxl_triposr")` and `("env","stub")`

- Schemas
  - `shared/schemas/manifest.v0.json` — JSON Schema for job manifest
  - `shared/schemas/scene_plan.py` — Pydantic v1 compatible ScenePlan

- Infra
  - `infra/compose/docker-compose.yaml` — mounts `/app/tmp`, sets `REDIS_HOST`, mounts `~/.aws` into API and env worker, sets `AWS_PROFILE` and region
  - `infra/sagemaker/entrypoint_processing.py` — reads `PROMPT_JSON`, writes `scene.glb` + `manifest.json`, uploads to `s3://.../jobs/<job_id>/...`

- Dependencies
  - `requirements.txt` — pinned workable versions for local build (removed pymeshlab for local images; still used in GPU images later)

### Immutable image (rollback)

We built and pushed the SageMaker image, then locked it:

1) Get digest of `:latest` and tag as `sprint2-release`:

```bash
aws ecr describe-images \
  --repository-name mmf-envgen \
  --query 'imageDetails[?imageTags && contains(imageTags, `latest`)].imageDigest' \
  --output text --region us-east-1 --profile mmfusion

aws ecr put-image --repository-name mmf-envgen \
  --image-tag sprint2-release \
  --image-manifest "$(aws ecr batch-get-image --repository-name mmf-envgen \
                      --image-ids imageDigest=sha256:... --query 'images[0].imageManifest' --output text)" \
  --region us-east-1 --profile mmfusion
```

2) `.env` uses the immutable tag:

```ini
ECR_IMAGE_URI=398341427473.dkr.ecr.us-east-1.amazonaws.com/mmf-envgen:sprint2-release
AWS_REGION=us-east-1
S3_BUCKET=s3://multimodal-fusion-models-sanyuktatuti
SAGEMAKER_ROLE_ARN=arn:aws:iam::398341427473:role/SageMakerProcessingRole
SM_INSTANCE_TYPE=ml.m5.xlarge
SM_VOL_GB=50
SM_MAX_SEC=1800
```

### Standardized S3 layout + Manifest schema

- Layout: `s3://multimodal-fusion-models-sanyuktatuti/jobs/<job_id>/scene.glb`, `manifest.json`
- Schema: `shared/schemas/manifest.v0.json` (Draft 2020-12)

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "MMF Manifest v0",
  "type": "object",
  "required": ["job_id", "prompt", "artifacts", "provenance"],
  "properties": {
    "job_id": { "type": "string" },
    "prompt": { "type": "string" },
    "artifacts": {
      "type": "object",
      "properties": {
        "scene_glb": { "type": "string" },
        "refs": { "type": "array", "items": { "type": "string" } }
      }
    },
    "provenance": { "type": "object" }
  }
}
```

### API usage (local demo)

1) Start services (mounts `~/.aws` for creds):

```bash
docker compose -f infra/compose/docker-compose.yaml up -d api env_worker redis
```

2) Submit a generation:

```bash
curl -s -X POST localhost:8000/v1/generations \
  -H 'content-type: application/json' \
  -d '{"prompt":"misty cyberpunk alley with neon"}'
# => {"task_id":"<id>"}
```

3) Poll status:

```bash
curl -s localhost:8000/v1/generations/<task_id>/status
# => {"state":"SUCCESS","job_id":"envgen-XXXXXXX","status":"submitted"}
```

4) Get presigned URLs:

```bash
curl -s localhost:8000/v1/generations/<job_id>/presigned
# => { manifest_url: "https://...", scene_url: "https://..." }
```

### Notes and safeguards

- Providers are lazy-loaded; local path uses stub or fast provider to avoid heavy deps
- SageMaker image is `linux/amd64` to prevent Exec format errors
- If using CPU instance for Processing, SDXL downloads may require `ml.m5.xlarge` or larger for memory
- Result backend in containers is minimal; status route returns Celery state and any dict payload when available

### Done criteria (met)

- POST creates an env generation task (SageMaker Processing)
- Status surfaces SUCCESS with job_id
- Presigned URLs download `scene.glb` and `manifest.json` from S3
- Immutable image tag `sprint2-release` configured


