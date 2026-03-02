# Reddit MicroSaaS Automation

A lightweight pipeline to discover repeated pain points on Reddit and turn them into scored micro-SaaS opportunities.

## What this does

1. Collects pain-signal posts/comments from selected subreddits
2. Saves normalized rows to CSV
3. Clusters and scores opportunities
4. Outputs top ideas with quick MVP/pricing suggestions

## Setup

### 1) Create and activate a virtual environment (recommended)

```powershell
cd "C:\Users\Owner\Documents\Programming Projects\reddit-microsaas-automation"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```powershell
pip install -r requirements.txt
```

### 3) Configure environment

Copy `.env.example` to `.env` and fill values.

```powershell
Copy-Item .env.example .env
```

You need Reddit script app credentials from:
https://www.reddit.com/prefs/apps

## Run

```powershell
python scripts/reddit_collect.py
python scripts/reddit_analyze.py
```

Outputs:
- `data/reddit_pain_signals.csv`
- `data/opportunity_scores.csv`
- `data/top_ideas.md`

## Customize

Edit these in `scripts/reddit_collect.py`:
- `SUBREDDITS`
- `KEYWORDS`
- `POST_LIMIT_PER_SUBREDDIT`
- `TOP_LEVEL_COMMENT_LIMIT`

## Notes

- Respect Reddit API usage policies and rate limits.
- This is idea discovery, not financial advice.
