"""
API route schemas (request/response bodies).
Separate from ORM models — avoids tight coupling between DB layer and API contract.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


# ── Tasks (workflow runs) ──────────────────────────────────────────────────────

class SubmitTaskRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=2000, description="Natural-language data request")
    hints: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured hints: target_fields, source_constraints, max_results, etc.",
    )


class StepOut(BaseModel):
    id: uuid.UUID
    step_id: str
    step_type: str
    description: str
    status: str
    source_url: str | None
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {"from_attributes": True}


class TaskOut(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    result_count: int
    created_at: datetime
    completed_at: datetime | None
    error_message: str | None
    plan: dict[str, Any] | None = None
    steps: list[StepOut] = []

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):  # type: ignore[override]
        """Map plan_json ORM column → plan field before validation."""
        if hasattr(obj, "plan_json") and not hasattr(obj, "plan"):
            # SQLAlchemy ORM object — safely inspect steps without triggering async lazy-load
            from sqlalchemy import inspect
            from sqlalchemy.orm.base import NO_VALUE

            steps = []
            try:
                insp = inspect(obj)
                if insp is not None and "steps" in insp.attrs and insp.attrs.steps.loaded_value is not NO_VALUE:
                    steps = obj.steps
            except Exception:
                steps = []

            data = {
                "id": obj.id,
                "prompt": obj.prompt,
                "status": obj.status,
                "result_count": obj.result_count,
                "created_at": obj.created_at,
                "completed_at": obj.completed_at,
                "error_message": obj.error_message,
                "plan": obj.plan_json,
                "steps": steps,
            }
            return super().model_validate(data, *args, **kwargs)
        return super().model_validate(obj, *args, **kwargs)


class TaskListItem(BaseModel):
    id: uuid.UUID
    prompt: str
    status: str
    result_count: int
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


# ── Results ────────────────────────────────────────────────────────────────────

class AttestationOut(BaseModel):
    id: uuid.UUID
    content_hash: str
    extracted_hash: str
    signer: str
    verified: bool
    attestation_document: dict[str, Any]

    model_config = {"from_attributes": True}


class SourceOut(BaseModel):
    id: uuid.UUID
    url: str
    fetched_at: datetime
    content_hash: str
    robots_txt_allowed: bool
    attestation: AttestationOut | None = None

    model_config = {"from_attributes": True}


class ResultOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    source_id: uuid.UUID
    schema_version: str
    structured_data: dict[str, Any]
    validated: bool
    dedup_group_id: str | None

    model_config = {"from_attributes": True}


class ResultsPage(BaseModel):
    items: list[ResultOut]
    total: int
    page: int
    page_size: int


class ResultWithSourceOut(ResultOut):
    source: SourceOut | None = None


# ── Export ─────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    format: str = Field(default="csv", pattern="^(csv|json)$")
