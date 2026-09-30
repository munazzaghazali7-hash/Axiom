"""
WorkflowPlan — the structured plan emitted by the LLM planner.

The planner ONLY emits a plan (never calls fetch/extract directly).
Every plan must validate against this schema before execution starts.
"""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class StepType(str, Enum):
    search = "search"
    fetch = "fetch"
    extract = "extract"


class ExtractionField(BaseModel):
    """A single field in the extraction schema."""

    name: str = Field(..., description="Field name (snake_case)")
    type: str = Field(
        ...,
        description="JSON-schema type: string | number | integer | boolean | array",
    )
    description: str = Field(..., description="Human-readable description for the LLM extractor")
    required: bool = Field(default=True)
    example: Any = Field(default=None, description="Representative example value")


class ExtractionSchema(BaseModel):
    """Per-source extraction schema — what fields to pull from each page."""

    fields: list[ExtractionField]
    unique_key: str = Field(
        ...,
        description="Field name used for exact-match deduplication (e.g. 'url' or 'id')",
    )

    @model_validator(mode="after")
    def unique_key_exists(self) -> "ExtractionSchema":
        names = {f.name for f in self.fields}
        if self.unique_key not in names:
            raise ValueError(
                f"unique_key '{self.unique_key}' is not in the extraction fields {names}"
            )
        return self


class PlanStep(BaseModel):
    """One step in the workflow plan."""

    step_id: str = Field(..., description="Unique step identifier, e.g. 'step_1'")
    type: StepType
    description: str = Field(..., description="Human-readable description of this step")
    # search-specific
    query: str | None = Field(default=None, description="Search query (for type=search)")
    num_results: int = Field(default=10, ge=1, le=50)
    # fetch-specific
    url: str | None = Field(default=None, description="URL to fetch (for type=fetch)")
    # extract-specific
    source_step_id: str | None = Field(
        default=None,
        description="step_id whose output feeds this extraction step",
    )
    extraction_schema: ExtractionSchema | None = Field(
        default=None,
        description="Schema for structured extraction (required for type=extract)",
    )

    @model_validator(mode="after")
    def validate_step_fields(self) -> "PlanStep":
        if self.type == StepType.search and not self.query:
            raise ValueError("type=search requires a query")
        if self.type == StepType.fetch and not self.url:
            raise ValueError("type=fetch requires a url")
        if self.type == StepType.extract and not self.extraction_schema:
            raise ValueError("type=extract requires an extraction_schema")
        return self


class WorkflowPlan(BaseModel):
    """
    Top-level plan document emitted by the LLM planner.
    Validated before execution starts — invalid plans are rejected and re-prompted.
    """

    version: str = Field(default="1.0", description="Plan schema version")
    title: str = Field(..., description="Short human-readable title for this workflow")
    description: str = Field(..., description="What this workflow collects and why")
    target_sources: list[str] = Field(
        ...,
        description="List of domain/source names the plan will touch",
    )
    output_schema: ExtractionSchema = Field(
        ...,
        description="The final unified schema for all collected records",
    )
    steps: list[PlanStep] = Field(..., min_length=1)
    estimated_records: int | None = Field(
        default=None,
        description="Rough estimate of how many records this plan will yield",
    )

    @model_validator(mode="after")
    def step_ids_unique(self) -> "WorkflowPlan":
        ids = [s.step_id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("step_id values must be unique within a plan")
        return self
