"""
dynamic.py — Generate semantic diffs when outlook changes
Stores structured diff entries for the website dynamic tab
"""

import json
import os
import re
import time
from datetime import date
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Run: pip install anthropic --break-system-packages")


def append_dynamic(
    store: dict, old_outlook: dict, shift_result: dict, today: str, failed: bool = False
) -> dict:
    # No-shift stub — readers need to see "checked, nothing changed"
    if not shift_result["should_update"]:
        store["dynamic"].append(
            {
                "date": today,
                "outlook_version": store["outlook"]["version"],
                "title": "No change — sentiment within normal range",
                "severity": "none",
                "sections": [],
                "reason": (
                    f"Today's sentiment score ({shift_result['today_score']:+.2f}) "
                    f"was within the normal band. "
                    f"Rolling average: {shift_result['rolling_avg']:+.2f}, "
                    f"effective threshold: {shift_result['effective_threshold']}."
                ),
                "source_headline_ids": [],
            }
        )
        return store

    if failed:
        store["dynamic"].append(
            {
                "date": today,
                "outlook_version": store["outlook"]["version"],
                "title": "Shift detected — outlook update failed",
                "severity": shift_result["severity"],
                "sections": [],
                "reason": "A market shift was detected but the outlook update call failed. Will retry next run.",
                "source_headline_ids": [],
            }
        )
        return store

    # Generate semantic diff via Claude
    entry = _generate_diff_entry(store, old_outlook, shift_result, today)
    store["dynamic"].append(entry)
    return store


def _generate_diff_entry(
    store: dict, old_outlook: dict, shift_result: dict, today: str
) -> dict:

    load_dotenv()
    api_key=os.getenv("GEMINI_API_KEY")
    #print("api_key",api_key)
    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")

    old_sections = {s["id"]: s for s in old_outlook["sections"]}
    new_sections = {s["id"]: s for s in store["outlook"]["sections"]}

    old_text = "\n\n".join(
        f"[{sid}]\n{s['content']}" for sid, s in old_sections.items()
    )
    new_text = "\n\n".join(
        f"[{sid}]\n{s['content']}" for sid, s in new_sections.items()
    )

    prompt = f"""Compare these two versions of a market context document and produce a structured diff.

## Old version (outlook v{old_outlook["version"]}):
{old_text}

## New version (outlook v{store["outlook"]["version"]}):
{new_text}

## Shift details:
Severity: {shift_result["severity"]}
Score deviation: {shift_result["deviation"]}
Triggered by: score={shift_result["score_triggered"]}, flag={shift_result["flag_triggered"]}, streak={shift_result["streak_triggered"]}

Return ONLY a valid JSON object:
{{
  "title": "one-line summary of what changed (max 10 words, sentence case)",
  "sections": [
    {{
      "section_label": "short section name",
      "lines": [       
        {{"type": "removed", "text": "sentence that was removed or changed from"}},
        {{"type": "added", "text": "new sentence that replaced it"}}
      ]
    }}
  ],
  "reason": "2-3 sentences: why did these specific sentences change, which headlines caused it"
}}

Rules:
- Only include sections that actually changed
- Keep line text concise — full sentences but not paragraphs
- reason should be human-readable, not technical
- dont make any change if its anything with sentence reordering or something related to grammars
- No preamble, no markdown fences"""

    for attempt in range(1, 4):
        try:
            # response = client.messages.create(
            #     model="gemini-2.5-flash",
            #     max_tokens=600,
            #     messages=[{"role": "user", "content": prompt}],
            # )
            # raw = response.content[0].text

            response = client.chat.completions.create(
                model="gemini-3.5-flash",
                messages=[{"role": "user", "content": prompt}],
            )
            raw = response.choices[0].message.content
            clean = re.sub(r"```json\s*|```\s*", "", raw).strip()
            diff = json.loads(clean)

            return {
                "date": today,
                "outlook_version": store["outlook"]["version"],
                "title": diff.get("title", "outlook updated"),
                "severity": shift_result["severity"],
                "sections": diff.get("sections", []),
                "reason": diff.get("reason", ""),
                "source_headline_ids": diff.get("source_headline_ids", []),
            }

        except (json.JSONDecodeError, ValueError) as e:
            print(f"  dynamic diff error attempt {attempt}: {e}")
            if attempt < 3:
                time.sleep(2**attempt)
            continue

    # Fallback: minimal entry if diff generation fails
    return {
        "date": today,
        "outlook_version": store["outlook"]["version"],
        "title": f"Market shift — {shift_result['severity']} update",
        "severity": shift_result["severity"],
        "sections": [],
        "reason": "Diff generation failed — outlook was updated but detailed diff unavailable.",
        "source_headline_ids": store["outlook"]["trigger_headline_ids"],
    }