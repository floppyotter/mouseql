import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from route_planner import rank_attractions


DB_PATH = Path("data/mouseql.db")
LOCATIONS_PATH = Path("data/attraction_locations.csv")

st.set_page_config(
    page_title="MOUSEQL",
    layout="wide",
)


# --------------------------------------------------
# Data
# --------------------------------------------------

@st.cache_data(ttl=300)
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


@st.cache_data(ttl=300)
def load_locations():
    locations = pd.read_csv(LOCATIONS_PATH)

    locations["latitude"] = pd.to_numeric(
        locations["latitude"],
        errors="coerce",
    )

    locations["longitude"] = pd.to_numeric(
        locations["longitude"],
        errors="coerce",
    )

    return locations.dropna(
        subset=["latitude", "longitude"]
    )


def format_hour(hour):
    hour = int(hour)

    if hour == 0:
        return "12 AM"

    if hour < 12:
        return f"{hour} AM"

    if hour == 12:
        return "12 PM"

    return f"{hour - 12} PM"


def build_historical_waits(data, current_hour):
    history = data.dropna(
        subset=["wait_minutes"]
    ).copy()

    history["hour"] = (
        history["recorded_at"].dt.hour
    )

    history = history[
        history["hour"] == current_hour
    ]

    if history.empty:
        return pd.DataFrame(
            columns=[
                "attraction",
                "typical_wait",
                "observations",
            ]
        )

    return (
        history.groupby(
            "attraction",
            as_index=False,
        )
        .agg(
            typical_wait=(
                "wait_minutes",
                "mean",
            ),
            observations=(
                "wait_minutes",
                "count",
            ),
        )
    )


df = load_data()
locations = load_locations()

if df.empty:
    st.warning(
        "No wait time data has been collected yet."
    )
    st.stop()


latest_waits = (
    df.sort_values("recorded_at")
    .groupby(
        "attraction",
        as_index=False,
    )
    .tail(1)
    .copy()
)

latest_timestamp = df["recorded_at"].max()
current_hour = latest_timestamp.hour

historical_waits = build_historical_waits(
    df,
    current_hour,
)


# --------------------------------------------------
# Header
# --------------------------------------------------

st.title("MOUSEQL")
st.subheader("Magic Kingdom Park Planner")

st.caption(
    "Latest data: "
    f"{latest_timestamp.strftime('%B %d, %Y at %I:%M %p')}"
)

st.divider()


# --------------------------------------------------
# Park day
# --------------------------------------------------

st.header("Plan Your Next Ride")

location_choices = sorted(
    locations["attraction"]
    .dropna()
    .unique()
)

