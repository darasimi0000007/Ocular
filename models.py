"""
models.py
Structured metadata lives here. Note: faiss_index_id is the ONLY bridge
between Postgres and FAISS. FAISS never stores anything else about a
person -- just the vector at that integer position.
"""

import uuid
from sqlalchemy import Column, String, Boolean, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from database import Base


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String, unique=True, nullable=False)  # e.g. "riverside-academy"
    name = Column(String, nullable=False)

    org_link = relationship("Moderator", back_populates="moderator_link")








#user signup model for authentication
class Moderator(Base):
    __tablename__ = "moderators"
    
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    #role = Column(String, default="admin")  # admin / teacher / class_rep, etc.
    password = Column(String)


    moderator_link = relationship("Organization", back_populates="org_link")


    #person_link = relationship("Person", back_populates="mod_link")







class Person(Base):
    __tablename__ = "persons"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    external_id = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)

    enrollments = relationship("FaceEnrollment", back_populates="person")

    #mod_link = relationship("Moderator", back_populates="person_link")








class FaceEnrollment(Base):
    __tablename__ = "face_enrollments"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)

    # The bridge key. This integer is the row position of the vector in FAISS.
    faiss_index_id = Column(Integer, unique=True, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    person = relationship("Person", back_populates="enrollments")








class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    person_id = Column(UUID(as_uuid=True), ForeignKey("persons.id"), nullable=False)
    matched_similarity = Column(String)  # store as string/float, your call
    recorded_at = Column(DateTime, server_default=func.now())









