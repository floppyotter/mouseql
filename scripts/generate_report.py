import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path("data/mouseql.db")
REPORT_PATH = Path("reports/magic_kingdom_report.md")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Dataset stats
cur.execute("""
    SELECT
        COUNT(*) AS observations,
        COUNT(DISTINCT attraction) AS attractions,
        MIN(recorded_at) AS first_recorded,
        MAX(recorded_at) AS last_recorded
    FROM wait_times
""")
stats = cur.fetchone()

# Highest average waits
cur.execute("""
    SELECT
        attraction,
        ROUND(AVG(wait_minutes), 1) AS avg_wait
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
    GROUP BY attraction
    ORDER BY avg_wait DESC
    LIMIT 10
""")
highest_waits = cur.fetchall()

# Best overall hour
cur.execute("""
    SELECT
        CAST(strftime('%H', datetime(recorded_at, '-4 hours')) AS INTEGER)
            AS hour_of_day,
        ROUND(AVG(wait_minutes), 1) AS avg_wait,
        COUNT(*) AS observations
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
    GROUP BY hour_of_day
    ORDER BY avg_wait
    LIMIT 1
""")
best_hour = cur.fetchone()


def format_hour(hour):
    hour = int(hour)

    if hour == 0:
        return "12 AM"
    if hour < 12:
        return f"{hour} AM"
    if hour == 12:
        return "12 PM"

    return f"{hour - 12} PM"


report = f"""# Magic Kingdom Wait Time Report

Generated from the MOUSEQL wait-time dataset.

## Dataset

- Observations: **{stats['observations']}**
- Attractions: **{stats['attractions']}**
- First observation: `{stats['first_recorded']}`
- Latest observation: `{stats['last_recorded']}`

## Best Overall Time

Based on the data collected so far, the lowest average wait occurred around:

**{format_hour(best_hour['hour_of_day'])} — {best_hour['avg_wait']} minute average**

Observations during this hour: **{best_hour['observations']}**

## Highest Average Waits

| Attraction | Average Wait |
|---|---:|
"""

for row in highest_waits:
    report += f"| {row['attraction']} | {row['avg_wait']} min |\n"

report += """
---

*This report is generated automatically from data collected by MOUSEQL.*
"""

REPORT_PATH.write_text(report, encoding="utf-8")

conn.close()

print(f"Generated {REPORT_PATH}")
