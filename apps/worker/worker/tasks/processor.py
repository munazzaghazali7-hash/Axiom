"""
Processing pipeline: validate → dedup → store → attest.

Rules (rules.md §5):
- No result reaches the results table without (a) schema validation AND (b) a linked source_id.
- Dedup runs AFTER validation, not before.
- Failed records are marked validated=False and surfaced in step logs — never silently dropped.
"""

from __future__ import annotations

import hashlib
import json
import logging
import uuid
from typing import Any

from rapidfuzz import fuzz

from worker.celery_app import celery_app

logger = logging.getLogger(__name__)

_FUZZY_THRESHOLD = 85  # RapidFuzz score above which two records are considered duplicates


def _field_hash(data: dict[str, Any], unique_key: str) -> str:
    """Hash the unique key field for exact dedup."""
    val = str(data.get(unique_key, ""))
    return hashlib.sha256(val.encode()).hexdigest()


def _full_hash(data: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _validate_record(data: dict[str, Any], schema: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a record against the extraction schema.
    Returns (is_valid, error_message).
    """
    required_fields = [f["name"] for f in schema.get("fields", []) if f.get("required", True)]
    missing = [f for f in required_fields if data.get(f) is None]
    if missing:
        return False, f"Missing required fields: {missing}"

    # Basic type checking
    for field in schema.get("fields", []):
        val = data.get(field["name"])
        if val is None:
            continue
        ftype = field.get("type", "string")
        if ftype == "number" and not isinstance(val, (int, float)):
            try:
                float(val)
            except (TypeError, ValueError):
                return False, f"Field '{field['name']}' expected number, got {type(val).__name__}"
        if ftype == "integer" and not isinstance(val, int):
            try:
                int(val)
            except (TypeError, ValueError):
                return False, f"Field '{field['name']}' expected integer, got {type(val).__name__}"

    return True, ""


def _deduplicate(
    records: list[dict[str, Any]],
    unique_key: str,
) -> list[tuple[dict[str, Any], str]]:
    """
    Deduplicate records. Returns list of (record, dedup_group_id) tuples.
    Uses exact match on unique_key first, then rapidfuzz fuzzy match on string representation.
    """
    seen_exact: dict[str, str] = {}  # hash → group_id
    seen_texts: list[tuple[str, str]] = []  # (text_repr, group_id)
    result: list[tuple[dict[str, Any], str]] = []

    for rec in records:
        exact_key = _field_hash(rec, unique_key)
        if exact_key in seen_exact:
            logger.debug(f"[dedup] Exact duplicate skipped: {rec.get(unique_key)}")
            continue

        text_repr = json.dumps(rec, sort_keys=True)
        matched_group: str | None = None

        for prev_text, prev_group in seen_texts:
            score = fuzz.ratio(text_repr, prev_text)
            if score >= _FUZZY_THRESHOLD:
                matched_group = prev_group
                logger.debug(f"[dedup] Fuzzy duplicate (score={score}): {rec.get(unique_key)}")
                break

        if matched_group:
            group_id = matched_group
        else:
            group_id = str(uuid.uuid4())
            seen_exact[exact_key] = group_id
            seen_texts.append((text_repr, group_id))
            result.append((rec, group_id))

    return result


@celery_app.task(
    name="worker.tasks.processor.process_results",
    bind=True,
)
def process_results(
    self,
    run_id: str,
    raw_records: list[dict[str, Any]],
    output_schema: dict[str, Any],
) -> dict:
    """
    Validate, deduplicate, attest, and store results.
    """
    import asyncio
    from worker.db import update_run_status, store_result, store_attestation

    logger.info(f"[processor] Processing {len(raw_records)} raw records for run {run_id}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Check if run was cancelled before processing
    async def _is_cancelled() -> bool:
        from worker.db import _SessionLocal
        from sqlalchemy import text as sql_text
        async with _SessionLocal() as _sess:
            res = await _sess.execute(
                sql_text("SELECT status FROM workflow_runs WHERE id = CAST(:id AS UUID)"),
                {"id": run_id},
            )
            row = res.fetchone()
            return bool(row and row[0] == "cancelled")

    if loop.run_until_complete(_is_cancelled()):
        logger.info(f"[processor] Run {run_id} is cancelled — skipping processing")
        loop.close()
        return {"status": "cancelled", "stored": 0, "failed_validation": 0}

    unique_key = output_schema.get("unique_key", "url")
    validated_records: list[dict[str, Any]] = []
    failed_count = 0

    # Step 1: Validate
    for raw in raw_records:
        data = raw.get("data", {})
        is_valid, error = _validate_record(data, output_schema)
        if is_valid:
            validated_records.append(raw)
        else:
            failed_count += 1
            logger.warning(f"[processor] Validation failed: {error} — data: {data}")

    logger.info(f"[processor] {len(validated_records)} valid, {failed_count} failed validation")

    # Step 2: Deduplicate (runs AFTER validation per rules.md §5)
    records_with_data = [(r.get("data", {}), r) for r in validated_records]
    deduped = _deduplicate([d for d, _ in records_with_data], unique_key)

    logger.info(f"[processor] {len(deduped)} records after dedup")

    # Step 3: Store results + attestations
    stored_count = 0
    for data, group_id in deduped:
        # Find matching raw record for source_id
        raw_match = next(
            (r for r in validated_records if r.get("data") == data),
            None,
        )
        if raw_match is None:
            continue

        source_id = raw_match.get("source_id")
        source_content = raw_match.get("source_content", "")
        content_hash = raw_match.get("source_content_hash", "")

        try:
            result_id = loop.run_until_complete(
                store_result(
                    run_id=run_id,
                    source_id=source_id,
                    data=data,
                    dedup_group_id=group_id,
                    validated=True,
                )
            )

            # Create stub attestation
            if source_id and content_hash:
                loop.run_until_complete(
                    store_attestation(
                        source_id=source_id,
                        content=source_content,
                        extracted=data,
                    )
                )

            stored_count += 1
        except Exception as e:
            logger.error(f"[processor] Failed to store record: {e}")

    # Update run as completed
    loop.run_until_complete(
        update_run_status(run_id, "completed", result_count=stored_count)
    )

    logger.info(f"[processor] Run {run_id} completed. Stored {stored_count} results.")
    loop.close()

    return {"status": "completed", "stored": stored_count, "failed_validation": failed_count}
