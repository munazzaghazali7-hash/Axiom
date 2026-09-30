"""
Workflow executor — runs each step in the plan: search → fetch → extract.
One Celery task per workflow run.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from worker.celery_app import celery_app
from worker.config import settings

logger = logging.getLogger(__name__)


@celery_app.task(
    name="worker.tasks.executor.execute_workflow",
    bind=True,
    max_retries=1,
)
def execute_workflow(self, run_id: str, plan: dict[str, Any]) -> dict:
    """
    Execute each step in the workflow plan. A single failed source does not
    fail the whole run — errors are logged and the step is marked failed.
    """
    from worker.db import (
        create_run_steps,
        update_run_status,
        update_step_status,
        store_source,
    )
    from worker.tools import search, fetch, extract

    logger.info(f"[executor] Starting execution for run {run_id}, plan: {plan.get('title')}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        loop.run_until_complete(update_run_status(run_id, "running"))

        steps = plan.get("steps", [])
        output_schema = plan.get("output_schema", {})

        # Create step records in DB
        step_ids = loop.run_until_complete(create_run_steps(run_id, steps))

        # step_id → result data (for chaining between steps)
        step_outputs: dict[str, Any] = {}

        # Accumulated raw records for processing
        all_raw_records: list[dict[str, Any]] = []

        for step in steps:
            stype = step["type"]
            sid = step["step_id"]
            db_step_id = step_ids[sid]

            # Check if run was cancelled mid-execution
            from sqlalchemy import text as sql_text
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

            async def _check_cancelled(run_id: str) -> bool:
                from worker.db import _SessionLocal
                from sqlalchemy import text as sql_text
                async with _SessionLocal() as _sess:
                    result = await _sess.execute(
                        sql_text("SELECT status FROM workflow_runs WHERE id = CAST(:id AS UUID)"),
                        {"id": run_id},
                    )
                    row = result.fetchone()
                    return bool(row and row[0] == "cancelled")

            if loop.run_until_complete(_check_cancelled(run_id)):
                logger.info(f"[executor] Run {run_id} was cancelled — stopping execution at step {sid}")
                return {"status": "cancelled", "raw_records": len(all_raw_records)}

            loop.run_until_complete(update_step_status(db_step_id, "running", source_url=step.get("url")))
            logger.info(f"[executor] Step {sid} ({stype}) starting...")

            try:
                if stype == "search":
                    results = search(step["query"], num_results=step.get("num_results", 10))
                    step_outputs[sid] = results
                    loop.run_until_complete(
                        update_step_status(db_step_id, "completed", output={"count": len(results)})
                    )

                elif stype == "fetch":
                    result = fetch(step["url"])
                    if result is None:
                        loop.run_until_complete(
                            update_step_status(db_step_id, "failed", error="Fetch failed or robots.txt blocked")
                        )
                        continue
                    # Save source to DB
                    source_id = loop.run_until_complete(
                        store_source(run_id, result)
                    )
                    step_outputs[sid] = {**result, "source_id": str(source_id)}
                    loop.run_until_complete(
                        update_step_status(db_step_id, "completed", source_url=step["url"], output={"source_id": str(source_id)})
                    )

                elif stype == "extract":
                    source_step_id = step.get("source_step_id")
                    extraction_schema = step.get("extraction_schema") or output_schema
                    source_data = step_outputs.get(source_step_id, {})

                    # Source data may be search results (list) or single fetch result
                    if isinstance(source_data, list):
                        # Extract from each search result URL
                        for search_result in source_data[:5]:  # cap at 5 fetches per search
                            url = search_result.get("url", "")
                            if not url:
                                continue
                            fetched = fetch(url)
                            if fetched:
                                source_id = loop.run_until_complete(
                                    store_source(run_id, fetched)
                                )
                                records = extract(fetched["content"], url, extraction_schema)
                                for rec in records:
                                    all_raw_records.append({
                                        "data": rec,
                                        "source_id": str(source_id),
                                        "source_content": fetched["content"],
                                        "source_content_hash": fetched["content_hash"],
                                    })
                            else:
                                # Fallback to search snippet as source if direct fetch is blocked
                                snippet_content = f"Title: {search_result.get('title', '')}\nSnippet: {search_result.get('content', '')}\nURL: {url}"
                                snippet_hash = hashlib.sha256(snippet_content.encode()).hexdigest()
                                dummy_source = {
                                    "url": url,
                                    "fetched_at": datetime.now(timezone.utc),
                                    "content_hash": snippet_hash,
                                    "snapshot_path": "search_snippet",
                                    "robots_txt_allowed": True,
                                }
                                source_id = loop.run_until_complete(store_source(run_id, dummy_source))
                                records = extract(snippet_content, url, extraction_schema)
                                for rec in records:
                                    all_raw_records.append({
                                        "data": rec,
                                        "source_id": str(source_id),
                                        "source_content": snippet_content,
                                        "source_content_hash": snippet_hash,
                                    })
                    else:
                        # Extract from a previously fetched page
                        url = source_data.get("url", "")
                        content = source_data.get("content", "")
                        source_id = source_data.get("source_id")
                        records = extract(content, url, extraction_schema)
                        for rec in records:
                            all_raw_records.append({
                                "data": rec,
                                "source_id": source_id,
                                "source_content": content,
                                "source_content_hash": source_data.get("content_hash", ""),
                            })

                    loop.run_until_complete(
                        update_step_status(db_step_id, "completed", output={"records_found": len(all_raw_records)})
                    )

            except Exception as step_err:
                logger.error(f"[executor] Step {sid} failed: {step_err}")
                loop.run_until_complete(
                    update_step_status(db_step_id, "failed", error=str(step_err))
                )
                # Single step failure does not fail the whole run

        logger.info(f"[executor] Collected {len(all_raw_records)} raw records for run {run_id}")

        # Kick off processing
        from worker.tasks.processor import process_results
        process_results.delay(run_id, all_raw_records, output_schema)

        return {"status": "executed", "raw_records": len(all_raw_records)}

    except Exception as e:
        logger.error(f"[executor] Fatal error for run {run_id}: {e}")
        loop.run_until_complete(update_run_status(run_id, "failed", error=str(e)))
        raise

    finally:
        loop.close()
