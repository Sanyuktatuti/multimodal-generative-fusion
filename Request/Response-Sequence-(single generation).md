
User (browser)                      API (FastAPI)                   Celery/Workers                     Storage (R2)                 Viewer (Next.js)
-----------------------------------------------------------------------------------------------------------------------------------------------------------------
1) POST /v1/generations  ─────────────────►  create job, id=J
                                     enqueue "planning:J"
                                     return {job_id:J, status:"queued"}

2) GET /status?J  ◄───────────────────────  polling (or SSE/websocket)
                     status from Redis → "planning"

3) planning:J  (LLM → scene_plan.json) ───────────────────────────────────────►  (no storage yet)
   set status "env"

4) env:J  (SDXL → TripoSR → GLB/.splat) ──────────────────────────────────────►  upload scene.glb, background.splat
                                          set status "motion"                                                ▲
                                                                                                            │ (signed URLs)
5) motion:J (text→motion → FBX/GLB) ──────────────────────────────────────────►  upload character.glb / .fbx │
                                          set status "audio"                                                 │
                                                                                                            │
6) audio:J (text→music+SFX → MP3/WAV) ───────────────────────────────────────►  upload music.mp3 / sfx.wav   │
                                          set status "sync"                                                  │
                                                                                                            │
7) sync:J (timeline JSON + camera path) ──────────────────────────────────────►  upload timeline.json         │
                                          set status "package"                                               │
                                                                                                            │
8) package:J (manifest + MP4 render) ─────────────────────────────────────────►  upload manifest.json, mp4    │
                                          set status "done"                                                  │
                                                                                                            │
9) GET /result?J  ◄──────────────────────  returns viewer_url + download links (from manifest)               │
                                                                                                            │
10) open viewer_url  ───────────────────────────────────────────────────────────────────────────────────────►  loads manifest, pulls assets via CDN,
                                                                                                               plays scene + audio
