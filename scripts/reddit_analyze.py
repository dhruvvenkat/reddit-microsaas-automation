import os
import re
from collections import Counter

import pandas as pd

IN_PATH = os.path.join("data", "reddit_pain_signals.csv")
OUT_SCORES = os.path.join("data", "opportunity_scores.csv")
OUT_TOP = os.path.join("data", "top_ideas.md")


def normalize_text(s: str) -> str:
    s = (s or "").lower().strip()
    s = re.sub(r"\s+", " ", s)
    return s


def infer_cluster(text: str) -> str:
    t = normalize_text(text)

    rules = [
        ("lead follow-up automation", ["lead", "follow up", "crm", "pipeline", "prospect"]),
        ("invoice and payment chasing", ["invoice", "payment", "reminder", "accounts receivable"]),
        ("content repurposing", ["content", "repurpose", "post", "linkedin", "twitter", "x "]),
        ("reporting and dashboards", ["report", "dashboard", "spreadsheet", "excel", "manual report"]),
        ("customer support triage", ["support", "ticket", "inbox", "email", "response"]),
        ("scheduling and calendar ops", ["schedule", "calendar", "booking", "appointment"]),
        ("data entry automation", ["data entry", "copy paste", "manual", "repetitive"]),
    ]

    for label, keys in rules:
        if any(k in t for k in keys):
            return label
    return "other ops pain"


def score_group(group: pd.DataFrame) -> dict:
    n = len(group)
    freq = 5 if n >= 30 else 4 if n >= 20 else 3 if n >= 10 else 2 if n >= 5 else 1

    avg_hint = group["score_hint_num"].mean() if n else 0
    severity = 5 if avg_hint >= 20 else 4 if avg_hint >= 10 else 3 if avg_hint >= 5 else 2

    budget_ratio = (group["budget_signal"].fillna("").astype(str).str.lower() == "yes").mean() if n else 0
    budget = 5 if budget_ratio >= 0.5 else 4 if budget_ratio >= 0.3 else 3 if budget_ratio >= 0.15 else 2

    # reachability heuristic: subreddit diversity -> easier to find prospects
    sub_count = group["subreddit"].nunique()
    reachability = 5 if sub_count >= 4 else 4 if sub_count == 3 else 3 if sub_count == 2 else 2

    # build speed heuristic: short scope clusters easier
    cluster_name = group["cluster"].iloc[0]
    fast_clusters = {"lead follow-up automation", "invoice and payment chasing", "reporting and dashboards", "data entry automation"}
    build_speed = 5 if cluster_name in fast_clusters else 3

    total = freq + severity + budget + reachability + build_speed
    return {
        "frequency": freq,
        "severity": severity,
        "budget": budget,
        "reachability": reachability,
        "build_speed": build_speed,
        "total": total,
    }


def mvp_suggestion(cluster: str) -> str:
    mapping = {
        "lead follow-up automation": "Capture leads, auto-reminders, follow-up templates, pipeline status board.",
        "invoice and payment chasing": "Invoice tracking, reminder automation, overdue queue, one-click nudges.",
        "content repurposing": "Paste long-form text, auto-generate platform variants, schedule export.",
        "reporting and dashboards": "Connect CSV/Sheets, auto weekly KPI summary, simple trend dashboard.",
        "customer support triage": "Inbox ingestion, auto-labeling, response draft suggestions.",
        "scheduling and calendar ops": "Booking intake, auto-slot suggestions, reminder sequences.",
        "data entry automation": "Form/CSV intake, transformation templates, push to destination tools.",
    }
    return mapping.get(cluster, "Single workflow automation around a repeated operational pain.")


def pricing_suggestion(cluster: str) -> str:
    return "Starter $19/mo · Pro $49/mo · Team $99/mo"


def build_top_markdown(scored: pd.DataFrame) -> str:
    lines = ["# Top Micro-SaaS Ideas\n"]
    top = scored.sort_values("total", ascending=False).head(3)

    for i, row in enumerate(top.itertuples(index=False), start=1):
        lines.append(f"## {i}. {row.cluster} (Score: {row.total}/25)")
        lines.append(f"- Signals: {row.count} matched pain points")
        lines.append(f"- MVP: {mvp_suggestion(row.cluster)}")
        lines.append(f"- Pricing test: {pricing_suggestion(row.cluster)}")
        lines.append("- Validation week: 30 outreach msgs + 5 calls + pre-sell landing page")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    if not os.path.exists(IN_PATH):
        raise FileNotFoundError(f"Missing input file: {IN_PATH}. Run reddit_collect.py first.")

    df = pd.read_csv(IN_PATH)
    if df.empty:
        raise RuntimeError("Input CSV is empty.")

    df["pain_quote"] = df["pain_quote"].fillna("")
    df["cluster"] = df["pain_quote"].apply(infer_cluster)
    df["score_hint_num"] = pd.to_numeric(df["score_hint"], errors="coerce").fillna(0)

    rows = []
    for cluster, group in df.groupby("cluster"):
        s = score_group(group)
        rows.append(
            {
                "cluster": cluster,
                "count": len(group),
                **s,
            }
        )

    scored = pd.DataFrame(rows).sort_values("total", ascending=False)
    os.makedirs("data", exist_ok=True)
    scored.to_csv(OUT_SCORES, index=False)

    top_md = build_top_markdown(scored)
    with open(OUT_TOP, "w", encoding="utf-8") as f:
        f.write(top_md)

    print(f"Wrote scores -> {OUT_SCORES}")
    print(f"Wrote top ideas -> {OUT_TOP}")


if __name__ == "__main__":
    main()
