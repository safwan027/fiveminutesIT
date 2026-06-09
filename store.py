"""
store.py — Load, save, and mutate context.json
"""

import json
import statistics
from pathlib import Path


DEFAULT_STORE = {
    "last_run_date": None,
    "last_run_status": None,
    "last_run_headline_count": 0,
    "pipeline_version": "1.0.0",

    "headline_hashes": {},
    "source_last_seen": {},

    "sentiment_history": [],
    "sentiment_7d_avg": 0.0,
    "sentiment_7d_std": 0.0,
    "sentiment_label_counts": {
        "positive": 0, "negative": 0, "cautious": 0, "neutral": 0
    },

    "para_a": {
        "version": 1,
        "last_updated": None,
        "sections": [
            {
                "id": "bifurcation",
                "title": "The structural split",
                "content": (
                    "India's IT sector is not collapsing — it is bifurcating. "
                    "The traditional IT services model, which absorbed hundreds of thousands "
                    "of freshers for routine coding and testing work, is contracting. "
                    "Meanwhile, Global Capability Centres (GCCs) of multinationals are building "
                    "deep engineering teams in Bengaluru, Hyderabad, and Pune — paying 12–30% "
                    "more than legacy IT firms."
                ),
                "last_modified_date": None
            },
            {
                "id": "fresher_market",
                "title": "Fresher pipeline",
                "content": (
                    "Fresher hiring among tier-1 IT firms has fallen sharply from the FY22 peak "
                    "of 6 lakh combined. Infosys remains the lone bright spot. Wipro and Tech "
                    "Mahindra have deferred hundreds of joining letters. Campus hiring is recovering "
                    "but concentrated at premier institutes and in AI/cloud roles."
                ),
                "last_modified_date": None
            },
            {
                "id": "opportunity_map",
                "title": "Where opportunities actually are",
                "content": (
                    "GCCs are set to add 3–4 lakh net new jobs in 2026. India's startup ecosystem "
                    "— Razorpay, Zepto, Meesho, Swiggy — is actively hiring. The semiconductor "
                    "mission targets 10 lakh jobs. Tier-2 city IT hubs (Kochi, Coimbatore, Indore) "
                    "are growing with lower competition. Mid-career developers with 3–7 years "
                    "experience are in a seller's market."
                ),
                "last_modified_date": None
            },
            {
                "id": "skills_signal",
                "title": "Skills that change your odds",
                "content": (
                    "AI fluency — using GitHub Copilot, integrating LLM APIs, understanding RAG "
                    "pipelines — is now explicitly required at Accenture, TCS, and Infosys JDs. "
                    "Cloud, DevOps, and data engineering roles are growing 7% YoY while generic "
                    "developer roles contract. Tailored keyword-optimised resumes are mandatory "
                    "as ATS threshold has risen to 75–80%."
                ),
                "last_modified_date": None
            }
        ],
        "trigger_headline_ids": [],
        "shift_log": []
    },

    "changelog": [],

    "config": {
        "shift_threshold": 0.30,
        "min_headlines": 5,
        "sentiment_window_days": 7,
        "sources": [
            {
                "name": "Economic Times Tech",
                "url": "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
                "active": True,
                "geo_tag": "India"
            },
            {
                "name": "Moneycontrol Tech",
                "url": "https://www.moneycontrol.com/rss/technology.xml",
                "active": True,
                "geo_tag": "India"
            },
            {
                "name": "YourStory",
                "url": "https://yourstory.com/feed",
                "active": True,
                "geo_tag": "India"
            },
            {
                "name": "Inc42",
                "url": "https://inc42.com/feed/",
                "active": True,
                "geo_tag": "India"
            },
            {
                "name": "TechCrunch",
                "url": "https://techcrunch.com/feed/",
                "active": True,
                "geo_tag": "Foreign"
            }
        ]
    }
}


def load_store(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        print(f"  No store found at {path} — initialising with defaults.")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(DEFAULT_STORE, indent=2, ensure_ascii=False))
        return json.loads(json.dumps(DEFAULT_STORE))

    store = json.loads(path.read_text())

    # Merge any missing keys from DEFAULT_STORE (forward compatibility)
    for key, val in DEFAULT_STORE.items():
        if key not in store:
            store[key] = json.loads(json.dumps(val))

    return store


def save_store(path: Path, store: dict):
    Path(path).write_text(json.dumps(store, indent=2, ensure_ascii=False))


def append_sentiment(store: dict, today: str, score: float,
                     label: str, headline_count: int) -> dict:
    store["sentiment_history"].append({
        "date": today,
        "score": round(score, 3),
        "label": label,
        "headline_count": headline_count
    })

    # Update label counts
    label_key = label if label in store["sentiment_label_counts"] else "neutral"
    store["sentiment_label_counts"][label_key] = \
        store["sentiment_label_counts"].get(label_key, 0) + 1

    # Recompute rolling stats
    window = store["config"]["sentiment_window_days"]
    recent = [e["score"] for e in store["sentiment_history"][-window:]]
    store["sentiment_7d_avg"] = round(statistics.mean(recent), 3)
    store["sentiment_7d_std"] = (
        round(statistics.stdev(recent), 3) if len(recent) > 1 else 0.0
    )
    return store


def trim_store(store: dict) -> dict:
    # Keep 30 days of sentiment history
    store["sentiment_history"] = store["sentiment_history"][-30:]

    # Keep 14 days of headline hashes
    from datetime import date, timedelta
    cutoff = (date.today() - timedelta(days=14)).isoformat()
    store["headline_hashes"] = {
        d: hashes for d, hashes in store["headline_hashes"].items()
        if d >= cutoff
    }
    return store
