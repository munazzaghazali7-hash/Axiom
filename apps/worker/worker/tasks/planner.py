"""
Workflow Planner — Celery task that sends the user's prompt to Gemini
and returns a validated WorkflowPlan JSON.

Rules (from rules.md §3):
- The planner ONLY emits a plan. It never calls fetch() or extract() directly.
- Every plan must validate against WorkflowPlan before execution starts.
- Extraction prompts must request structured JSON output — never free text.
- Raw planner output is logged alongside the parsed plan.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from worker.celery_app import celery_app
from worker.config import settings
from worker.db import run_sync_db

logger = logging.getLogger(__name__)

PLAN_SYSTEM_PROMPT = """You are a data collection workflow planner. Your ONLY job is to produce a structured JSON plan.
You do NOT fetch URLs, call search APIs, or extract data yourself — you only plan.

Given a natural-language data request, output a JSON object matching this schema exactly:

{
  "version": "1.0",
  "title": "<short workflow title>",
  "description": "<what this workflow collects and why>",
  "target_sources": ["<domain1>", "<domain2>"],
  "output_schema": {
    "fields": [
      {
        "name": "<field_name>",
        "type": "<string|number|integer|boolean>",
        "description": "<description for extractor>",
        "required": true,
        "example": "<example value>"
      }
    ],
    "unique_key": "<field_name used for dedup>"
  },
  "steps": [
    {
      "step_id": "step_1",
      "type": "search",
      "description": "<human-readable description>",
      "query": "<search query>",
      "num_results": 10
    },
    {
      "step_id": "step_2",
      "type": "fetch",
      "description": "<human-readable description>",
      "url": "<url to fetch>"
    },
    {
      "step_id": "step_3",
      "type": "extract",
      "description": "<human-readable description>",
      "source_step_id": "step_1",
      "extraction_schema": {
        "fields": [...],
        "unique_key": "<field>"
      }
    }
  ],
  "estimated_records": 20
}

Rules:
- Use only public, permitted sources (no auth required).
- Always include at least one search step followed by extract steps.
- The output_schema must cover all fields you intend to extract.
- unique_key must be one of the field names in output_schema.fields.
- Respond with ONLY the JSON object — no markdown, no explanation."""


def build_fallback_plan(prompt: str, hints: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Build a deterministic, schema-compliant WorkflowPlan if LLM quota is exhausted
    or service is unreachable (e.g. offline demo mode or free tier 429).
    """
    p_lower = prompt.lower()
    if any(k in p_lower for k in ("job", "hiring", "developer", "engineer", "openings")):
        title = "Job Openings Pipeline"
        description = "Collects verified job listings and position details"
        sources = ["linkedin.com", "naukri.com", "indeed.com"]
        fields = [
            {"name": "title", "type": "string", "description": "Job title", "required": True, "example": "Python Developer"},
            {"name": "company", "type": "string", "description": "Company name", "required": True, "example": "Tech Corp"},
            {"name": "location", "type": "string", "description": "Location or remote status", "required": True, "example": "Bangalore, India"},
            {"name": "salary", "type": "string", "description": "Salary or compensation", "required": False, "example": "₹15-25 LPA"},
            {"name": "url", "type": "string", "description": "Direct application URL", "required": True, "example": "https://example.com/job/1"},
        ]
        unique_key = "url"
    elif any(k in p_lower for k in ("startup", "yc", "founder", "company", "companies")):
        title = "Startup Intelligence Directory"
        description = "Collects startup details, founders, and business summaries"
        sources = ["ycombinator.com", "techcrunch.com", "crunchbase.com"]
        fields = [
            {"name": "name", "type": "string", "description": "Company name", "required": True, "example": "Acme AI"},
            {"name": "description", "type": "string", "description": "What the startup does", "required": True, "example": "AI workflow engine"},
            {"name": "founders", "type": "string", "description": "Founding team members", "required": False, "example": "Jane Doe, John Smith"},
            {"name": "industry", "type": "string", "description": "Market sector", "required": False, "example": "AI / DevTools"},
            {"name": "url", "type": "string", "description": "Website URL", "required": True, "example": "https://example.com"},
        ]
        unique_key = "url"
    elif any(k in p_lower for k in ("conference", "event", "summit", "meetup")):
        title = "Conference & Events Calendar"
        description = "Collects upcoming events, dates, and locations"
        sources = ["eventbrite.com", "meetup.com", "conferences.org"]
        fields = [
            {"name": "name", "type": "string", "description": "Event name", "required": True, "example": "AI Summit 2025"},
            {"name": "location", "type": "string", "description": "City and venue or virtual", "required": True, "example": "San Francisco, CA"},
            {"name": "date", "type": "string", "description": "Event dates", "required": True, "example": "2025-10-15"},
            {"name": "topics", "type": "string", "description": "Key themes", "required": False, "example": "LLMs, Agents"},
            {"name": "url", "type": "string", "description": "Registration URL", "required": True, "example": "https://example.com/summit"},
        ]
        unique_key = "url"
    else:
        title = f"Axiom Pipeline: {prompt[:40]}"
        description = f"Structured data collection for query: {prompt}"
        sources = ["wikipedia.org", "news.ycombinator.com", "google.com"]
        fields = [
            {"name": "title", "type": "string", "description": "Entity or item title", "required": True, "example": "Item Name"},
            {"name": "description", "type": "string", "description": "Summary or details", "required": True, "example": "Brief description"},
            {"name": "source", "type": "string", "description": "Origin domain or source", "required": False, "example": "example.com"},
            {"name": "url", "type": "string", "description": "Source URL", "required": True, "example": "https://example.com/item/1"},
        ]
        unique_key = "url"

    return {
        "version": "1.0",
        "title": title,
        "description": description,
        "target_sources": sources,
        "output_schema": {
            "fields": fields,
            "unique_key": unique_key,
        },
        "steps": [
            {
                "step_id": "step_1",
                "type": "search",
                "description": f"Search public web for: {prompt[:60]}",
                "query": prompt,
                "num_results": 10,
            },
            {
                "step_id": "step_2",
                "type": "extract",
                "description": f"Extract structured records matching {title}",
                "source_step_id": "step_1",
                "extraction_schema": {
                    "fields": fields,
                    "unique_key": unique_key,
                },
            },
        ],
        "estimated_records": 10,
    }


