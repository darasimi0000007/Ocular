Description
Ocular is a Face Detection Application that uses insightface (RetinaFace + ArcFace) to make face detections by capturing live face data through a webcam. The backend is implemented with FastAPI and is designed to support both educational and corporate attendance scenarios.

The current API already exposes generic endpoints for registering a person with identity details and face data, and for verifying a captured image against the registered registry.

## API endpoints

### Register a person
- POST /persons/register
- Form fields:
  - external_id: string
  - display_name: string
  - email: optional string
  - department: optional string
  - role: optional string
  - face_image: uploaded image file

### Verify a person
- POST /persons/verify
- Form field:
  - face_image: uploaded image file

### List registered people
- GET /persons

## Run locally
```bash
c:/Users/LENOVO/Documents/Ocular/.venv/Scripts/python.exe -m uvicorn main:app --reload
```

## Test locally
```bash
c:/Users/LENOVO/Documents/Ocular/.venv/Scripts/python.exe -m unittest discover -s tests -v
```

RetinaFace is responsible for detecting the face. ArcFace matches whose face it is to the user data.

System Architecture Diagram for Ocular

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