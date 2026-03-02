import os
import csv
import time
import datetime as dt
from typing import Dict, List

import praw
from dotenv import load_dotenv

load_dotenv()

SUBREDDITS = ["SaaS", "smallbusiness", "Entrepreneur", "freelance", "startups"]
KEYWORDS = [
    "manual", "time-consuming", "takes forever", "spreadsheet", "error-prone",
    "need a tool", "looking for software", "too expensive", "hacky", "pain",
    "frustrating", "annoying", "wasting time", "automation"
]
POST_LIMIT_PER_SUBREDDIT = 120
TOP_LEVEL_COMMENT_LIMIT = 40
SLEEP_BETWEEN_POSTS_SEC = 0.2

OUT_PATH = os.path.join("data", "reddit_pain_signals.csv")


def ensure_env(name: str) -> str:
    val = os.getenv(name, "").strip()
    if not val:
        raise RuntimeError(f"Missing required env var: {name}")
    return val


def build_reddit_client() -> praw.Reddit:
    return praw.Reddit(
        client_id=ensure_env("REDDIT_CLIENT_ID"),
        client_secret=ensure_env("REDDIT_CLIENT_SECRET"),
        username=ensure_env("REDDIT_USERNAME"),
        password=ensure_env("REDDIT_PASSWORD"),
        user_agent=ensure_env("REDDIT_USER_AGENT"),
    )


def has_pain_signal(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)


def detect_budget_signal(text: str) -> str:
    t = (text or "").lower()
    budget_terms = ["pay", "paying", "subscription", "cost", "expensive", "$", "priced", "budget"]
    return "yes" if any(term in t for term in budget_terms) else ""


def make_row(
    *,
    source: str,
    subreddit: str,
    url: str,
    title: str,
    pain_quote: str,
    score_hint: int,
) -> Dict[str, str]:
    txt = pain_quote or ""
    return {
        "date": dt.datetime.now().isoformat(timespec="seconds"),
        "source": source,
        "subreddit": subreddit,
        "url": url,
        "title": (title or "").strip(),
        "pain_quote": txt.strip().replace("\n", " ")[:400],
        "persona": "",
        "current_workaround": "",
        "budget_signal": detect_budget_signal(txt),
        "score_hint": str(score_hint),
    }


def collect_rows(reddit: praw.Reddit) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    for sub in SUBREDDITS:
        sr = reddit.subreddit(sub)
        for post in sr.new(limit=POST_LIMIT_PER_SUBREDDIT):
            post_text = f"{post.title}\n{post.selftext or ''}"
            post_url = f"https://reddit.com{post.permalink}"

            if has_pain_signal(post_text):
                rows.append(
                    make_row(
                        source="reddit_post",
                        subreddit=sub,
                        url=post_url,
                        title=post.title,
                        pain_quote=(post.selftext or post.title),
                        score_hint=int(post.score or 0),
                    )
                )

            try:
                post.comments.replace_more(limit=0)
                comments = post.comments[:TOP_LEVEL_COMMENT_LIMIT]
                for c in comments:
                    body = getattr(c, "body", "") or ""
                    if has_pain_signal(body):
                        rows.append(
                            make_row(
                                source="reddit_comment",
                                subreddit=sub,
                                url=post_url,
                                title=post.title,
                                pain_quote=body,
                                score_hint=int(getattr(c, "score", 0) or 0),
                            )
                        )
            except Exception:
                pass

            time.sleep(SLEEP_BETWEEN_POSTS_SEC)

    return rows


def dedupe(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    out = []
    for r in rows:
        key = (r.get("url", ""), r.get("pain_quote", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def write_csv(rows: List[Dict[str, str]], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fields = [
        "date",
        "source",
        "subreddit",
        "url",
        "title",
        "pain_quote",
        "persona",
        "current_workaround",
        "budget_signal",
        "score_hint",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    reddit = build_reddit_client()
    rows = collect_rows(reddit)
    rows = dedupe(rows)
    write_csv(rows, OUT_PATH)
    print(f"Wrote {len(rows)} rows -> {OUT_PATH}")


if __name__ == "__main__":
    main()
