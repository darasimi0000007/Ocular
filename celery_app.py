"""
celery_app.py
Redis plays two roles here: message broker (FastAPI hands off jobs to
workers through it) and result backend (workers write results back so
FastAPI can poll for them). Same Redis instance, two logical uses.
"""

from celery import Celery
from config import settings

celery_app = Celery(
    "ocular",
    broker=settings.redis_url,
    backend=settings.redis_url,\
    include=["tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    # CPU-bound CNN inference -> keep worker concurrency tied to CPU cores,
    # not high like you would for I/O-bound tasks.
    worker_concurrency=4,
)

