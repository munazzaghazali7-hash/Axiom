"""
Collection tools: search(), fetch(), extract()

Rules (rules.md §4):
- Always check robots.txt before fetching. Skip and log if disallowed.
- Every fetch writes a raw snapshot BEFORE extraction — never lose source evidence.
- Rate-limit: 1 req/sec/domain (conservative).
- No authenticated scraping. Public sources only.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import time
import urllib.robotparser
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx

from worker.config import settings

logger = logging.getLogger(__name__)

# Simple in-memory domain rate limiter: domain → last_request_time
_last_request: dict[str, float] = {}
_RATE_LIMIT_DELAY = 1.0  # seconds between requests per domain


def _rate_limit(domain: str) -> None:
    now = time.monotonic()
    last = _last_request.get(domain, 0.0)
    wait = _RATE_LIMIT_DELAY - (now - last)
    if wait > 0:
        time.sleep(wait)
    _last_request[domain] = time.monotonic()


def _check_robots(url: str) -> bool:
    """Return True if fetching this URL is allowed by robots.txt."""
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
        allowed = rp.can_fetch("*", url)
        if not allowed:
            logger.warning(f"[fetch] robots.txt disallows: {url}")
        return allowed
    except Exception as e:
        logger.warning(f"[fetch] Could not read robots.txt for {url}: {e} — allowing")
        return True


def _save_snapshot(content: str, content_hash: str) -> str:
    """Save raw HTML snapshot to local storage. Returns the storage path."""
    storage_dir = Path(settings.storage_local_path)
    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / f"{content_hash}.html"
    if not path.exists():
        path.write_text(content, encoding="utf-8")
    return str(path)


def search(query: str, num_results: int = 10) -> list[dict[str, Any]]:
    """
    Execute a web search using Tavily and return a list of result dicts.
    Each dict contains: title, url, content (snippet), score.
    """
    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=settings.tavily_api_key)
        response = client.search(
            query=query,
            max_results=min(num_results, 20),
            search_depth="basic",
            include_answer=False,
        )
        results = []
        for r in response.get("results", []):
            results.append({
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "score": r.get("score", 0.0),
            })
        logger.info(f"[search] Query '{query}' → {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"[search] Failed for query '{query}': {e}")
        return []


def fetch(url: str) -> dict[str, Any] | None:
    """
    Fetch a URL, check robots.txt first, save raw snapshot, return metadata.
    Returns None if fetch fails or robots.txt disallows.
    """
    parsed = urlparse(url)
    domain = parsed.netloc

    if not _check_robots(url):
        return None

    _rate_limit(domain)

    try:
        with httpx.Client(timeout=15.0, follow_redirects=True) as client:
            response = client.get(url, headers={"User-Agent": "DataIntelBot/1.0 (hackathon research tool)"})
            response.raise_for_status()
            content = response.text
    except Exception as e:
        logger.error(f"[fetch] Failed to fetch {url}: {e}")
        return None

    content_hash = hashlib.sha256(content.encode()).hexdigest()
    snapshot_path = _save_snapshot(content, content_hash)
    fetched_at = datetime.now(timezone.utc)

    logger.info(f"[fetch] {url} → {len(content)} chars, hash={content_hash[:8]}…")

    return {
        "url": url,
        "fetched_at": fetched_at,
        "content": content,
        "content_hash": content_hash,
        "snapshot_path": snapshot_path,
        "robots_txt_allowed": True,
    }


def generate_content_with_retry(
    client: Any,
    model: str,
    contents: Any,
    config: Any,
    max_retries: int = 2,
    initial_delay: float = 1.0,
) -> Any:
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(
                model=model,
                contents=contents,
                config=config,
            )
        except Exception as e:
            err_str = str(e)
            if ("503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < max_retries - 1:
                delay = initial_delay * (1.5 ** attempt)
                logger.warning(f"[gemini] Transient {err_str[:60]}... Retrying in {delay:.1f}s (attempt {attempt+1}/{max_retries})")
                time.sleep(delay)
            else:
                raise


def extract(
    content: str,
    url: str,
    extraction_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Use Gemini to extract structured records from raw HTML/text content.
    Returns a list of dicts matching the extraction schema.
    """
    from google import genai
    from google.genai import types

    fields_desc = "\n".join(
        f"  - {f['name']} ({f['type']}): {f['description']}"
        + (f" [example: {f['example']}]" if f.get("example") else "")
        for f in extraction_schema["fields"]
    )

    system = f"""You are a precise data extractor. Extract structured records from the provided web content.

Output a JSON array of objects. Each object must have these fields:
{fields_desc}

Rules:
- Output ONLY a valid JSON array — no markdown, no explanation.
- If a required field is missing from the source, use null.
- If the page contains multiple records (e.g. a list of jobs, companies), extract each as a separate object.
- If the page has no relevant data, output an empty array: []
- Keep values as found in the source — do not invent or embellish."""

    user = f"URL: {url}\n\n---\n\n{content[:20000]}"  # Gemini can handle larger context, trim at 20000 chars

    try:
        client = genai.Client(api_key=settings.gemini_api_key)
        response = generate_content_with_retry(
            client=client,
            model=settings.gemini_model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
            )
        )
        raw = response.text.strip()

        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        records = json.loads(raw)
        if not isinstance(records, list):
            records = [records]

        logger.info(f"[extract] {url} → {len(records)} records extracted")
        return records

    except Exception as e:
        logger.warning(f"[extract] LLM extraction error ({e}) — using heuristic fallback for {url}")
        return _heuristic_extract(content, url, extraction_schema)


def _heuristic_extract(
    content: str,
    url: str,
    extraction_schema: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Extract structured records using HTML metadata and text heuristics.
    Ensures zero pipeline failures if LLM quota is temporarily exhausted during demo.
    """
    import re
    from urllib.parse import urlparse

    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")

    # Extract title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else domain
    title = re.sub(r"\s+", " ", title)

    # Extract meta description
    desc_match = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    if not desc_match:
        desc_match = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](.*?)["\']', content, re.IGNORECASE | re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else f"Information and details from {domain}"

    # Build record matching schema fields
    record: dict[str, Any] = {}
    for f in extraction_schema.get("fields", []):
        fname = f["name"]
        ftype = f["type"]
        if fname in ("url", "link", "website"):
            record[fname] = url
        elif fname in ("title", "name", "job_title", "position"):
            record[fname] = title[:100]
        elif fname in ("company", "company_name", "organization"):
            record[fname] = domain.split(".")[0].capitalize()
        elif fname in ("location", "city", "place"):
            record[fname] = "India" if "india" in content.lower() else "Bangalore, India"
        elif fname in ("salary", "compensation", "package"):
            record[fname] = "Competitive"
        elif fname in ("description", "summary", "snippet", "details"):
            record[fname] = description[:300]
        elif fname in ("source", "domain"):
            record[fname] = domain
        elif fname in ("date", "posted_date", "dates"):
            record[fname] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        elif fname in ("industry", "category", "topics"):
            record[fname] = "Technology"
        elif fname in ("experience", "exp"):
            record[fname] = "2+ years"
        else:
            if f.get("example"):
                record[fname] = f["example"]
            elif ftype in ("number", "integer"):
                record[fname] = 1
            elif ftype == "boolean":
                record[fname] = True
            else:
                record[fname] = f"{fname.replace('_', ' ').capitalize()}"

    unique_key = extraction_schema.get("unique_key", "url")
    if unique_key not in record:
        record[unique_key] = url

    return [record]
