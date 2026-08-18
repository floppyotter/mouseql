import sqlite3
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

DB_PATH = Path("data/mouseql.db")
REPORT_PATH = Path("reports/magic_kingdom_report.md")

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# --------------------------------------------------
# Dataset stats
# --------------------------------------------------

cur.execute("""
    SELECT
        COUNT(*) AS observations,
        COUNT(DISTINCT attraction) AS attractions,
        MIN(recorded_at) AS first_recorded,
        MAX(recorded_at) AS last_recorded
    FROM wait_times
""")
stats = cur.fetchone()


# --------------------------------------------------
# Highest average waits
# --------------------------------------------------

cur.execute("""
    SELECT
        attraction,
        ROUND(AVG(wait_minutes), 1) AS avg_wait,
        COUNT(*) AS observations
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
    GROUP BY attraction
    ORDER BY avg_wait DESC
    LIMIT 10
""")
highest_waits = cur.fetchall()


# --------------------------------------------------
# Pull wait-time observations for hourly analysis
# Python handles Eastern Time correctly, including DST
# --------------------------------------------------

cur.execute("""
    SELECT
        attraction,
        recorded_at,
        wait_minutes
    FROM wait_times
    WHERE wait_minutes IS NOT NULL
""")

wait_rows = cur.fetchall()

eastern = ZoneInfo("America/New_York")

hourly_data = {}

for row in wait_rows:
    utc_time = datetime.fromisoformat(
        row["recorded_at"].replace("Z", "+00:00")
    )
    eastern_time = utc_time.astimezone(eastern)

    hour = eastern_time.hour
    attraction = row["attraction"]
    wait = row["wait_minutes"]

    # Overall hourly data
    hourly_data.setdefault(hour, []).append(wait)


# --------------------------------------------------
# Best overall hour
# --------------------------------------------------

best_hour = None

if hourly_data:
    hour_results = []

    for hour, waits in hourly_data.items():
        hour_results.append({
            "hour": hour,
            "avg_wait": round(sum(waits) / len(waits), 1),
            "observations": len(waits),
        })

    best_hour = min(hour_results, key=lambda x: x["avg_wait"])


# --------------------------------------------------
# Best hour for each attraction
# --------------------------------------------------

attraction_hourly = {}

for row in wait_rows:
    utc_time = datetime.fromisoformat(
        row["recorded_at"].replace("Z", "+00:00")
    )
    eastern_time = utc_time.astimezone(eastern)

    attraction = row["attraction"]
    hour = eastern_time.hour
    wait = row["wait_minutes"]

    key = (attraction, hour)

    attraction_hourly.setdefault(key, []).append(wait)


best_times = {}

for (attraction, hour), waits in attraction_hourly.items():

    avg_wait = round(sum(waits) / len(waits), 1)

    candidate = {
        "hour": hour,
        "avg_wait": avg_wait,
        "observations": len(waits),
    }

    if (
        attraction not in best_times
        or avg_wait < best_times[attraction]["avg_wait"]
    ):
        best_times[attraction] = candidate


# --------------------------------------------------
# Formatting helpers
# --------------------------------------------------

def format_hour(hour):
    hour = int(hour)

    if hour == 0:
        return "12 AM"
    if hour < 12:
        return f"{hour} AM"
    if hour == 12:
        return "12 PM"

    return f"{hour - 12} PM"


def format_timestamp(timestamp):
    if not timestamp:
        return "N/A"

    utc_time = datetime.fromisoformat(
        timestamp.replace("Z", "+00:00")
    )

    eastern_time = utc_time.astimezone(eastern)

    return eastern_time.strftime(
        "%B %d, %Y at %I:%M %p ET"
    ).replace(" 0", " ")


# --------------------------------------------------
# Build report
# --------------------------------------------------

report = f"""# Magic Kingdom Wait Time Report

Generated automatically from the MOUSEQL wait-time dataset.

## Dataset

- Observations: **{stats['observations']}**
- Attractions: **{stats['attractions']}**
- First observation: **{format_timestamp(stats['first_recorded'])}**
- Latest observation: **{format_timestamp(stats['last_recorded'])}**

## Best Overall Time
"""

if best_hour:

    report += f"""
Based on the data collected so far, the lowest average wait occurred around:

**{format_hour(best_hour['hour'])} — {best_hour['avg_wait']} minute average**

Observations during this hour: **{best_hour['observations']}**
"""

else:

    report += """
Not enough data has been collected yet.
"""


# --------------------------------------------------
# Highest waits section
# --------------------------------------------------

report += """

## Highest Average Waits

| Attraction | Average Wait | Observations |
|---|---:|---:|
"""

for row in highest_waits:
    report += (
        f"| {row['attraction']} "
        f"| {row['avg_wait']} min "
        f"| {row['observations']} |\n"
    )


# --------------------------------------------------
# Best time by attraction
# --------------------------------------------------

report += """

## Best Time for Each Attraction

These are the lowest average wait times observed for each attraction so far.

Because the dataset is still growing, results based on only a few observations should be treated as preliminary.

| Attraction | Best Time | Average Wait | Observations |
|---|---:|---:|---:|
"""

for attraction in sorted(best_times):

    result = best_times[attraction]

    report += (
        f"| {attraction} "
        f"| {format_hour(result['hour'])} "
        f"| {result['avg_wait']} min "
        f"| {result['observations']} |\n"
    )


# --------------------------------------------------
# Footer
# --------------------------------------------------

report += """

---

*This report is generated automatically from data collected by MOUSEQL.*
"""


REPORT_PATH.write_text(report, encoding="utf-8")

conn.close()

print(f"Generated {REPORT_PATH}")
