import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


DB_PATH = Path("data/mouseql.db")


st.set_page_config(
    page_title="MOUSEQL",
    layout="wide",
)

st.title("MOUSEQL")
st.write("Magic Kingdom wait time data")


@st.cache_data
def load_data():
    conn = sqlite3.connect(DB_PATH)

    waits = pd.read_sql_query(
        """
        SELECT
            recorded_at,
            attraction,
            wait_minutes,
            status
        FROM wait_times
        ORDER BY recorded_at
        """,
        conn,
    )

    conn.close()

    waits["recorded_at"] = pd.to_datetime(
        waits["recorded_at"],
        utc=True,
    ).dt.tz_convert("America/New_York")

    return waits


df = load_data()

if df.empty:
    st.warning("No wait time data has been collected yet.")
    st.stop()


# Dataset summary

st.header("Dataset")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Observations",
    f"{len(df):,}",
)

col2.metric(
    "Attractions",
    df["attraction"].nunique(),
)

col3.metric(
    "Average Wait",
    f"{df['wait_minutes'].mean():.1f} min",
)


# Attraction averages

st.header("Average Wait by Attraction")

attraction_summary = (
    df.dropna(subset=["wait_minutes"])
    .groupby("attraction", as_index=False)
    .agg(
        average_wait=("wait_minutes", "mean"),
        observations=("wait_minutes", "count"),
    )
)

attraction_summary["average_wait"] = (
    attraction_summary["average_wait"].round(1)
)

attraction_summary = attraction_summary.sort_values(
    "average_wait",
    ascending=False,
)

st.dataframe(
    attraction_summary,
    use_container_width=True,
    hide_index=True,
)


# Highest average waits

st.header("Highest Average Waits")

top_attractions = attraction_summary.head(10).copy()

st.bar_chart(
    top_attractions,
    x="attraction",
    y="average_wait",
)


# Wait times by hour

st.header("Average Wait by Hour")

hourly = df.dropna(subset=["wait_minutes"]).copy()

hourly["hour"] = hourly["recorded_at"].dt.hour

hourly_summary = (
    hourly.groupby("hour", as_index=False)
    .agg(
        average_wait=("wait_minutes", "mean"),
        observations=("wait_minutes", "count"),
    )
)

hourly_summary["average_wait"] = (
    hourly_summary["average_wait"].round(1)
)

st.line_chart(
    hourly_summary,
    x="hour",
    y="average_wait",
)


# Latest data

st.header("Latest Observations")

latest = (
    df.sort_values("recorded_at", ascending=False)
    .head(25)
    .copy()
)

latest["recorded_at"] = latest["recorded_at"].dt.strftime(
    "%B %d, %Y %I:%M %p"
)

st.dataframe(
    latest,
    use_container_width=True,
    hide_index=True,
)
