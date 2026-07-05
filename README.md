# fiveminuteIT - IT Job Market Brief Pipeline

fiveminuteIT is an automated daily pipeline that curates IT job market news, analyzes sentiment, detects market shifts, and publishes a comprehensive daily brief via an email newsletter. It is designed to run automatically (e.g., via a daily cron job at 12:01 AM IST) and keeps professionals updated with a concise 5-minute read on the IT job market.

## Architecture & Pipeline

The pipeline is orchestrated by `run.py` and consists of several sequential stages:

1. **Context Store Loading (`store.py`)**: Loads historical data, previous configurations, and state from `data/context.json`.
2. **Scraping (`scraper.py`)**: Gathers and filters the latest IT job market headlines and news using RSS feeds.
3. **Brief Generation (`brief.py`)**: Leverages LLMs to analyze headlines, compute a sentiment score, and generate a concise summary.
4. **Shift Detection (`shift.py`)**: Analyzes the sentiment score against historical data to detect significant shifts in the market.
5. **Dynamic Content Update (`outlook.py` & `dynamic.py`)**: If a market shift is detected, it dynamically updates the core contextual paragraph ("outlook") and records the change in a dynamic.
6. **State Persistence**: Saves the updated context, sentiment history, and run status back to the JSON store.
7. **Email Rendering & Newsletter Publishing (`email_renderer.py` & `newsletter.py`)**: Renders a polished HTML email and dispatches the newsletter to subscribers using the Resend API.

## Requirements

The project uses Python and relies on the following key libraries:
- `feedparser` (for scraping RSS feeds)
- `openai` (for LLM interactions)
- `resend` (for sending email newsletters)
- `python-dotenv` (for environment variable management)

## Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd 5minIT
   ```

2. **Create a virtual environment (optional but recommended):**
   ```bash
   python -m venv myvenv
   # On Windows:
   myvenv\Scripts\activate
   # On macOS/Linux:
   source myvenv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and add your required API keys (e.g., for OpenAI and Resend):
   ```env
   OPENAI_API_KEY=your_openai_api_key
   RESEND_API_KEY=your_resend_api_key
   ```

5. **Data Initialization:**
   Ensure `data/context.json` is properly initialized as required by the `store.py` module.

5. **Subscribers:**
   Ensure `data/subscribers.txt` is properly initialized as required by the `newsletter.py` module. (Add your email address in the `data/subscribers.txt` file)

## Usage

To run the pipeline manually, execute the main script:

```bash
python run.py
```

## Deployment (GitHub Actions)

This service is designed to run completely hands-off via GitHub Actions.

1. Push your repository to GitHub.
2. In your repository, go to **Settings → Secrets and variables → Actions**.
3. Add the following Repository Secrets:
   - `GEMINI_API_KEY`
   - `RESEND_API_KEY`
   - `ALERT_EMAIL` (Optional: where failure alerts should be sent)

Ensure your `.github/workflows/daily-brief.yml` file is configured to run the pipeline automatically via `cron` schedule.


## Tuning Parameters

All tunable parameters live in `5minIT files/data/context.json` under `config`—you can edit these values without touching code:

| Field | Default | Effect |
|-------|---------|--------|
| `shift_threshold` | `0.25` | How much sentiment must deviate to trigger an Outlook update |
| `min_headlines` | `5` | Abort if fewer headlines are found (scraper likely broken) |
| `sentiment_window_days` | `7` | Rolling average window for shift detection |

*Note: If the Market Outlook updates too frequently, raise `shift_threshold` to `0.30`. If it never updates during volatile periods, lower it to `0.20`.*

## Contributing

<<<<<<< HEAD
We welcome contributions to make fiveminutesIT even better!
=======
We welcome contributions to make fiveminuteIT even better!
>>>>>>> 738b1d6fb62d7095da56a71799e19833f6bb098d

## How to Contribute
1. Fork the repository.
2. Create your feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request!
