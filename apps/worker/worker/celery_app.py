"""Celery application configuration."""

from celery import Celery
from worker.config import settings

celery_app = Celery(
    "dataintel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "worker.tasks.planner",
        "worker.tasks.executor",
        "worker.tasks.processor",
    ],
)

from kombu import Queue

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_queues=(
        Queue("celery"),
        Queue("planning"),
        Queue("execution"),
        Queue("processing"),
    ),
    task_routes={
        "worker.tasks.planner.*": {"queue": "planning"},
        "worker.tasks.executor.*": {"queue": "execution"},
        "worker.tasks.processor.*": {"queue": "processing"},
    },
)
