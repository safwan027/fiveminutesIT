"""
scraper.py — RSS scraping, deduplication, relevance scoring
"""

import hashlib
import re
from datetime import date, timedelta

try:
    import feedparser
except ImportError:
    raise ImportError("Run: pip install feedparser --break-system-packages")


# Keywords that increase relevance score
IT_JOB_KEYWORDS = [
    # Direct job signals
    "hiring",
    "layoff",
    "fired",
    "laid off",
    "job cut",
    "workforce reduction",
    "fresher",
    "campus placement",
    "offer letter",
    "joining date",
    "deferred",
    "recruitment",
    "headcount",
    "attrition",
    "appraisal",
    "salary",
    "hike",
    # Companies
    "tcs",
    "infosys",
    "wipro",
    "hcl",
    "tech mahindra",
    "accenture",
    "cognizant",
    "capgemini",
    "ibm india",
    "oracle india",
    "microsoft india",
    "google india",
    "amazon india",
    "nasscom",
    "gcc",
    "global capability centre",
    # Roles / skills
    "developer",
    "engineer",
    "programmer",
    "it jobs",
    "tech jobs",
    "ai jobs",
    "software engineer",
    "data engineer",
    "cloud",
    "devops",
    "ai/ml",
    # Market signals
    "it sector",
    "tech sector",
    "startup hiring",
    "india tech",
    "bengaluru",
    "hyderabad",
    "pune",
    "fy26",
    "fy27",
    "quarter",
    "results",
    "guidance",
]

# Keywords that disqualify a headline
NOISE_KEYWORDS = [
    "stock price",
    "share price",
    "nse",
    "bse",
    "quarterly earnings",
    "revenue guidance",
    "dividend",
    "buyback",
    "ipo",
    "merger",
    "cricket",
    "bollywood",
    "entertainment",
    "weather",
]


def _hash(text: str) -> str:
    return hashlib.md5(text.lower().strip().encode()).hexdigest()[:12]


def _is_recent(entry, yesterday: str) -> bool:
    """Accept headlines published yesterday or today (for timezone slack)."""
    published = getattr(entry, "published_parsed", None)
    if not published:
        return True  # If no date, include it — better than missing news
    from time import mktime
    from datetime import datetime

    entry_date = datetime.fromtimestamp(mktime(published)).date().isoformat()
    today = date.today().isoformat()
    return entry_date in (yesterday, today)


def _relevance_score(title: str, summary: str = "") -> int:
    text = (title + " " + summary).lower()

    # Hard disqualify
    for kw in NOISE_KEYWORDS:
        if kw in text:
            return -1

    score = 0
    for kw in IT_JOB_KEYWORDS:
        if kw in text:
            score += 1

    return score


def scrape_headlines(store: dict, today: str) -> list:
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    sources = [s for s in store["config"]["sources"] if s["active"]]

    # Ensure today's hash bucket exists
    if today not in store["headline_hashes"]:
        store["headline_hashes"][today] = []

    # print("headline_hashes",store["headline_hashes"]);
    # print("today",today);

    seen_hashes = set()
    for day_hashes in store["headline_hashes"].values():
        seen_hashes.update(day_hashes)

        # print("day_hashes",day_hashes);

    headlines = []

    for source in sources:
        print(f"  Fetching: {source['name']}...")
        try:
            feed = feedparser.parse(source["url"])
            fetched = 0

            for entry in feed.entries:
                title = getattr(entry, "title", "").strip()
                link = getattr(entry, "link", "").strip()
                summary = getattr(entry, "summary", "").strip()
                # client.messages.create
                if not title or not link:
                    continue

                # if not _is_recent(entry, yesterday):
                #     continue

                h = _hash(title)
                # print("h",h)
                # print("seen_hashes",seen_hashes)
                if h in seen_hashes:                 
                    continue

                # score = _relevance_score(title, summary)
                # print("score",score)
                # if score < 1:             
                #     continue 

                headlines.append(
                    {
                        "hash": h,
                        "title": title,
                        "link": link,
                        "source": source["name"],
                        "geo_tag": source["geo_tag"],
                        # "relevance_score": score,
                        "date": yesterday,
                    }
                )

                # print("headlines",headlines);               
                seen_hashes.add(h)
                store["headline_hashes"][today].append(h)
                fetched += 1

            store["source_last_seen"][source["name"]] = today
            print(f"    → {fetched} new relevant headlines")

        except Exception as e:
            print(f"    → FAILED: {e}")
            # Don't update source_last_seen — this lets the alerter detect stale sources

    # Sort by relevance score descending, take top 15
    #headlines.sort(key=lambda h: h["relevance_score"], reverse=True)
    return headlines[:15]
