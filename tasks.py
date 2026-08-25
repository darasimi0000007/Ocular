"""
tasks.py
This is where FastAPI's request/response cycle hands off to a worker
process. Nothing in here is imported/run inside the FastAPI process
itself -- these functions execute inside separate Celery worker
processes, picked up off the Redis queue.
"""

import cv2
import numpy as np

from celery_app import celery_app
from model_loader import extract_embedding
from vector_store import vector_store
from database import SessionLocal
from models import FaceEnrollment, Person
from config import settings


def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    return cv2.imdecode(arr, cv2.IMREAD_COLOR)


@celery_app.task(name="tasks.enroll_face")
def enroll_face(person_id: str, image_bytes: bytes, next_faiss_id: int):
    """
    Enrollment pipeline. Postgres write happens BEFORE FAISS write --
    durability first, index second. If this task crashes after the
    Postgres commit but before FAISS add, the recognition path just
    won't find a match yet; that's recoverable. The reverse order
    (FAISS first) would risk a vector with no corresponding Postgres
    row, which is worse -- an orphaned, unexplainable match.
    """
    image = _decode_image(image_bytes)
    embedding = extract_embedding(image)
    if embedding is None:
        return {"status": "no_face_detected"}

    db = SessionLocal()
    try:
        enrollment = FaceEnrollment(
            person_id=person_id,
            faiss_index_id=next_faiss_id,
            is_active=True,
        )
        db.add(enrollment)
        db.commit()
    finally:
        db.close()

    vector_store.add(embedding, faiss_id=next_faiss_id)
    return {"status": "enrolled", "faiss_index_id": next_faiss_id}


@celery_app.task(name="tasks.recognize_face")
def recognize_face(image_bytes: bytes):
    """
    Recognition pipeline. FAISS answers "who looks like this" (similarity),
    Postgres answers "is that still a valid, active identity" (truth).
    Never skip the second step -- FAISS keeps deactivated vectors around
    until the next index rebuild (soft-delete drift).
    """
    image = _decode_image(image_bytes)
    embedding = extract_embedding(image)
    if embedding is None:
        return {"status": "no_face_detected"}

    matches = vector_store.search(embedding, top_k=1)
    if not matches:
        return {"status": "no_match"}

    faiss_id, similarity = matches[0]
    if similarity < settings.recognition_threshold:
        return {"status": "no_match", "similarity": similarity}

    db = SessionLocal()
    try:
        enrollment = (
            db.query(FaceEnrollment)
            .filter(FaceEnrollment.faiss_index_id == faiss_id)
            .first()
        )
        # Defensive re-check: this is what guards against soft-delete drift.
        if enrollment is None or not enrollment.is_active:
            return {"status": "no_match", "reason": "inactive_or_missing_in_postgres"}

        person = db.query(Person).filter(Person.id == enrollment.person_id).first()
        return {
            "status": "matched",
            "person_id": str(person.id),
            "full_name": person.full_name,
            "similarity": similarity,
        }
    finally:
        db.close()
