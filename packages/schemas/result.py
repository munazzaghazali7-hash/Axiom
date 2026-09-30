"""
Result-side models — ResultRecord, Source, Attestation, and run-tracking models.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class RunStatus(str, Enum):
    pending = "pending"
    planning = "planning"
    running = "running"
    completed = "completed"
    failed = "failed"
    cancelled = "cancelled"


class StepStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"
    skipped = "skipped"


class Source(BaseModel):
    """A single fetched web source, stored before extraction runs."""

    id: UUID
    url: str
    fetched_at: datetime
    content_hash: str  # SHA-256 of raw HTML
    raw_snapshot_path: str  # path/key in object storage
    robots_txt_allowed: bool = True


class Attestation(BaseModel):
    """
    TEE attestation document tying source content to extracted record.
    Stubbed for hackathon — architecture and UI treatment stay correct.
    """

    id: UUID
    source_id: UUID
    content_hash: str  # SHA-256 of raw fetched content
    extracted_hash: str  # SHA-256 of extracted structured record
    attestation_document: dict[str, Any] = Field(
        default_factory=dict,
        description="Signed attestation (stub: contains signer=stub-tee-signer)",
    )
    signer: str = Field(default="stub-tee-signer")
    verified: bool = Field(default=False)

    @classmethod
    def create_stub(
        cls,
        source_id: UUID,
        att_id: UUID,
        content: str,
        extracted: dict[str, Any],
    ) -> "Attestation":
        """Create a deterministic stub attestation for demo purposes."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        extracted_str = json.dumps(extracted, sort_keys=True)
        extracted_hash = hashlib.sha256(extracted_str.encode()).hexdigest()
        return cls(
            id=att_id,
            source_id=source_id,
            content_hash=content_hash,
            extracted_hash=extracted_hash,
            attestation_document={
                "version": "stub-1.0",
                "signer": "stub-tee-signer",
                "note": "TEE-ready stub — replace with Nitro Enclave attestation",
                "content_hash": content_hash,
                "extracted_hash": extracted_hash,
            },
            signer="stub-tee-signer",
            verified=True,  # stub always passes
        )


class ResultRecord(BaseModel):
    """A single validated, structured result in the results table."""

    id: UUID
    run_id: UUID
    schema_version: str = "1.0"
    structured_data: dict[str, Any]
    source_id: UUID
    dedup_group_id: str | None = None
    validated: bool = True

    @computed_field
    @property
    def data_hash(self) -> str:
        """SHA-256 of the structured data for dedup."""
        return hashlib.sha256(
            json.dumps(self.structured_data, sort_keys=True).encode()
        ).hexdigest()


class RunStep(BaseModel):
    """Represents one step in an executing workflow run."""

    id: UUID
    run_id: UUID
    step_id: str  # matches PlanStep.step_id
    step_type: str  # search | fetch | extract
    description: str
    input: dict[str, Any] = Field(default_factory=dict)
    output: dict[str, Any] = Field(default_factory=dict)
    source_url: str | None = None
    status: StepStatus = StepStatus.pending
    error_message: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None


class WorkflowRun(BaseModel):
    """Top-level workflow run record."""

    id: UUID
    prompt: str
    plan_json: dict[str, Any] | None = None
    status: RunStatus = RunStatus.pending
    created_at: datetime
    completed_at: datetime | None = None
    error_message: str | None = None
    result_count: int = 0
    steps: list[RunStep] = Field(default_factory=list)
