"""
Shared async DB helpers used by Celery tasks.
Workers use sync Celery tasks but run async SQLAlchemy in a dedicated event loop.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from worker.config import settings

_engine = create_async_engine(settings.database_url, echo=False, poolclass=NullPool)
_SessionLocal = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


async def _get_session() -> AsyncSession:
    return _SessionLocal()


# ── Run status helpers ─────────────────────────────────────────────────────────

async def update_run_status(
    run_id: str,
    status: str,
    error: str | None = None,
    result_count: int | None = None,
) -> None:
    from sqlalchemy import text
    async with _SessionLocal() as session:
        values: dict[str, Any] = {"status": status}
        if error:
            values["error_message"] = error
        if result_count is not None:
            values["result_count"] = result_count
        if status in ("completed", "failed", "cancelled"):
            values["completed_at"] = datetime.now(timezone.utc)

        set_clause = ", ".join(f"{k} = :{k}" for k in values)
        values["run_id"] = run_id
        condition = "WHERE id = CAST(:run_id AS UUID)"
        if status != "cancelled":
            condition += " AND status != 'cancelled'"
        await session.execute(
            text(f"UPDATE workflow_runs SET {set_clause} {condition}"),
            values,
        )
        await session.commit()


async def store_plan(run_id: str, plan: dict[str, Any]) -> None:
    from sqlalchemy import text
    async with _SessionLocal() as session:
        await session.execute(
            text("UPDATE workflow_runs SET plan_json = CAST(:plan AS JSONB), status = 'planning' WHERE id = CAST(:run_id AS UUID)"),
            {"plan": json.dumps(plan), "run_id": run_id},
        )
        await session.commit()


# ── Step helpers ───────────────────────────────────────────────────────────────

async def create_run_steps(run_id: str, steps: list[dict[str, Any]]) -> dict[str, str]:
    """Create RunStep records for each plan step. Returns {step_id: db_uuid}."""
    from sqlalchemy import text

    step_ids: dict[str, str] = {}
    async with _SessionLocal() as session:
        for step in steps:
            db_id = str(uuid.uuid4())
            step_ids[step["step_id"]] = db_id
            await session.execute(
                text("""
                    INSERT INTO run_steps (id, run_id, step_id, step_type, description, input, output, status)
                    VALUES (CAST(:id AS UUID), CAST(:run_id AS UUID), :step_id, :step_type, :description, CAST(:input AS JSONB), CAST(:output AS JSONB), 'pending')
                """),
                {
                    "id": db_id,
                    "run_id": run_id,
                    "step_id": step["step_id"],
                    "step_type": step["type"],
                    "description": step.get("description", ""),
                    "input": json.dumps({k: v for k, v in step.items() if k not in ("type", "step_id", "description")}),
                    "output": "{}",
                },
            )
        await session.commit()
    return step_ids


async def update_step_status(
    db_step_id: str,
    status: str,
    source_url: str | None = None,
    output: dict | None = None,
    error: str | None = None,
) -> None:
    from sqlalchemy import text
    async with _SessionLocal() as session:
        values: dict[str, Any] = {"status": status, "id": db_step_id}
        if source_url:
            values["source_url"] = source_url
        if output:
            values["output"] = json.dumps(output)
        if error:
            values["error_message"] = error
        if status == "running":
            values["started_at"] = datetime.now(timezone.utc)
        if status in ("completed", "failed", "skipped"):
            values["finished_at"] = datetime.now(timezone.utc)

        set_clause = ", ".join(
            f"{k} = CAST(:{k} AS JSONB)" if k == "output" else f"{k} = :{k}"
            for k in values if k != "id"
        )
        await session.execute(
            text(f"UPDATE run_steps SET {set_clause} WHERE id = CAST(:id AS UUID)"),
            values,
        )
        await session.commit()


# ── Source / result / attestation helpers ─────────────────────────────────────

async def store_source(run_id: str, fetch_result: dict[str, Any]) -> str:
    from sqlalchemy import text
    source_id = str(uuid.uuid4())
    fetched_at = fetch_result.get("fetched_at")
    if isinstance(fetched_at, str):
        try:
            fetched_at = datetime.fromisoformat(fetched_at)
        except Exception:
            fetched_at = datetime.now(timezone.utc)
    elif not isinstance(fetched_at, datetime):
        fetched_at = datetime.now(timezone.utc)

    async with _SessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO sources (id, url, fetched_at, content_hash, raw_snapshot_path, robots_txt_allowed)
                VALUES (CAST(:id AS UUID), :url, :fetched_at, :content_hash, :snapshot_path, :robots_ok)
                ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": source_id,
                "url": fetch_result["url"],
                "fetched_at": fetched_at,
                "content_hash": fetch_result["content_hash"],
                "snapshot_path": fetch_result["snapshot_path"],
                "robots_ok": fetch_result.get("robots_txt_allowed", True),
            },
        )
        await session.commit()
    return source_id


async def store_result(
    run_id: str,
    source_id: str,
    data: dict[str, Any],
    dedup_group_id: str,
    validated: bool,
) -> str:
    from sqlalchemy import text
    result_id = str(uuid.uuid4())
    async with _SessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO results (id, run_id, source_id, schema_version, structured_data, dedup_group_id, validated)
                VALUES (CAST(:id AS UUID), CAST(:run_id AS UUID), CAST(:source_id AS UUID), '1.0', CAST(:data AS JSONB), :group_id, :validated)
            """),
            {
                "id": result_id,
                "run_id": run_id,
                "source_id": source_id,
                "data": json.dumps(data),
                "group_id": dedup_group_id,
                "validated": validated,
            },
        )
        await session.commit()
    return result_id


async def store_attestation(
    source_id: str,
    content: str,
    extracted: dict[str, Any],
) -> None:
    from sqlalchemy import text
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../packages"))
    from schemas import Attestation

    att_id = uuid.uuid4()
    att = Attestation.create_stub(
        source_id=uuid.UUID(source_id),
        att_id=att_id,
        content=content,
        extracted=extracted,
    )
    async with _SessionLocal() as session:
        await session.execute(
            text("""
                INSERT INTO attestations (id, source_id, content_hash, extracted_hash, attestation_document, signer, verified)
                VALUES (CAST(:id AS UUID), CAST(:source_id AS UUID), :ch, :eh, CAST(:doc AS JSONB), :signer, :verified)
                ON CONFLICT (source_id) DO NOTHING
            """),
            {
                "id": str(att.id),
                "source_id": source_id,
                "ch": att.content_hash,
                "eh": att.extracted_hash,
                "doc": json.dumps(att.attestation_document),
                "signer": att.signer,
                "verified": True,  # stub signer marks itself as verified; real TEE would check enclave measurement
            },
        )
        await session.commit()


def run_sync_db(coro):
    """Helper to run an async DB coroutine from sync Celery context."""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
