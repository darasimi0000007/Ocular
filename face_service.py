"""
face_service.py
Small helpers that sit between the FastAPI route and the Celery task.
Keeps id-allocation logic out of both the route and the worker task.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from models import FaceEnrollment


def next_faiss_id(db: Session) -> int:
    """
    Simple monotonic allocator: max existing id + 1. Fine at portfolio
    scale. At real scale you'd use a Postgres sequence to avoid a
    race between two concurrent enrollments reading the same max().
    """
    current_max = db.query(func.max(FaceEnrollment.faiss_index_id)).scalar()
    return (current_max or 0) + 1
