"""
Demo seeder — inserts 3 pre-completed workflow runs with realistic results
so judges see a populated history page immediately on launch.

Usage:
    cd apps/worker
    python seed_demo.py

Requires: DATABASE_URL in .env (Postgres must be running).
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from worker.config import settings

_engine = create_async_engine(settings.database_url, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

# ── Seed data ──────────────────────────────────────────────────────────────────

DEMO_RUNS = [
    {
        "prompt": "Find 20 Python developer job openings in Bangalore",
        "title": "Python Jobs — Bangalore",
        "description": "Collects Python developer job listings from major Indian job boards",
        "target_sources": ["linkedin.com", "naukri.com", "indeed.co.in"],
        "minutes_ago": 45,
        "results": [
            {"title": "Senior Python Developer", "company": "Flipkart", "location": "Bangalore, Karnataka", "experience": "3-5 years", "salary": "₹18-25 LPA", "url": "https://linkedin.com/jobs/view/1001", "posted_date": "2026-09-22"},
            {"title": "Python Backend Engineer", "company": "Swiggy", "location": "Bangalore, Karnataka", "experience": "2-4 years", "salary": "₹15-22 LPA", "url": "https://linkedin.com/jobs/view/1002", "posted_date": "2026-09-22"},
            {"title": "ML Platform Engineer (Python)", "company": "Meesho", "location": "Bangalore, Karnataka", "experience": "4-7 years", "salary": "₹25-40 LPA", "url": "https://naukri.com/job/1003", "posted_date": "2026-09-21"},
            {"title": "Python Developer — Fintech", "company": "Razorpay", "location": "Bangalore, Karnataka", "experience": "2-5 years", "salary": "₹20-30 LPA", "url": "https://naukri.com/job/1004", "posted_date": "2026-09-21"},
            {"title": "Django/FastAPI Engineer", "company": "Groww", "location": "Bangalore, Karnataka", "experience": "3-6 years", "salary": "₹22-35 LPA", "url": "https://linkedin.com/jobs/view/1005", "posted_date": "2026-09-20"},
            {"title": "Python Data Engineer", "company": "Zepto", "location": "Bangalore, Karnataka", "experience": "2-4 years", "salary": "₹18-28 LPA", "url": "https://indeed.co.in/job/1006", "posted_date": "2026-09-20"},
            {"title": "Backend Python Developer", "company": "PhonePe", "location": "Bangalore, Karnataka", "experience": "3-5 years", "salary": "₹20-32 LPA", "url": "https://linkedin.com/jobs/view/1007", "posted_date": "2026-09-19"},
            {"title": "Senior Software Engineer — Python", "company": "Ola", "location": "Bangalore, Karnataka", "experience": "4-8 years", "salary": "₹28-45 LPA", "url": "https://naukri.com/job/1008", "posted_date": "2026-09-19"},
        ],
        "unique_key": "url",
    },
    {
        "prompt": "Collect YC W24 startup names, descriptions, and founders",
        "title": "YC W24 Startup Directory",
        "description": "Structured directory of Y Combinator Winter 2024 batch startups",
        "target_sources": ["ycombinator.com", "linkedin.com"],
        "minutes_ago": 120,
        "results": [
            {"name": "Orum", "description": "AI-powered live voice agent for sales teams", "founders": "Talmage Egan, Jason Dorfman", "industry": "Sales AI", "url": "https://ycombinator.com/companies/orum", "batch": "W24"},
            {"name": "Decagon", "description": "AI customer support agents that handle complex queries end-to-end", "founders": "Jesse Zhang, Ashwin Sreenivas", "industry": "Customer Support AI", "url": "https://ycombinator.com/companies/decagon", "batch": "W24"},
            {"name": "Apex", "description": "AI coding assistant for enterprise security teams", "founders": "David Park, Kevin Wang", "industry": "DevSecOps", "url": "https://ycombinator.com/companies/apex", "batch": "W24"},
            {"name": "Lutra", "description": "No-code AI workflow automation using natural language", "founders": "Mike Chen, Sarah Kim", "industry": "Workflow Automation", "url": "https://ycombinator.com/companies/lutra", "batch": "W24"},
            {"name": "Dosu", "description": "AI agent that triages and responds to GitHub issues automatically", "founders": "Anirudh Patil, Nikhil Benesch", "industry": "Developer Tools", "url": "https://ycombinator.com/companies/dosu", "batch": "W24"},
            {"name": "Speakeasy", "description": "SDK generation from OpenAPI specs with AI-generated documentation", "founders": "Sagar Batchu, Nolan Di Mare Sullivan", "industry": "Developer Tools", "url": "https://ycombinator.com/companies/speakeasy", "batch": "W24"},
        ],
        "unique_key": "url",
    },
    {
        "prompt": "List AI/ML conferences happening in 2025 with dates and locations",
        "title": "AI/ML Conference Calendar 2025",
        "description": "Comprehensive calendar of major AI and ML conferences for 2025",
        "target_sources": ["aiconferences.com", "machinelearning.org", "neurips.cc"],
        "minutes_ago": 240,
        "results": [
            {"name": "NeurIPS 2025", "location": "San Diego, USA", "date_start": "2025-12-07", "date_end": "2025-12-13", "topics": "Deep learning, reinforcement learning, generative AI", "submission_deadline": "2025-05-15", "url": "https://neurips.cc/2025"},
            {"name": "ICML 2025", "location": "Vancouver, Canada", "date_start": "2025-07-13", "date_end": "2025-07-19", "topics": "Machine learning theory, applications, optimization", "submission_deadline": "2025-01-31", "url": "https://icml.cc/2025"},
            {"name": "ICLR 2025", "location": "Singapore", "date_start": "2025-04-24", "date_end": "2025-04-28", "topics": "Representation learning, LLMs, multimodal AI", "submission_deadline": "2024-10-01", "url": "https://iclr.cc/2025"},
            {"name": "CVPR 2025", "location": "Nashville, USA", "date_start": "2025-06-11", "date_end": "2025-06-15", "topics": "Computer vision, image generation, 3D AI", "submission_deadline": "2024-11-15", "url": "https://cvpr.thecvf.com/2025"},
            {"name": "ACL 2025", "location": "Vienna, Austria", "date_start": "2025-07-27", "date_end": "2025-08-01", "topics": "NLP, LLMs, computational linguistics", "submission_deadline": "2025-02-15", "url": "https://acl2025.org"},
            {"name": "EMNLP 2025", "location": "Tokyo, Japan", "date_start": "2025-11-05", "date_end": "2025-11-09", "topics": "Empirical NLP, information extraction, MT", "submission_deadline": "2025-06-01", "url": "https://emnlp2025.org"},
            {"name": "KDD 2025", "location": "Toronto, Canada", "date_start": "2025-08-03", "date_end": "2025-08-07", "topics": "Data mining, knowledge discovery, applied AI", "submission_deadline": "2025-02-01", "url": "https://kdd.org/kdd2025"},
        ],
        "unique_key": "url",
    },
]


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


async def seed():
    async with _Session() as session:
        # Ensure tables exist
        await session.execute(text("SELECT 1"))  # basic connectivity check

        for demo in DEMO_RUNS:
            run_id = str(uuid.uuid4())
            source_id = str(uuid.uuid4())
            att_id = str(uuid.uuid4())
            now = datetime.now(timezone.utc)
            created_at = now - timedelta(minutes=demo["minutes_ago"] + 5)
            completed_at = now - timedelta(minutes=demo["minutes_ago"])
            result_count = len(demo["results"])

            plan = {
                "version": "1.0",
                "title": demo["title"],
                "description": demo["description"],
                "target_sources": demo["target_sources"],
                "output_schema": {
                    "fields": [
                        {"name": k, "type": "string", "description": k, "required": True}
                        for k in demo["results"][0].keys()
                    ],
                    "unique_key": demo["unique_key"],
                },
                "steps": [
                    {"step_id": "step_1", "type": "search", "description": "Web search", "query": demo["prompt"], "num_results": 10},
                    {"step_id": "step_2", "type": "extract", "description": "Extract structured data", "source_step_id": "step_1", "extraction_schema": {"fields": [], "unique_key": demo["unique_key"]}},
                ],
                "estimated_records": result_count,
            }

            # Insert workflow_run
            await session.execute(
                text("""
                    INSERT INTO workflow_runs (id, prompt, plan_json, status, result_count, created_at, completed_at)
                    VALUES (CAST(:id AS UUID), :prompt, CAST(:plan AS JSONB), 'completed', :count, :created_at, :completed_at)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": run_id,
                    "prompt": demo["prompt"],
                    "plan": json.dumps(plan),
                    "count": result_count,
                    "created_at": created_at,
                    "completed_at": completed_at,
                },
            )

            # Insert a fake source
            fake_content = f"<html><body>Demo seed data for: {demo['title']}</body></html>"
            content_hash = _sha256(fake_content)
            snapshot_path = f"./data/snapshots/{content_hash}.html"

            await session.execute(
                text("""
                    INSERT INTO sources (id, url, fetched_at, content_hash, raw_snapshot_path, robots_txt_allowed)
                    VALUES (CAST(:id AS UUID), :url, :fetched_at, :ch, :snap, true)
                    ON CONFLICT DO NOTHING
                """),
                {
                    "id": source_id,
                    "url": f"https://{demo['target_sources'][0]}/",
                    "fetched_at": created_at,
                    "ch": content_hash,
                    "snap": snapshot_path,
                },
            )

            # Insert stub attestation
            extracted_str = json.dumps(demo["results"], sort_keys=True)
            extracted_hash = _sha256(extracted_str)
            att_doc = {
                "version": "stub-1.0",
                "signer": "stub-tee-signer",
                "note": "TEE-ready stub — seeded for demo",
                "content_hash": content_hash,
                "extracted_hash": extracted_hash,
            }

            await session.execute(
                text("""
                    INSERT INTO attestations (id, source_id, content_hash, extracted_hash, attestation_document, signer, verified)
                    VALUES (CAST(:id AS UUID), CAST(:sid AS UUID), :ch, :eh, CAST(:doc AS JSONB), 'stub-tee-signer', true)
                    ON CONFLICT (source_id) DO NOTHING
                """),
                {
                    "id": att_id,
                    "sid": source_id,
                    "ch": content_hash,
                    "eh": extracted_hash,
                    "doc": json.dumps(att_doc),
                },
            )

            # Insert results
            for rec in demo["results"]:
                result_id = str(uuid.uuid4())
                group_id = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO results (id, run_id, source_id, schema_version, structured_data, dedup_group_id, validated)
                        VALUES (CAST(:id AS UUID), CAST(:run_id AS UUID), CAST(:src_id AS UUID), '1.0', CAST(:data AS JSONB), :group_id, true)
                    """),
                    {
                        "id": result_id,
                        "run_id": run_id,
                        "src_id": source_id,
                        "data": json.dumps(rec),
                        "group_id": group_id,
                    },
                )

            # Insert two demo run_steps (search + extract)
            for i, (step_id, stype, desc) in enumerate([
                ("step_1", "search", f"Search: {demo['prompt']}"),
                ("step_2", "extract", f"Extract structured records"),
            ]):
                sid = str(uuid.uuid4())
                await session.execute(
                    text("""
                        INSERT INTO run_steps (id, run_id, step_id, step_type, description, input, output, status, started_at, finished_at)
                        VALUES (CAST(:id AS UUID), CAST(:run_id AS UUID), :step_id, :stype, :desc, '{}', CAST(:output AS JSONB), 'completed', :started, :finished)
                        ON CONFLICT DO NOTHING
                    """),
                    {
                        "id": sid,
                        "run_id": run_id,
                        "step_id": step_id,
                        "stype": stype,
                        "desc": desc,
                        "output": json.dumps({"count": result_count if stype == "extract" else 10}),
                        "started": created_at + timedelta(seconds=i * 30),
                        "finished": created_at + timedelta(seconds=(i + 1) * 30),
                    },
                )

            await session.commit()
            print(f"✅ Seeded: '{demo['title']}' — {result_count} results")

    await _engine.dispose()


if __name__ == "__main__":
    print("🌱 Seeding demo data...\n")
    asyncio.run(seed())
    print("\n✅ Done! Refresh /history to see the seeded workflows.")