if location_choices:

    current_attraction = st.selectbox(
        "Current location",
        location_choices,
        key="current_location",
    )

    ride_choices = [
        attraction
        for attraction in location_choices
        if attraction != current_attraction
    ]

    wanted_attractions = st.multiselect(
        "Attractions you still want to ride",
        ride_choices,
        default=ride_choices,
    )

    if wanted_attractions:

        with st.expander(
            "Ride priorities",
            expanded=False,
        ):

            st.caption(
                "Priority affects the recommendation while "
                "still accounting for walking time and waits."
            )

            must_do = st.multiselect(
                "Must Do",
                wanted_attractions,
                default=[],
                key="must_do_rides",
            )

            remaining_after_must = [
                attraction
                for attraction in wanted_attractions
                if attraction not in must_do
            ]

            want_to_do = st.multiselect(
                "Want to Do",
                remaining_after_must,
                default=[],
                key="want_to_do_rides",
            )

            if_theres_time = [
                attraction
                for attraction in wanted_attractions
                if attraction not in must_do
                and attraction not in want_to_do
            ]

            st.caption(
                f"If There's Time: "
                f"{len(if_theres_time)} attractions"
            )

        priorities = {}

        for attraction in must_do:
            priorities[attraction] = "Must Do"

        for attraction in want_to_do:
            priorities[attraction] = "Want to Do"

        for attraction in if_theres_time:
            priorities[attraction] = "If There's Time"

        selected_locations = locations[
            locations["attraction"].isin(
                wanted_attractions
                + [current_attraction]
            )
        ].copy()

        selected_waits = latest_waits[
            latest_waits["attraction"].isin(
                wanted_attractions
            )
        ].copy()

        selected_history = historical_waits[
            historical_waits["attraction"].isin(
                wanted_attractions
            )
        ].copy()

        recommendations = rank_attractions(
            current_attraction,
            selected_locations,
            selected_waits,
            selected_history,
            priorities,
        )

        if recommendations:

            best = recommendations[0]

            st.divider()

            st.header("Best Next Ride")

            st.subheader(
                best["attraction"]
            )

            col1, col2, col3, col4 = (
                st.columns(4)
            )

            col1.metric(
                "Priority",
                best["priority"],
            )

            col2.metric(
                "Walk",
                f"{best['walking_minutes']} min",
            )

            col3.metric(
                "Current Wait",
                f"{best['wait_minutes']} min",
            )

            col4.metric(
                "Walk + Wait",
                f"{best['total_minutes']} min",
            )

            if best["typical_wait"] is not None:

                difference = best["difference"]

                if difference < 0:
                    comparison = (
                        f"{abs(difference):.1f} minutes "
                        "below typical"
                    )

                elif difference > 0:
                    comparison = (
                        f"{difference:.1f} minutes "
                        "above typical"
                    )

                else:
                    comparison = "at the typical wait"

                st.write(
                    f"The current wait is **{comparison}** "
                    f"for {format_hour(current_hour)}."
                )

                st.caption(
                    f"Typical wait: "
                    f"{best['typical_wait']:.1f} min | "
                    f"{best['observations']} observations | "
                    f"{best['confidence']} confidence"
                )

            else:
                st.caption(
                    "Not enough historical data for a "
                    "same-hour comparison yet."
                )


            # ------------------------------------------
            # Other recommendations
            # ------------------------------------------

            st.subheader("Other Options")

            top_recommendations = (
                recommendations[1:6]
            )

            if top_recommendations:

                for number, ride in enumerate(
                    top_recommendations,
                    start=2,
                ):

                    st.markdown(
                        f"**{number}. {ride['attraction']}**"
                    )

                    details = (
                        f"{ride['walking_minutes']} min walk | "
                        f"{ride['wait_minutes']} min wait | "
                        f"{ride['total_minutes']} min total"
                    )

                    if ride["priority"] != "If There's Time":
                        details += (
                            f" | {ride['priority']}"
                        )

                    st.caption(details)

                    if (
                        ride["typical_wait"] is not None
                        and ride["confidence"] != "Low"
                    ):

                        difference = ride["difference"]

                        if difference <= -5:
                            st.caption(
                                "Current wait is lower "
                                "than typical."
                            )

                        elif difference >= 5:
                            st.caption(
                                "Current wait is higher "
                                "than typical."
                            )


            # ------------------------------------------
            # Full ranking
            # ------------------------------------------

            with st.expander(
                "View full recommendation table"
            ):

                recommendations_df = pd.DataFrame(
                    recommendations
                )

                recommendations_df = (
                    recommendations_df.rename(
                        columns={
                            "attraction": "Attraction",
                            "priority": "Priority",
                            "walking_minutes": "Walk",
                            "wait_minutes": "Wait Now",
                            "typical_wait": "Typical",
                            "difference": "Difference",
                            "observations": "History",
                            "confidence": "Confidence",
                            "wait_message": "Wait Status",
                            "total_minutes": "Walk + Wait",
                            "recommendation_score": "Score",
                        }
                    )
                )

                display_columns = [
                    "Attraction",
                    "Priority",
                    "Walk",
                    "Wait Now",
                    "Typical",
                    "Difference",
                    "History",
                    "Confidence",
                    "Wait Status",
                    "Walk + Wait",
                ]

                st.dataframe(
                    recommendations_df[
                        display_columns
                    ],
                    use_container_width=True,
                    hide_index=True,
                )

                st.caption(
                    "Recommendations consider ride priority, "
                    "walking time, current waits, and historical "
                    "wait patterns when enough history is available."
                )

        else:
            st.info(
                "None of the selected attractions currently "
                "have usable wait-time data."
            )

    else:
        st.info(
            "Choose at least one attraction you still want to ride."
        )

else:
    st.info(
        "No attraction locations are available."
    )


# --------------------------------------------------
# Park map
# --------------------------------------------------

st.divider()
st.header("Park Map")

if not locations.empty:

    map_data = locations.merge(
        latest_waits[
            [
                "attraction",
                "wait_minutes",
                "status",
            ]
        ],
        on="attraction",
        how="left",
    )

    st.map(
        map_data,
        latitude="latitude",
        longitude="longitude",
        size=20,
        use_container_width=True,
    )

    st.caption(
        f"{len(map_data)} attraction locations"
    )

else:
    st.info(
        "No attraction location data available."
    )


# --------------------------------------------------
# Data and history
# --------------------------------------------------

st.divider()
st.header("Data & History")

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
    "Overall Average Wait",
    f"{df['wait_minutes'].mean():.1f} min",
)


# --------------------------------------------------
# Attraction lookup
# --------------------------------------------------

st.subheader("Attraction Lookup")

attractions = sorted(
    df["attraction"]
    .dropna()
    .unique()
)

selected_attraction = st.selectbox(
    "Choose an attraction",
    attractions,
    index=(
        attractions.index(
            "TRON Lightcycle / Run"
        )
        if "TRON Lightcycle / Run" in attractions
        else 0
    ),
)

date_range = st.selectbox(
    "Date range",
    [
        "Today",
        "Last 7 days",
        "Last 30 days",
        "All data",
    ],
)

