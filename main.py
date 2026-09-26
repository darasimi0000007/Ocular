from fastapi import FastAPI, UploadFile, Depends, HTTPException
import uvicorn
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from database import get_db
from celery_app import celery_app
from face_service import next_faiss_id
from schemas import TaskAccepted, TaskResult, PersonCreated, PersonCreate, ModeratorSignup, ModeratorCreated
import tasks  # noqa: F401  (import registers tasks with celery_app)
from database import Base, engine
from contextlib import asynccontextmanager
import uuid
from models import Person, Organization, Moderator
import models
import hashing
from oauth2 import get_current_moderator
import authentication




#on event startup, create database tables
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure the database tables are created on startup
    Base.metadata.create_all(bind=engine)
    yield








#application instance
app = FastAPI(title="Ocular Face Detection API", lifespan = lifespan)








@app.get("/")
async def root():
    return {"detail": "Ocular Face Detection API is running"}








#enrolling a face
@app.post("/persons/{person_id}/enroll", response_model=TaskAccepted, tags = ["Tasks"])
async def enroll(person_id: str, file: UploadFile, 
                 db: Session = Depends(get_db), 
                 current_moderator: Moderator = Depends(get_current_moderator)):
    image_bytes = await file.read()

    # Allocate the id here (in the request/response cycle, against Postgres)
    # rather than inside the worker, so the caller can reason about it
    # deterministically and we avoid two workers racing on the same max().
    faiss_id = next_faiss_id(db)

    async_result = tasks.enroll_face.delay(person_id, image_bytes, faiss_id)
    return TaskAccepted(task_id=async_result.id)










#recognizing a face
@app.post("/recognize", response_model=TaskAccepted, tags = ["Tasks"])
async def recognize(file: UploadFile, current_moderator: Moderator = Depends(get_current_moderator)):
    image_bytes = await file.read()
    async_result = tasks.recognize_face.delay(image_bytes)
    return TaskAccepted(task_id=async_result.id)








#exporting and emailing attendance
@app.get("/export_attendance", response_model = TaskAccepted, tags = ["Tasks"])
async def export_attendance(current_moderator: Moderator = Depends(get_current_moderator)):
    async_result = tasks.export_and_email_attendance.delay(current_moderator.id, str(current_moderator.organization_id))
    return TaskAccepted(task_id = async_result.id)








#getting a completed task result
@app.get("/tasks/{task_id}", response_model=TaskResult, tags = ["Tasks"])
async def get_task_result(task_id: str, current_moderator: Moderator = Depends(get_current_moderator)):
    result = AsyncResult(task_id, app=celery_app)

    if result.status == "FAILURE":
        raise HTTPException(status_code=500, detail=str(result.result))

    return TaskResult(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else None,
    )












#creating a person in the Persons table of the database. Important before enrolling a face for that person
@app.post("/organizations/persons", tags = ["Create Person"])
async def create_person(request: PersonCreate, db: Session = Depends(get_db), 
                        current_moderator: Moderator = Depends(get_current_moderator)):
    person = Person(
        organization_id=current_moderator.organization_id,
        external_id=request.external_id,
        first_name=request.first_name,
        last_name=request.last_name,
    )
    db.add(person)
    db.commit()
    db.refresh(person)
    # return PersonCreated(person_id=person.id)
    return {"person_id": person.id}





# #registering a new organization in the Organizations table of the database. Important before creating a person for that organization
# @app.post("/organizations/{org_slug}/persons", response_model=PersonCreated)
# async def create_person(org_slug: str, payload: PersonCreate, db: Session = Depends(get_db)):
#     org = db.query(Organization).filter(Organization.slug == org_slug).first()
#     if not org:
#         raise HTTPException(status_code=404, detail="Organization not found")
#     person = Person(organization_id=org.id, external_id=payload.external_id, ...)
#     ...










#first moderator signup endpoint for authentication.
@app.post("/signup", tags = ["Signup"])
async def create_Moderator(request: ModeratorSignup, db: Session = Depends(get_db)):
    org = Organization(name=request.organization_name, slug=request.organization_slug)
    db.add(org)
    db.flush()
    moderator = Moderator(
        organization_id=org.id,
        first_name = request.first_name,
        last_name = request.last_name,
        email=request.email,
        password=hashing.Hash().bcrypt(request.password)
    )
    db.add(moderator)
    db.commit()
    db.refresh(moderator)
    # return ModeratorCreated(moderator_id=moderator.id, organization_id=org.id)
    return {"organization_id": org.id}










#additional moderators signup endpoint for authentication. This is for adding more moderators to an existing organization
@app.post("/organizations/{slug}/moderators", response_model=ModeratorCreated, tags = ["Signup"])
async def signup(slug: str, request: ModeratorSignup, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.slug == slug).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    moderator = Moderator(
        organization_id=org.id,
        first_name = request.first_name,
        last_name = request.last_name,
        email=request.email,
        password=hashing.Hash().bcrypt(request.password)
    )
    db.add(moderator)
    db.commit()
    db.refresh(moderator)
    # return ModeratorCreated(moderator_id=moderator.id, organization_id=moderator.organization_id)
    return {"organization_id": org.id}








#router for authentication(login)
app.include_router(authentication.router)






















if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

