Description
Ocular is a Face Detection Application that uses insightface (RetinaFace + ArcFace) to make face detections by capturing live face data through a webcam. The backend is implemented with FastAPI and is designed to support both educational and corporate attendance scenarios.

The current API already exposes generic endpoints for registering a person with identity details and face data, and for verifying a captured image against the registered registry.

RetinaFace is responsible for detecting the face. ArcFace matches whose face it is to the user data.

System Architecture for Ocular

┌─────────────────────────────────────────────┐
│  Flutter mobile app                          │
│  Capture + compress photo                    │
└───────────────────┬───────────────────────────┘
                     │
        ┌────────────┴────────────┐
        ▼                         ▼
┌───────────────────┐   ┌───────────────────────┐
│ FastAPI REST       │   │ FastAPI WebSocket     │
│ Enrollment, auth,  │   │ Live capture feedback │
│ CRUD               │   │ (framing/quality)     │
└─────────┬──────────┘   └───────────┬───────────┘
          │                          │
          └────────────┬─────────────┘
                        ▼
        ┌───────────────────────────────┐
        │  Async task queue (Celery)    │
        │  hands off to...              │
        └───────────────┬───────────────┘
                         ▼
        ┌───────────────────────────────┐
        │  CNN inference                │
        │  PyTorch detection + embedding│
        └───────────────┬───────────────┘
                         │
           ┌─────────────┴─────────────┐
           ▼                           ▼
┌───────────────────┐       ┌───────────────────────┐
│ PostgreSQL         │       │ FAISS vector store    │
│ Metadata + logs    │       │ Face embedding index  │
└───────────────────┘       └───────────────────────┘

















# Ocular — Skeleton Wiring

## The request lifecycle (this is the part that matters)

```
Client
  │  POST /recognize (image)
  ▼
FastAPI (main.py)
  │  reads file bytes, does NOT touch the model
  │  tasks.recognize_face.delay(image_bytes)
  ▼
Redis (broker)
  │  job sits on a queue
  ▼
Celery worker (tasks.py, separate process)
  │  1. model_loader.extract_embedding()   <- InsightFace, CPU-bound
  │  2. vector_store.search()              <- FAISS, in-memory, fast
  │  3. SessionLocal() query Postgres      <- re-verify is_active, resolve identity
  │  writes result back to Redis (result backend)
  ▼
Client
  │  polls GET /tasks/{task_id} until status == SUCCESS
  ▼
FastAPI (main.py)
     reads result from Redis via AsyncResult, returns it
```

FastAPI never imports `model_loader.py` directly and never calls FAISS
directly. It only ever talks to Celery/Redis for anything inference-related.
That separation is the whole point: the web process stays responsive under
load because slow CPU work never happens inside it.

## Processes you actually run (3, all separate)

```bash
# 1. FastAPI (the web server)
uvicorn main:app --reload

# 2. Celery worker (the inference process — this is what loads InsightFace)
celery -A celery_app worker --loglevel=info

# 3. Redis + Postgres (infra, via Docker)
docker compose up -d redis postgres
```

Note the model only loads inside the **worker** process (first call to
`get_model()` in `model_loader.py`), never inside the FastAPI process —
consistent with FastAPI staying thin.

## Where each concern lives

| Concern | File | Notes |
|---|---|---|
| HTTP surface | `main.py` | thin, no inference |
| Async job definitions | `tasks.py` | runs inside Celery workers only |
| Broker/backend config | `celery_app.py` | Redis both ways |
| CNN inference | `model_loader.py` | loaded once per worker, frozen extractor |
| Vector similarity | `vector_store.py` | FAISS, keyed by `faiss_index_id` |
| Structured truth | `models.py` / `database.py` | Postgres, source of truth |
| id bridging | `face_service.py` | allocates the shared int key |

## Things this skeleton deliberately simplifies

- `next_faiss_id()` uses `max()+1` — fine for portfolio scale, would race
  under concurrent enrollments in production (use a Postgres sequence).
- No retry/backoff policy on Celery tasks yet.
- No periodic FAISS rebuild job to purge soft-deleted vectors (the thing
  that fixes soft-delete drift long-term) — recognition currently
  defends against it at read-time in `tasks.recognize_face`, which is
  correct but doesn't shrink the index.
- Auth/multi-tenancy (organization scoping) isn't wired into the routes yet.
