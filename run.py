"""
IT Job Market Brief — Daily Pipeline
Runs at 12:01 AM IST via cron.
Orchestrates: scrape → filter → brief → shift detect → Para A update → render → publish
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
from para_a import update_para_a
from changelog import append_changelog
from renderer import render_all
from publisher import publish
from alerter import send_alert

BASE = Path(__file__).parent.parent
# STORE_PATH = BASE/ "5minIT" / "data" / "context.json"
# OUTPUT_PATH = BASE/"5minIT" / "output"

STORE_PATH = BASE/ "data" / "context.json"
OUTPUT_PATH = BASE/ "output" 



def run_pipeline():
    # today = date.today().isoformat()
    ist = timezone(timedelta(hours=5, minutes=30))
    today = datetime.now(ist).date().isoformat()
    print(f"\n{'='*50}")
    print(f"5minIT Pipeline — {today}")
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
    print(f"  Should update Para A: {shift_result['should_update']}")
    if shift_result["should_update"]:
        print(f"  Severity: {shift_result['severity']}")
        print(f"  Triggered by: score={shift_result['score_triggered']} "
              f"flag={shift_result['flag_triggered']} "
              f"streak={shift_result['streak_triggered']}")

    # ── 5. Update Para A if shift detected ────────────────
    para_a_changed = False
    if shift_result["should_update"]:
        print("[5/7] Updating Para A...")
        try:
            old_para_a = json.loads(json.dumps(store["para_a"]))  # deep copy
            store = update_para_a(store, brief, headlines, shift_result)
            changelog_entry = append_changelog(store, old_para_a, shift_result, today)
            para_a_changed = True
            print(f"  Para A updated to v{store['para_a']['version']}")
        except Exception as e:
            msg = f"Para A update failed: {e}\n{traceback.format_exc()}"
            print(f"  ERROR: {msg}")
            # send_alert("Para A update failed (non-fatal)", msg)
            # Non-fatal — continue with old Para A
            append_changelog(store, store["para_a"], shift_result, today,
                             failed=True)
    else:
        print("[5/7] No shift — appending no-update stub to changelog...")
        append_changelog(store, store["para_a"], shift_result, today)

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
    render_all(store, brief, today, OUTPUT_PATH)
    # publish(OUTPUT_PATH, para_a_changed)

    print(f"\n✓ Pipeline complete — {datetime.now().strftime('%H:%M:%S')}\n")


if __name__ == "__main__":
    run_pipeline()
