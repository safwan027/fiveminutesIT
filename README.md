# India IT Brief — Daily Job Market Pipeline

Automated daily pipeline that scrapes Indian IT job market news, generates an AI-powered brief for job seekers, tracks sentiment over time, and publishes a three-tab website updated every morning.

## What it does

Every day at 12:01 AM IST:


1. **Scrapes** IT job market headlines from RSS feeds (ET, Moneycontrol, YourStory, Inc42, TechCrunch)
2. **Filters** for relevance to Indian IT job seekers and deduplicates
3. **Generates** a structured brief via Claude API — each headline explained from a job seeker's perspective
4. **Detects** market shifts using a three-check system (statistical deviation, semantic flag, streak)
5. **Updates** the broader market context (Para A) only when a real shift is detected
6. **Records** a git-diff style changelog of every Para A change
7. **Renders** three HTML pages and pushes to your website

## Project structure

```
it-brief-pipeline/
├── pipeline/
│   ├── run.py          # Main orchestrator — runs the full pipeline
│   ├── store.py        # Load/save/mutate context.json
│   ├── scraper.py      # RSS scraping + dedup + relevance filter
│   ├── brief.py        # Claude API brief generator (3-layer prompt)
│   ├── shift.py        # Three-check shift detector
│   ├── para_a.py       # Para A patch updater via Claude
│   ├── changelog.py    # Semantic diff generator via Claude
│   ├── renderer.py     # Jinja-style HTML renderer (3 pages)
│   ├── publisher.py    # Conditional git push
│   └── alerter.py      # Email alerts on failure
├── data/
│   └── context.json    # Persistent store — sentiment history, Para A, changelog
├── output/
│   ├── daily/          # Raw brief JSON files (one per day)
│   └── site/           # Rendered HTML — index.html, para-a.html, changelog.html
├── .github/
│   └── workflows/
│       └── daily-brief.yml   # GitHub Actions — runs at 12:01 AM IST
├── requirements.txt
├── setup.sh
└── .env.example
```

## Setup

### 1. Install

```bash
git clone <your-repo>
bash setup.sh
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

Required:
- `GEMINI_API_KEY` 

Optional but recommended:
- `ALERT_EMAIL` — email address for failure alerts
- `RESEND_API_KEY` — from [resend.com](https://resend.com) (free 100 emails/day)
- `WEBSITE_REPO_PATH` — path to your website git repo for auto-publishing






### 3. Test manually

```bash
source .env
python3 run.py
```
This runs the full pipeline once and writes output to `output/site/`.




### 4. Set up daily cron (Linux/Mac)

```bash
crontab -e
```

Add:
```
1 0 * * * TZ=Asia/Kolkata cd /path/to/it-brief-pipeline && source .env && python3 pipeline/run.py >> logs/pipeline.log 2>&1
```

### 5. Or use GitHub Actions

Push to GitHub and add these secrets in Settings → Secrets:
- `GEMINI_API_KEY`
- `ALERT_EMAIL` (optional)
- `RESEND_API_KEY` (optional)

The workflow runs automatically at 12:01 AM IST daily.

## Website publishing

The rendered HTML files in `output/site/` are self-contained — no framework, no build step.

<!-- **GitHub Pages**: Point GitHub Pages to the `output/site/` directory.

**Netlify**: Drag-drop the `output/site/` folder, or connect the repo and set publish directory to `output/site`. -->

**Manual**: Copy the three HTML files to any static host.
















## Tuning

All tunable parameters live in `data/context.json` under `config` — edit without touching code:

| Field | Default | Effect |
|-------|---------|--------|
| `shift_threshold` | `0.25` | How much sentiment must deviate to trigger Para A update |
| `min_headlines` | `5` | Abort if fewer headlines found (scraper likely broken) |
| `sentiment_window_days` | `7` | Rolling average window for shift detection |

If Para A updates too frequently → raise `shift_threshold` to `0.30`
If Para A never updates → lower to `0.20` or check Claude `shift_detected` flag logic

## The three website tabs

| Tab | File | Updated |
|-----|------|---------|
| Today's Brief | `index.html` | Every day |
| Market Context (Para A) | `para-a.html` | Only on shift |
| Change Log | `changelog.html` | Every day (shift entries + no-change stubs) |

## Token usage

| Run type | Approx tokens | Approx cost |
|----------|---------------|-------------|
| Normal day (no shift) | ~2,400 | ~$0.01 |
| Shift day | ~4,700 | ~$0.02 |
| Monthly | ~80,000–100,000 | ~$0.40 |

## Extending — WhatsApp push

When you're ready to push to WhatsApp, add at the end of `run.py`:

```python
from whatsapp import push_to_whatsapp
push_to_whatsapp(brief, store)
```

And create `pipeline/whatsapp.py` using the WhatsApp Business API or a Twilio MCP server.
The brief JSON is already structured for easy reformatting into plain text for messaging apps.
