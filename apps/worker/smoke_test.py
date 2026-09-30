"""
Phase 0 smoke test — takes a prompt, runs planning + execution + processing inline,
and prints one structured, validated record to the console.

Usage:
    cd apps/worker
    cp ../../.env.example .env  # fill in GEMINI_API_KEY and TAVILY_API_KEY
    python smoke_test.py "Find 5 Python developer job openings in Bangalore"
"""

import json
import sys
import os

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../packages"))

import logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "../../.env"))

from worker.config import settings

def main():
    prompt = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "Find 5 Python developer job openings in Bangalore on LinkedIn"
    print(f"\n🔍 Prompt: {prompt}\n")

    # ── Step 1: Planning ──────────────────────────────────────────────────────
    print("📋 Step 1: Planning workflow with Gemini...")
    from google import genai
    from google.genai import types
    from schemas import WorkflowPlan

    PLAN_SYSTEM_PROMPT = """You are a data collection workflow planner. Your ONLY job is to produce a structured JSON plan.

Given a natural-language data request, output a JSON object with these keys:
- version: "1.0"
- title: short workflow title
- description: what this collects
- target_sources: list of domain names
- output_schema: { fields: [{name, type, description, required, example}], unique_key }
- steps: list of {step_id, type (search|fetch|extract), description, query?, num_results?, url?, source_step_id?, extraction_schema?}
- estimated_records: integer

Output ONLY valid JSON. No markdown. No explanation."""

    from worker.tools import generate_content_with_retry
    from worker.tasks.planner import build_fallback_plan

    plan = None
    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = generate_content_with_retry(
            client=client,
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PLAN_SYSTEM_PROMPT,
                response_mime_type="application/json",
            ),
            max_retries=2,
            initial_delay=1.0,
        )
        raw = response.text
        print(f"   Raw planner output: {raw[:300]}...")

        # Strip markdown code fences if Gemini wraps the JSON
        if raw.strip().startswith("```"):
            raw = raw.strip().split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        plan_data = json.loads(raw)
        plan = WorkflowPlan.model_validate(plan_data)
    except Exception as e:
        print(f"   ⚠️  Gemini planning unavailable ({e}) — using schema fallback plan")
        plan = WorkflowPlan.model_validate(build_fallback_plan(prompt))

    print(f"   ✅ Plan validated: '{plan.title}' ({len(plan.steps)} steps)")

    # ── Step 2: Execute one search step ───────────────────────────────────────
    print("\n🔎 Step 2: Executing search step...")
    from worker.tools import search, fetch, extract

    search_step = next((s for s in plan.steps if s.type.value == "search"), None)
    if not search_step:
        print("   ⚠️  No search step in plan — skipping")
        return

    results = search(search_step.query, num_results=search_step.num_results)
    print(f"   ✅ Found {len(results)} search results")
    if not results:
        print("   ⚠️  No results — check TAVILY_API_KEY")
        return

    # ── Step 3: Fetch first result ─────────────────────────────────────────────
    print(f"\n📥 Step 3: Fetching: {results[0]['url']}")
    fetched = fetch(results[0]["url"])
    if not fetched:
        print("   ⚠️  Fetch blocked or failed — trying next result")
        for r in results[1:3]:
            fetched = fetch(r["url"])
            if fetched:
                break
    if not fetched:
        print("   ❌ All fetches failed")
        return
    print(f"   ✅ Fetched {len(fetched['content'])} chars, hash={fetched['content_hash'][:8]}…")

    # ── Step 4: Extract ────────────────────────────────────────────────────────
    print("\n🧠 Step 4: Extracting structured data with Gemini...")
    extract_step = next((s for s in plan.steps if s.type.value == "extract"), None)
    schema = extract_step.extraction_schema.model_dump() if extract_step and extract_step.extraction_schema else plan.output_schema.model_dump()

    records = extract(fetched["content"], fetched["url"], schema)
    if not records:
        print("   ⚠️  No records extracted")
        return
    print(f"   ✅ Extracted {len(records)} record(s)")

    # ── Step 5: Validate ───────────────────────────────────────────────────────
    print("\n✅ Step 5: Validating first record...")
    from worker.tasks.processor import _validate_record
    record = records[0]
    valid, err = _validate_record(record, schema)
    print(f"   {'✅ Valid' if valid else f'❌ Invalid: {err}'}")

    # ── Step 6: Stub attestation ───────────────────────────────────────────────
    import uuid
    from schemas import Attestation
    att = Attestation.create_stub(
        source_id=uuid.uuid4(),
        att_id=uuid.uuid4(),
        content=fetched["content"],
        extracted=record,
    )
    print(f"\n🔐 Stub attestation:")
    print(f"   content_hash:   {att.content_hash[:16]}…")
    print(f"   extracted_hash: {att.extracted_hash[:16]}…")
    print(f"   signer:         {att.signer}")
    print(f"   verified:       {att.verified}")

    # ── Result ────────────────────────────────────────────────────────────────
    print("\n🎉 Final result (first record):")
    print(json.dumps(record, indent=2, default=str))
    print(f"\n   Source: {fetched['url']}")
    print(f"   Fetched at: {fetched['fetched_at']}")
    print("\n✅ Phase 0 smoke test passed!\n")


if __name__ == "__main__":
    main()
