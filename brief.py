"""
brief.py — Generate daily brief via Claude API
Three-layer prompt: system → context → task
"""

import json
import os
import re
import time
from dotenv import load_dotenv


try:
    from openai import OpenAI
except ImportError:
    raise ImportError("Run: pip install anthropic --break-system-packages")


OUTPUT_SCHEMA = """
{
  "headlines": [
    {
      "id": "string (the hash from input)",
      "link": string (url to source article)
      "text": "string (original headline title)",
      "geo": "India | Foreign (India-impacted) | Foreign (global signal)",
      "impact": "pos | neg | neu",
      "impact_label": "Positive | Negative | Mixed | Neutral",
      "badge": "string (short category: Layoffs | Fresher hiring | GCC signal | Startup hiring | Market signal | Policy | Skills signal | Deferred joins)",
      "detail": "2-3 sentences explaining exactly how this affects an Indian IT job seeker today"
    }
  ],
  "summary_positive": "string (2-3 sentences on headlines lifting market sentiment)",
  "summary_negative": "string (2-3 sentences on headlines dragging market sentiment)",
  "summary_neutral": "string (2-3 sentences on structurally important but sentiment-neutral headlines)",
  "sentiment_score": "float between -1.0 (very negative) and +1.0 (very positive)",
  "sentiment_label": "positive | negative | cautious | neutral",
  "shift_detected": "boolean — true if you believe the broader market narrative has materially changed today vs recent trend"
}
"""


def build_system_prompt() -> str:
    return f"""You are an expert analyst writing a daily job market brief for Indian IT professionals.
Your audience is freshers and recently laid-off developers actively looking for work in India.

Rules:
- Write every detail field from the perspective of a job seeker — not an investor, not a business analyst
- Be specific and actionable — tell them what to do with the information
- The sentiment_score must reflect the net effect on a job seeker's prospects, not general market health
- Set shift_detected=true only if today's headlines represent a structural change, not just a bad/good day
- Return ONLY a valid JSON object. No preamble, no explanation, no markdown fences.

Output schema:
{OUTPUT_SCHEMA}""".strip()

def build_context_block(store: dict) -> str:
    # Helper to clean up bad encodings like ï¿½
    def clean_text(text: str) -> str:
        return text.replace("ï¿½", "—").replace("ï¿½", "'")

    # Serialize outlook sections with sanitized content
    outlook_text = "\n\n".join(
        f"[Section: {s['id']}]\n{s['title']}\n{clean_text(s['content'])}"
        for s in store["outlook"]["sections"]
    )

    # Last 7 sentiment entries
    recent = store["sentiment_history"][-7:]
    if recent:
        sentiment_lines = "\n".join(
            [
    f"  {e['date']}: {float(e['score']):+.2f} ({e['label']})" 
    for e in recent 
    if e.get("score") not in ("", None) 
    and e.get("date") not in ("", None) 
    and e.get("label") not in ("", None)
]
        )
    else:
        sentiment_lines = "  No history yet — first run."




    return f"""## Current broader market context (outlook)
Use this as background lens. Do not summarise or rewrite it — just use it when judging each headline.

{outlook_text}

## Recent sentiment history (last 7 days)
{sentiment_lines}

7-day rolling average: {store["sentiment_7d_avg"]:+.2f}
Standard deviation: {store["sentiment_7d_std"]:.3f}
Shift threshold: {store["config"]["shift_threshold"]}

Set shift_detected=true if today's score would deviate from the rolling average by more than {store["config"]["shift_threshold"]}, OR if headlines represent a qualitative structural change.""".strip()

def build_task_block(headlines: list, today: str) -> str:
    formatted = "\n".join(
        f"{i + 1}. [id:{h['hash']}] [{h['geo_tag']}] {h['title']} (source: {h['source']})"
        for i, h in enumerate(headlines)
    )
    return f"""## Today's headlines — {today}
Analyse these {len(headlines)} headlines and produce the JSON brief.

{formatted}

keep maximum 6 - 8 headlines, not everything has to be related to job prospects, keep the 
market signal headlines as well, in brief also include the normal IT headlines too.

For each headline:
- Use the exact hash as the id field
- Write the detail field for someone who is actively job hunting in India's IT sector right now
- Choose the geo field based on whether this directly affects Indian jobs
- Rate impact based on effect on job seeker prospects specifically""".strip()

def parse_response(raw: str) -> dict:
    # Strip markdown fences if present
    clean = re.sub(r"```json\s*|```\s*", "", raw).strip()

    data = json.loads(clean)  # Raises json.JSONDecodeError if invalid

    required = [
        "headlines",
        "summary_positive",
        "summary_negative",
        "summary_neutral",
        "sentiment_score",
        "sentiment_label",
        "shift_detected",
    ]
    # for field in required:
    #     if field not in data:
    #         raise ValueError(f"Missing required field: {field}")

    # Validate score range
    score = float(data["sentiment_score"])
    if not (-1.0 <= score <= 1.0):
        raise ValueError(f"sentiment_score out of range: {score}")
    data["sentiment_score"] = round(score, 3)

    return data

def generate_brief(
    store: dict, headlines: list, today: str, max_retries: int = 3
) -> dict:

    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    # print("api_key",api_key)

    client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
    system = build_system_prompt()
    context = build_context_block(store)
    task = build_task_block(headlines, today)
    user_message = f"{context}\n\n---\n\n{task}"

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            print(f"  Gemini API call (attempt {attempt}/{max_retries})...")

            response = client.chat.completions.create(
        model="gemini-2.5-flash-lite", # Or gemini-2.5-pro
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user_message}
        ],
        # Explicitly pass basic json_object configuration
        # Do NOT pass full Pydantic schemas into response_format here
        response_format={"type": "json_object"},
        temperature=0.1
    ) 

            raw = response.choices[0].message.content
            # print("raw",raw)
            result = parse_response(raw)
            print(
                f"  Parsed successfully — {len(result['headlines'])} headlines processed"
            )
            return result

        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"  Parse error on attempt {attempt}: {e}")
            if attempt < max_retries:
                time.sleep(2**attempt)  # exponential backoff
            continue

        except Exception as e:
            # API errors — re-raise immediately
            raise RuntimeError(f"Gemini API error: {e}") from e

    raise RuntimeError(
        f"Failed to get valid JSON after {max_retries} attempts. "
        f"Last error: {last_error}"
    )