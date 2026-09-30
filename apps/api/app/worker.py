"""
Celery client shim for apps/api.
Sends tasks to Celery queues via send_task without importing worker task implementations.
"""

from celery import Celery
from app.config import settings

celery_app = Celery(
    "dataintel",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)


def enqueue_plan_workflow(run_id: str, prompt: str, hints: dict | None = None):
    """Enqueue planning task on the 'planning' queue."""
    return celery_app.send_task(
        "worker.tasks.planner.plan_workflow",
        args=[run_id, prompt, hints or {}],
        queue="planning",
    )
