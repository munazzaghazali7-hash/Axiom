"""
SQLAlchemy ORM models — maps directly to the data model in architecture.md §3.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class WorkflowRunModel(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    plan_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    result_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # relationships
    steps: Mapped[list[RunStepModel]] = relationship(
        "RunStepModel", back_populates="run", cascade="all, delete-orphan"
    )
    results: Mapped[list[ResultModel]] = relationship(
        "ResultModel", back_populates="run", cascade="all, delete-orphan"
    )


class RunStepModel(Base):
    __tablename__ = "run_steps"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False
    )
    step_id: Mapped[str] = mapped_column(String(64), nullable=False)
    step_type: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    output: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    run: Mapped[WorkflowRunModel] = relationship("WorkflowRunModel", back_populates="steps")


class SourceModel(Base):
    __tablename__ = "sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    raw_snapshot_path: Mapped[str] = mapped_column(Text, nullable=False)
    robots_txt_allowed: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    results: Mapped[list[ResultModel]] = relationship("ResultModel", back_populates="source")
    attestation: Mapped[AttestationModel | None] = relationship(
        "AttestationModel", back_populates="source", uselist=False
    )


class AttestationModel(Base):
    __tablename__ = "attestations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    extracted_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    attestation_document: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    signer: Mapped[str] = mapped_column(String(128), default="stub-tee-signer", nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    source: Mapped[SourceModel] = relationship("SourceModel", back_populates="attestation")


class ResultModel(Base):
    __tablename__ = "results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_runs.id", ondelete="CASCADE"), nullable=False
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False
    )
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0", nullable=False)
    structured_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    dedup_group_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    validated: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    run: Mapped[WorkflowRunModel] = relationship("WorkflowRunModel", back_populates="results")
    source: Mapped[SourceModel] = relationship("SourceModel", back_populates="results")
