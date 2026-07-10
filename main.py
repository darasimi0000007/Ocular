import hashlib
from typing import Any, Dict, List, Optional
from uuid import uuid4

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile

app = FastAPI(title="Ocular Face Detection API")

registered_people: List[Dict[str, Any]] = []


def build_face_signature(face_bytes: bytes) -> List[int]:
    """Create a deterministic signature from image bytes.

    This placeholder implementation is intentionally simple so the API can be
    exercised immediately. In production, replace it with an insightface-based
    embedding pipeline such as RetinaFace + ArcFace.
    """
    digest = hashlib.sha256(face_bytes).digest()
    return [int(byte) for byte in digest[:16]]


def similarity_score(signature_a: List[int], signature_b: List[int]) -> float:
    if not signature_a or not signature_b:
        return 0.0
    if len(signature_a) != len(signature_b):
        return 0.0
    matches = sum(1 for left, right in zip(signature_a, signature_b) if left == right)
    return matches / len(signature_a)


@app.get("/")
async def read_root() -> Dict[str, str]:
    return {"message": "Welcome to Ocular Face Detection API!"}




@app.post("/persons/register")
async def register_person(
    external_id: str = Form(...),
    display_name: str = Form(...),
    email: Optional[str] = Form(None),
    department: Optional[str] = Form(None),
    role: Optional[str] = Form(None),
    face_image: UploadFile = File(...),
) -> Dict[str, Any]:
    if not face_image.filename:
        raise HTTPException(status_code=400, detail="A face image is required")

    face_bytes = await face_image.read()
    if not face_bytes:
        raise HTTPException(status_code=400, detail="The uploaded face image is empty")

    person_id = str(uuid4())
    person_record = {
        "person_id": person_id,
        "external_id": external_id,
        "display_name": display_name,
        "email": email,
        "department": department,
        "role": role,
        "face_signature": build_face_signature(face_bytes),
        "face_image_name": face_image.filename,
    }
    registered_people.append(person_record)

    return {
        "status": "registered",
        "person_id": person_id,
        "person": person_record,
    }


@app.post("/persons/verify")
async def verify_person(face_image: UploadFile = File(...)) -> Dict[str, Any]:
    if not face_image.filename:
        raise HTTPException(status_code=400, detail="A face image is required")

    face_bytes = await face_image.read()
    if not face_bytes:
        raise HTTPException(status_code=400, detail="The uploaded face image is empty")

    candidate_signature = build_face_signature(face_bytes)

    best_match: Optional[Dict[str, Any]] = None
    best_score = 0.0

    for person in registered_people:
        score = similarity_score(candidate_signature, person["face_signature"])
        if score > best_score:
            best_match = person
            best_score = score

    if best_match and best_score >= 0.85:
        return {
            "matched": True,
            "score": round(best_score, 4),
            "person": {
                key: value
                for key, value in best_match.items()
                if key != "face_signature"
            },
        }

    return {
        "matched": False,
        "score": round(best_score, 4),
        "message": "No matching person was found in the registry",
    }


@app.get("/persons")
async def list_people() -> Dict[str, Any]:
    return {"count": len(registered_people), "people": registered_people}

















if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

