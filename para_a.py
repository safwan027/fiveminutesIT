"""
para_a.py — Patch Para A sections when a shift is detected
Only rewrites sections that are factually outdated — not the whole document
"""

import json
import os
import re
import time
from datetime import date, datetime, timezone, timedelta
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Run: pip install anthropic --break-system-packages")


def update_para_a(
    store: dict, brief: dict, headlines: list, shift_result: dict
) -> dict:
    load_dotenv()
    api_key=os.getenv("GEMINI_API_KEY")
    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).date().isoformat()

    # Serialize current Para A for the prompt
    current_sections = "\n\n".join(
        f"[{s['id']}]\nTitle: {s['title']}\nContent: {s['content']}"
        for s in store["para_a"]["sections"]
    )

    # Summary of today's shift signals
    shift_summary = (
        f"Severity: {shift_result['severity']}\n"
        f"Score deviation: {shift_result['deviation']} "
        f"(threshold: {shift_result['effective_threshold']})\n"
        f"Claude shift flag: {shift_result['flag_triggered']}\n"
        f"Streak triggered: {shift_result['streak_triggered']}"
    )

    # Today's headlines that triggered the shift
    trigger_headlines = "\n".join(
        f"- [{h['hash']}] {h['title']}" for h in headlines[:10]
    )

    prompt = f"""You are updating a standing market analysis document for Indian IT job seekers.

## Current Para A sections:
{current_sections}

## Shift signals today:
{shift_summary}

## Today's triggering headlines:
{trigger_headlines}

## Today's brief summaries:
Positive: {brief["summary_positive"]}
Negative: {brief["summary_negative"]}
Neutral: {brief["summary_neutral"]}

## Instructions:
1. Identify which sections are now factually outdated based on today's headlines
2. Rewrite ONLY those sections — leave others exactly as they are
3. Keep the same section ids and titles
4. Content should remain 2-4 sentences per section — concise, factual, job-seeker focused
5. Do NOT add new sections or remove existing ones

Return ONLY a valid JSON array of ALL sections (updated and unchanged):
[
  {{"id": "section_id", "title": "section title", "content": "updated or unchanged content"}}
]

No preamble, no explanation, no markdown fences."""

    for attempt in range(1, 4):
        try:
            print(f"  Para A update call (attempt {attempt}/3)...")
            # response = client.chat.completions.create(
            #     model="gemini-2.5-flash",
            #     messages=[{"role": "user", "content": prompt}],
            # )
            # raw = response.choices[0].message.content
            # clean = re.sub(r"```json\s*|```\s*", "", raw).strip()
            # new_sections_raw = json.loads(clean)

            response = client.chat.completions.create(
                model="gemini-2.5-flash",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content

            # 1. Look specifically for anything trapped between ```json and ```
            # The DOTALL flag ensures it captures line breaks too.
            match = re.search(r"```json\s*(.*?)\s*```", raw, re.DOTALL)
            
            if match:
                clean = match.group(1).strip()
            else:
                # Fallback: if the model forgot markdown block entirely and just returned pure JSON
                clean = raw.strip()
            
            try:
                new_sections_raw = json.loads(clean)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON. Raw output was: {raw}")
                raise e

            # Validate structure
            if not isinstance(new_sections_raw, list):
                raise ValueError("Expected a JSON array")

            # Merge: preserve last_modified_date for unchanged sections
            old_sections = {s["id"]: s for s in store["para_a"]["sections"]}
            new_sections = []

            for ns in new_sections_raw:
                old = old_sections.get(ns["id"], {})
                changed = old.get("content", "") != ns["content"]
                new_sections.append(
                    {
                        "id": ns["id"],
                        "title": ns["title"],
                        "content": ns["content"],
                        "last_modified_date": today
                        if changed
                        else old.get("last_modified_date"),
                    }
                )

            # Record which headlines triggered this update
            trigger_ids = [h["hash"] for h in headlines[:10]]

            # Update store
            store["para_a"]["sections"] = new_sections
            store["para_a"]["version"] = store["para_a"]["version"] + 1
            store["para_a"]["last_updated"] = today
            store["para_a"]["trigger_headline_ids"] = trigger_ids
            store["para_a"]["shift_log"].append(
                {
                    "date": today,
                    "version_after": store["para_a"]["version"],
                    "severity": shift_result["severity"],
                    "trigger_score_delta": shift_result["deviation"],
                }
            )

            return store

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  Para A parse error attempt {attempt}: {e}")
            if attempt < 3:
                time.sleep(2**attempt)
            continue

    raise RuntimeError("Para A update failed after 3 attempts")