ride_data = (
    df[
        df["attraction"]
        == selected_attraction
    ]
    .dropna(
        subset=["wait_minutes"]
    )
    .sort_values("recorded_at")
    .copy()
)


# --------------------------------------------------
# Date filtering
# --------------------------------------------------

if not ride_data.empty:

    today = latest_timestamp.date()

    if date_range == "Today":

        ride_data = ride_data[
            ride_data["recorded_at"].dt.date
            == today
        ]

    elif date_range == "Last 7 days":

        cutoff = (
            latest_timestamp
            - pd.Timedelta(days=7)
        )

        ride_data = ride_data[
            ride_data["recorded_at"]
            >= cutoff
        ]

    elif date_range == "Last 30 days":

        cutoff = (
            latest_timestamp
            - pd.Timedelta(days=30)
        )

        ride_data = ride_data[
            ride_data["recorded_at"]
            >= cutoff
        ]


if not ride_data.empty:

    latest = ride_data.iloc[-1]

    latest_wait = latest["wait_minutes"]

    average_wait = (
        ride_data["wait_minutes"].mean()
    )

    lowest_wait = (
        ride_data["wait_minutes"].min()
    )

    highest_wait = (
        ride_data["wait_minutes"].max()
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Latest Wait",
        f"{latest_wait:.0f} min",
    )

    col2.metric(
        "Average Wait",
        f"{average_wait:.1f} min",
    )

    col3.metric(
        "Lowest",
        f"{lowest_wait:.0f} min",
    )

    col4.metric(
        "Highest",
        f"{highest_wait:.0f} min",
    )

    st.caption(
        f"{len(ride_data)} observations "
        f"in selected date range"
    )


    # Wait history

    st.subheader("Wait Time History")

    history = (
        ride_data[
            [
                "recorded_at",
                "wait_minutes",
            ]
        ]
        .set_index("recorded_at")
    )

    st.line_chart(
        history
    )


    # Best observed hour

    ride_data["hour"] = (
        ride_data["recorded_at"].dt.hour
    )

    ride_hourly = (
        ride_data.groupby(
            "hour",
            as_index=False,
        )
        .agg(
            average_wait=(
                "wait_minutes",
                "mean",
            ),
            observations=(
                "wait_minutes",
                "count",
            ),
        )
    )

    ride_hourly["average_wait"] = (
        ride_hourly["average_wait"].round(1)
    )

    best_hour = (
        ride_hourly
        .sort_values(
            [
                "average_wait",
                "observations",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .iloc[0]
    )

    st.write(
        f"Best observed hour: "
        f"**{format_hour(best_hour['hour'])}** "
        f"with an average wait of "
        f"**{best_hour['average_wait']:.1f} minutes** "
        f"across "
        f"**{int(best_hour['observations'])} observations**."
    )

else:

    st.info(
        "No observations are available for this attraction "
        "during the selected date range."
    )


# --------------------------------------------------
# Average wait by attraction
# --------------------------------------------------

st.divider()
st.subheader("Average Wait by Attraction")

attraction_summary = (
    df.dropna(
        subset=["wait_minutes"]
    )
    .groupby(
        "attraction",
        as_index=False,
    )
    .agg(
        average_wait=(
            "wait_minutes",
            "mean",
        ),
        observations=(
            "wait_minutes",
            "count",
        ),
    )
)

attraction_summary["average_wait"] = (
    attraction_summary["average_wait"].round(1)
)

attraction_summary = (
    attraction_summary
    .sort_values(
        "average_wait",
        ascending=False,
    )
)

st.dataframe(
    attraction_summary,
    use_container_width=True,
    hide_index=True,
)


# --------------------------------------------------
# Highest average waits
# --------------------------------------------------

st.subheader("Highest Average Waits")

top_attractions = (
    attraction_summary
    .head(10)
    .copy()
)

st.bar_chart(
    top_attractions,
    x="attraction",
    y="average_wait",
)


# --------------------------------------------------
# Average wait by hour
# --------------------------------------------------

st.subheader("Average Wait by Hour")

hourly = (
    df.dropna(
        subset=["wait_minutes"]
    )
    .copy()
)

hourly["hour"] = (
    hourly["recorded_at"].dt.hour
)

hourly_summary = (
    hourly.groupby(
        "hour",
        as_index=False,
    )
    .agg(
        average_wait=(
            "wait_minutes",
            "mean",
        ),
        observations=(
            "wait_minutes",
            "count",
        ),
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


# --------------------------------------------------
# Latest observations
# --------------------------------------------------

st.subheader("Latest Observations")

latest = (
    df.sort_values(
        "recorded_at",
        ascending=False,
    )
    .head(25)
    .copy()
)

latest["recorded_at"] = (
    latest["recorded_at"]
    .dt.strftime(
        "%B %d, %Y %I:%M %p"
    )
)

st.dataframe(
    latest,
    use_container_width=True,
    hide_index=True,
)
