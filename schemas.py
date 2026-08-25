from pydantic import BaseModel


class TaskAccepted(BaseModel):
    task_id: str
    status: str = "queued"


class TaskResult(BaseModel):
    task_id: str
    status: str  # PENDING | STARTED | SUCCESS | FAILURE
    result: dict | None = None
