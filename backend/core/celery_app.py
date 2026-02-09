import os
from celery import Celery
from backend.core.config import settings

celery_app = Celery(
    "clarity_check",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.workers.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task time limits to prevent hung processes
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,
)
