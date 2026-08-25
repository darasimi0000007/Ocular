from fastapi import FastAPI, UploadFile, Depends, HTTPException
import uvicorn
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from database import get_db
from celery_app import celery_app
from face_service import next_faiss_id
from schemas import TaskAccepted, TaskResult
import tasks  # noqa: F401  (import registers tasks with celery_app)


app = FastAPI(title="Ocular Face Detection API")


#enrolling a face
@app.post("/persons/{person_id}/enroll", response_model=TaskAccepted)
async def enroll(person_id: str, file: UploadFile, db: Session = Depends(get_db)):
    image_bytes = await file.read()

    # Allocate the id here (in the request/response cycle, against Postgres)
    # rather than inside the worker, so the caller can reason about it
    # deterministically and we avoid two workers racing on the same max().
    faiss_id = next_faiss_id(db)

    async_result = tasks.enroll_face.delay(person_id, image_bytes, faiss_id)
    return TaskAccepted(task_id=async_result.id)



#recognizing a face
@app.post("/recognize", response_model=TaskAccepted)
async def recognize(file: UploadFile):
    image_bytes = await file.read()
    async_result = tasks.recognize_face.delay(image_bytes)
    return TaskAccepted(task_id=async_result.id)



#getting a completed task result
@app.get("/tasks/{task_id}", response_model=TaskResult)
async def get_task_result(task_id: str):
    result = AsyncResult(task_id, app=celery_app)

    if result.status == "FAILURE":
        raise HTTPException(status_code=500, detail=str(result.result))

    return TaskResult(
        task_id=task_id,
        status=result.status,
        result=result.result if result.ready() else None,
    )














if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

