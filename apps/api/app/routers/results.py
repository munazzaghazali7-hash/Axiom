"""
Results router — GET /tasks/{id}/results, GET /results/{id}/source,
                 GET /datasets, POST /datasets/{id}/export
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import ResultModel, SourceModel, WorkflowRunModel
from app.schemas import (
    ExportRequest,
    ResultOut,
    ResultsPage,
    ResultWithSourceOut,
    SourceOut,
    TaskListItem,
)

router = APIRouter(tags=["results"])


# ── Results for a specific run ─────────────────────────────────────────────────

@router.get("/tasks/{task_id}/results", response_model=ResultsPage)
async def get_task_results(
    task_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None),
) -> ResultsPage:
    """Paginated results for a workflow run. Optionally filter by search term."""
    # Verify run exists
    run = await db.get(WorkflowRunModel, task_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Task not found")

    offset = (page - 1) * page_size
    q = select(ResultModel).where(ResultModel.run_id == task_id)

    # Basic JSONB text search
    if search:
        q = q.where(
            ResultModel.structured_data.cast(type_=None).astext.ilike(f"%{search}%")
        )

    total_result = await db.execute(select(func.count()).select_from(q.subquery()))
    total = total_result.scalar_one()

    items_result = await db.execute(q.offset(offset).limit(page_size))
    items = items_result.scalars().all()

    return ResultsPage(
        items=[ResultOut.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
    )


# ── Source + attestation for one result ───────────────────────────────────────

@router.get("/results/{result_id}/source", response_model=ResultWithSourceOut)
async def get_result_source(
    result_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ResultWithSourceOut:
    """Return a result with its linked source and attestation."""
    result = await db.execute(
        select(ResultModel)
        .where(ResultModel.id == result_id)
        .options(
            selectinload(ResultModel.source).selectinload(SourceModel.attestation)
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=404, detail="Result not found")
    return ResultWithSourceOut.model_validate(record)


# ── Dataset history ────────────────────────────────────────────────────────────

@router.get("/datasets", response_model=list[TaskListItem])
async def list_datasets(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 50,
    offset: int = 0,
) -> list[TaskListItem]:
    """List all past workflow runs (alias for history view)."""
    result = await db.execute(
        select(WorkflowRunModel)
        .where(WorkflowRunModel.status == "completed")
        .order_by(WorkflowRunModel.completed_at.desc())
        .limit(limit)
        .offset(offset)
    )
    runs = result.scalars().all()
    return [TaskListItem.model_validate(r) for r in runs]


# ── Export ─────────────────────────────────────────────────────────────────────

@router.post("/datasets/{task_id}/export")
async def export_dataset(
    task_id: uuid.UUID,
    body: ExportRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreamingResponse:
    """Export all results for a run as CSV or JSON."""
    run = await db.get(WorkflowRunModel, task_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Task not found")

    result = await db.execute(
        select(ResultModel).where(ResultModel.run_id == task_id)
    )
    records = result.scalars().all()

    if body.format == "json":
        data = json.dumps(
            [r.structured_data for r in records], indent=2, default=str
        )
        return StreamingResponse(
            iter([data]),
            media_type="application/json",
            headers={
                "Content-Disposition": f'attachment; filename="run_{task_id}.json"'
            },
        )

    # CSV
    if not records:
        return StreamingResponse(
            iter([""]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f'attachment; filename="run_{task_id}.csv"'
            },
        )

    buf = io.StringIO()
    all_keys: list[str] = list(
        dict.fromkeys(k for r in records for k in r.structured_data.keys())
    )
    writer = csv.DictWriter(buf, fieldnames=all_keys, extrasaction="ignore")
    writer.writeheader()
    for r in records:
        writer.writerow(r.structured_data)

    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="run_{task_id}.csv"'
        },
    )