@celery_app.task(
    name="worker.tasks.planner.plan_workflow",
    bind=True,
    max_retries=2,
    default_retry_delay=5,
)
def plan_workflow(self, run_id: str, prompt: str, hints: dict[str, Any] | None = None) -> dict:
    """
    Phase 1: call Gemini → get WorkflowPlan JSON → store on workflow_run → trigger executor.
    Includes automatic fallback planner if LLM quota is exhausted or unreachable.
    """
    import asyncio
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../../packages"))
    from schemas import WorkflowPlan
    from worker.db import update_run_status, store_plan

    logger.info(f"[planner] Starting planning for run {run_id}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Update run status → planning
    loop.run_until_complete(update_run_status(run_id, "planning"))

    try:
        plan: WorkflowPlan | None = None
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=settings.gemini_api_key)

            user_message = prompt
            if hints:
                user_message += f"\n\nAdditional hints: {json.dumps(hints)}"

            from worker.tools import generate_content_with_retry

            response = generate_content_with_retry(
                client=client,
                model=settings.gemini_model,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=PLAN_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                ),
            )

            raw_output = response.text
            logger.info(f"[planner] Raw output for run {run_id}: {raw_output[:500]}...")

            # Strip markdown code fences if Gemini wraps the JSON
            if raw_output.strip().startswith("```"):
                raw_output = raw_output.strip().split("```")[1]
                if raw_output.startswith("json"):
                    raw_output = raw_output[4:]
                raw_output = raw_output.strip()

            plan_data = json.loads(raw_output)
            plan = WorkflowPlan.model_validate(plan_data)
        except Exception as llm_err:
            logger.warning(
                f"[planner] Gemini planning unavailable ({llm_err}). "
                f"Using resilient fallback plan for prompt: '{prompt}'"
            )
            fallback_dict = build_fallback_plan(prompt, hints)
            plan = WorkflowPlan.model_validate(fallback_dict)

        logger.info(f"[planner] Plan validated for run {run_id}: '{plan.title}' ({len(plan.steps)} steps)")

        # Persist plan on workflow_run
        loop.run_until_complete(store_plan(run_id, plan.model_dump()))

        # Kick off executor
        from worker.tasks.executor import execute_workflow
        execute_workflow.delay(run_id, plan.model_dump())

        return {"status": "planned", "plan_title": plan.title, "steps": len(plan.steps)}

    except Exception as e:
        logger.error(f"[planner] Fatal error for run {run_id}: {e}")
        loop.run_until_complete(update_run_status(run_id, "failed", error=str(e)))
        raise

    finally:
        loop.close()
