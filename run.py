"""
fiveminutesIT — Pipeline
Runs at 12:01 AM IST via cron.
Orchestrates: scrape → filter → brief → shift detect → outlook update → email
"""

import json
import sys
import traceback
from datetime import date, datetime, timezone, timedelta
from pathlib import Path

from scraper import scrape_headlines
from store import load_store, save_store, append_sentiment, trim_store
from brief import generate_brief
from shift import detect_shift
from outlook import update_outlook
from dynamic import append_dynamic
from email_renderer import render_email
from newsletter import send_newsletter

BASE = Path(__file__).parent.parent
STORE_PATH = BASE/ "fiveminuteIT" / "data" / "context.json"






def run_pipeline():
    # today = date.today().isoformat()
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).date().isoformat()
    print(f"fiveminutesIT Pipeline ")
    print(f"{'='*50}\n")

    # ── 1. Load context store ──────────────────────────────
    print("[1/7] Loading context store...")
    store = load_store(STORE_PATH)

    # Guard: don't run twice on same day
    if store.get("last_run_date") == today and store.get("last_run_status") == "success":
        print(f"  Already ran successfully today ({today}). Exiting.")
        sys.exit(0)

    # ── 2. Scrape headlines ────────────────────────────────
    print("[2/7] Scraping headlines...")
    try:
        headlines = scrape_headlines(store, today)
        print(f"  {len(headlines)} headlines after dedup + filter")
    except Exception as e:
        msg = f"Scraping failed: {e}"
        print(f"  ERROR: {msg}")
        store["last_run_date"] = today
        store["last_run_status"] = "failed"
        save_store(STORE_PATH, store)
        # send_alert("Pipeline FAILED — scrape step", msg)
        sys.exit(1)

    if len(headlines) < store["config"]["min_headlines"]:
        msg = f"Only {len(headlines)} headlines found (min: {store['config']['min_headlines']}). Aborting."
        print(f"  WARNING: {msg}")
        store["last_run_date"] = today
        store["last_run_status"] = "failed"
        save_store(STORE_PATH, store)
        # send_alert("Pipeline ABORTED — too few headlines", msg)
        sys.exit(1)

    # ── 3. Generate brief via Claude ──────────────────────
    print("[3/7] Generating brief (Claude API)...")
    try:
        brief = generate_brief(store, headlines, today)
        print(f"  Sentiment: {brief['sentiment_label']} ({brief['sentiment_score']:+.2f})")
        print(f"  Claude shift flag: {brief['shift_detected']}")
    except Exception as e:
        msg = f"Brief generation failed: {e}\n{traceback.format_exc()}"
        print(f"  ERROR: {msg}")
        store["last_run_date"] = today
        store["last_run_status"] = "partial"
        save_store(STORE_PATH, store)
        # send_alert("Pipeline FAILED — Claude brief step", msg)
        sys.exit(1)

    # ── 4. Detect market shift ────────────────────────────
    print("[4/7] Running shift detector...")
    shift_result = detect_shift(store, brief["sentiment_score"],
                                brief["sentiment_label"], brief["shift_detected"])
    print(f"  Should update outlook: {shift_result['should_update']}")
    if shift_result["should_update"]:
        print(f"  Severity: {shift_result['severity']}")
        print(f"  Triggered by: score={shift_result['score_triggered']} "
              f"flag={shift_result['flag_triggered']} "
              f"streak={shift_result['streak_triggered']}")

    # ── 5. Update outlook if shift detected ────────────────
    outlook_changed = False
    if shift_result["should_update"]:
        print("[5/7] Updating outlook...")
        try:
            old_outlook = json.loads(json.dumps(store["outlook"]))  # deep copy
            store = update_outlook(store, brief, headlines, shift_result)
            dynamic_entry = append_dynamic(store, old_outlook, shift_result, today)
            outlook_changed = True
            print(f"  outlook updated to v{store['outlook']['version']}")
        except Exception as e:
            msg = f"outlook update failed: {e}\n{traceback.format_exc()}"
            print(f"  ERROR: {msg}")
            # send_alert("outlook update failed (non-fatal)", msg)
            # Non-fatal — continue with old outlook
            append_dynamic(store, store["outlook"], shift_result, today,
                             failed=True)
    else:
        print("[5/7] No shift — appending no-update stub to changelog...")
        append_dynamic(store, store["outlook"], shift_result, today)

    # ── 6. Update store state ─────────────────────────────
    print("[6/7] Updating store...")
    store = append_sentiment(store, today, brief["sentiment_score"],
                             brief["sentiment_label"], len(headlines))
    store = trim_store(store)
    store["last_run_date"] = today
    store["last_run_status"] = "success"
    store["last_run_headline_count"] = len(headlines)
    save_store(STORE_PATH, store)   

    # Save daily brief JSON
    # daily_path = OUTPUT_PATH / "daily" / f"{today}.json"
    # daily_path.parent.mkdir(parents=True, exist_ok=True)
    # daily_path.write_text(json.dumps(brief, indent=2, ensure_ascii=False))
    # print(f"Daily brief saved: {daily_path}")

    # ── 7. Render + publish ───────────────────────────────
    print("[7/7] Rendering HTML and publishing...")
    #render_all(store, brief, today, OUTPUT_PATH)
    # publish(OUTPUT_PATH, para_a_changed)

    # ── 8. Send Newsletter ────────────────────────────────
    print("[8/8] Generating and sending email newsletter...")
    try:
        email_html = render_email(brief, store, today)
        send_newsletter(f"fiveminutesIT - {today}", email_html)
    except Exception as e:
        print(f"  ERROR sending newsletter: {e}\n{traceback.format_exc()}")

    print(f"\n✓ Pipeline complete — {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == "__main__":
    run_pipeline()
