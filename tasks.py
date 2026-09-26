

import cv2
import numpy as np

from celery_app import celery_app
from model_loader import extract_embedding
from vector_store import vector_store
from database import SessionLocal
from models import FaceEnrollment, Person
from config import settings
from typing import Any, cast
import models
import build_csv
import datetime
import email_service






#decoding image before enrollment or recognition, image is sent as bytes from the frontend
def _decode_image(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    return cast(Any, cv2.imdecode(arr, cv2.IMREAD_COLOR))








#task for enrolling a face into the database and FAISS index
@celery_app.task(name="tasks.enroll_face")
def enroll_face(person_id: str, image_bytes: bytes, next_faiss_id: int):
    
    image =  _decode_image(image_bytes)
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
        db.refresh(enrollment)
    finally:
        db.close()

    vector_store.add(embedding, faiss_id=next_faiss_id)
    return {"status": "Enrolled Face!"}















#task for recognizing a face from an image
@celery_app.task(name="tasks.recognize_face")
def recognize_face(image_bytes: bytes):
   
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
        if enrollment is None or not cast(bool, enrollment.is_active):
            return {"status": "no_match", "reason": "User is inactive or deleted in the database, present in FAISS"}
        
        else:
            person = db.query(Person).filter(Person.id == enrollment.person_id).first()
            if not person:
                return {"status": "no_match", "reason": "Person not found in the database"}

            #saving attendance record in the database
            record = models.AttendanceRecord(
                        person_id=person.id,
                        matched_similarity=str(similarity),
                    )
            db.add(record)
            db.commit()
            db.refresh(record)
    
            return {
                "status": "matched",
                "person_id": str(person.id),
                "first_name": person.first_name,
                "last_name": person.last_name,
                "similarity": similarity,
            }
      
    finally:
        db.close()













#task for exporting attendance records and emailing it
@celery_app.task(name="tasks.export_and_email_attendance", bind=True, max_retries=3)
def export_and_email_attendance(self, moderator_id: int, organization_id: str):
    db = SessionLocal()
    try:
        cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=0)

        records = (
            db.query(models.AttendanceRecord)
            .join(Person, Person.id == models.AttendanceRecord.person_id)
            .filter(Person.organization_id == organization_id)
            .filter(models.AttendanceRecord.exported_at.is_(None))
            .filter(models.AttendanceRecord.recorded_at < cutoff)
            .all()
        )
        if records is None:
            return {"status": "nothing_to_export"}

        csv_bytes = build_csv.build_csv(records)  # group by recorded_at date inside the CSV

        moderator = db.query(models.Moderator).get(moderator_id)
        if moderator is not None:
            try:
                email_service.send_email(to=str(moderator.email), attachment=csv_bytes, filename="attendance_export.csv")
            except Exception as exc:
                raise self.retry(exc=exc, countdown=60)

        now = datetime.datetime.now(datetime.timezone.utc)
        db.query(models.AttendanceRecord).filter(
            models.AttendanceRecord.id.in_([r.id for r in records])
        ).update({"exported_at": now}, synchronize_session=False)
        db.commit()

        return {"status": "sent", "count": len(records)}
    finally:
        db.close()