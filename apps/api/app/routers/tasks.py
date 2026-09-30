"""
Task router — POST /tasks, GET /tasks, GET /tasks/{id}, DELETE /tasks/{id}/cancel
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import WorkflowRunModel
from app.schemas import SubmitTaskRequest, TaskOut, TaskListItem

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
async def submit_task(
    body: SubmitTaskRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskOut:
    """Submit a natural-language prompt → creates a workflow_run and kicks off planning."""
    from app.worker import enqueue_plan_workflow  # deferred to avoid circular import

    run = WorkflowRunModel(
        id=uuid.uuid4(),
        prompt=body.prompt,
        status="pending",
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Kick off async Celery task
    enqueue_plan_workflow(str(run.id), body.prompt, body.hints)

    return TaskOut.model_validate(run)


@router.get("", response_model=list[TaskListItem])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[TaskListItem]:
    """List all workflow runs, newest first."""
    result = await db.execute(
        select(WorkflowRunModel)
        .order_by(WorkflowRunModel.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    runs = result.scalars().all()
    return [TaskListItem.model_validate(r) for r in runs]


@router.get("/{task_id}", response_model=TaskOut)
async def get_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskOut:
    """Get full task detail including step-by-step progress."""
    result = await db.execute(
        select(WorkflowRunModel)
        .where(WorkflowRunModel.id == task_id)
        .options(selectinload(WorkflowRunModel.steps))
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(run)


@router.post("/{task_id}/cancel", response_model=TaskOut)
async def cancel_task(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TaskOut:
    """Cancel a running or pending workflow and revoke its Celery task."""
    result = await db.execute(
        select(WorkflowRunModel).where(WorkflowRunModel.id == task_id)
    )
    run = result.scalar_one_or_none()
    if run is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if run.status not in ("pending", "planning", "running"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel a task in '{run.status}' state",
        )
    run.status = "cancelled"
    from datetime import datetime, timezone
    run.completed_at = datetime.now(timezone.utc)
    await db.flush()

    # Revoke the Celery task so the worker stops if it hasn't started yet.
    # The executor also checks the DB status mid-run and will stop on next step boundary.
    try:
        from app.worker import celery_app
        # Revoke by task name pattern — terminates any queued task for this run
        celery_app.control.revoke(str(task_id), terminate=True, signal="SIGTERM")
    except Exception:
        pass  # Revocation is best-effort; DB status is the source of truth

    return TaskOut.model_validate(run)
