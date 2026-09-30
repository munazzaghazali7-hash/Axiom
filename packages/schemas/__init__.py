"""
packages/schemas — shared Pydantic v2 models.
Import from here in both apps/api and apps/worker.
"""

from .workflow_plan import (
    WorkflowPlan,
    PlanStep,
    ExtractionSchema,
    ExtractionField,
    StepType,
)
from .result import (
    ResultRecord,
    Source,
    Attestation,
    RunStatus,
    StepStatus,
    WorkflowRun,
    RunStep,
)

__all__ = [
    # Plan
    "WorkflowPlan",
    "PlanStep",
    "ExtractionSchema",
    "ExtractionField",
    "StepType",
    # Result
    "ResultRecord",
    "Source",
    "Attestation",
    "RunStatus",
    "StepStatus",
    "WorkflowRun",
    "RunStep",
]
