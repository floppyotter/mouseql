import sqlite3
from pathlib import Path
from textwrap import dedent

import pandas as pd
import pydeck as pdk
import streamlit as st

from route_planner import (
    rank_attractions,
    get_route_coordinates,
)

from itinerary_planner import (
    build_itinerary,
)


DB_PATH = Path("data/mouseql.db")
WAITS_CSV_PATH = Path("data/magic_kingdom_waits.csv")
LOCATIONS_PATH = Path("data/attraction_locations.csv")

MIN_USABLE_WAITS_PER_SNAPSHOT = 3


st.set_page_config(
    page_title="MOUSEQL",
    layout="wide",
)


def render_html(content):
    st.html(
        dedent(content)
    )


render_html(
    """
    <style>
    :root {
        --bg: #090d19;
        --surface: #12192b;
        --surface-2: #171f34;
        --text: #f5f1e9;
        --muted: #a4a9ba;
        --lavender: #b9add5;
        --gold: #d8c58f;
        --border: rgba(188, 177, 218, 0.16);
    }

    .stApp {
        background:
            radial-gradient(
                circle at 90% 0%,
                rgba(125, 108, 168, 0.17),
                transparent 28rem
            ),
            linear-gradient(
                180deg,
                #090d19 0%,
                #0a0f1d 45%,
                #0b1020 100%
            );
    }

    [data-testid="stHeader"] {
        background: rgba(9, 13, 25, 0.85);
    }

    .block-container {
        max-width: 1180px;
        padding-top: 2rem;
        padding-bottom: 5rem;
    }

    h1,
    h2,
    h3 {
        color: var(--text);
        letter-spacing: -0.025em;
    }

    hr {
        border-color: rgba(188, 177, 218, 0.11);
        margin: 2.6rem 0;
    }

    .mouseql-hero {
        position: relative;
        overflow: hidden;

        padding:
            2.6rem
            2.7rem
            2.45rem;

        margin-bottom: 2.2rem;

        border-radius: 28px;

        border:
            1px solid
            rgba(191, 179, 220, 0.22);

        background:
            radial-gradient(
                circle at 88% 10%,
                rgba(187, 167, 222, 0.22),
                transparent 17rem
            ),
            radial-gradient(
                circle at 75% 85%,
                rgba(215, 195, 145, 0.07),
                transparent 13rem
            ),
            linear-gradient(
                135deg,
                rgba(25, 32, 56, 0.98),
                rgba(13, 18, 34, 0.98)
            );

        box-shadow:
            0 26px 65px
            rgba(0, 0, 0, 0.30);
    }

    .mouseql-hero::after {
        content: "";
        position: absolute;

        width: 220px;
        height: 220px;

        right: -80px;
        top: -95px;

        border-radius: 999px;

        border:
            1px solid
            rgba(215, 195, 145, 0.12);
    }

    .mouseql-eyebrow {
        color: #c6b9da;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.17em;
        text-transform: uppercase;
        margin-bottom: 0.75rem;
    }

    .mouseql-title {
        color: #f7f3eb;

        font-size:
            clamp(
                3rem,
                7vw,
                5rem
            );

        line-height: 0.96;
        font-weight: 790;
        letter-spacing: -0.06em;
        margin: 0;
    }

    .mouseql-subtitle {
        max-width: 660px;
        color: #b4b8c8;
        font-size: 1.03rem;
        line-height: 1.65;
        margin-top: 1rem;
        margin-bottom: 1.4rem;
    }

    .mouseql-status {
        display: inline-flex;
        align-items: center;

        padding:
            0.52rem
            0.82rem;

        border-radius: 999px;

        background:
            rgba(215, 195, 145, 0.08);

        border:
            1px solid
            rgba(215, 195, 145, 0.20);

        color: #dacb9e;
        font-size: 0.78rem;
    }

    .mouseql-section {
        margin-bottom: 1.1rem;
    }

    .mouseql-kicker {
        color: #afa2cc;
        font-size: 0.69rem;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        font-weight: 750;
        margin-bottom: 0.35rem;
    }

    .mouseql-section-title {
        color: #f3efe7;

        font-size:
            clamp(
                1.7rem,
                4vw,
                2.3rem
            );

        letter-spacing: -0.04em;
        font-weight: 710;
        line-height: 1.12;
        margin-bottom: 0.35rem;
    }

    .mouseql-section-copy {
        color: #969caf;
        font-size: 0.91rem;
        line-height: 1.55;
        max-width: 750px;
    }

    .mouseql-best-card {
        padding:
            1.6rem
            1.7rem;

        border-radius: 22px;

        margin:
            1.3rem
            0
            1.2rem;

        border:
            1px solid
            rgba(195, 182, 225, 0.27);

        background:
            radial-gradient(
                circle at 90% 15%,
                rgba(200, 184, 230, 0.13),
                transparent 12rem
            ),
            linear-gradient(
                135deg,
                rgba(38, 43, 69, 0.94),
                rgba(21, 27, 47, 0.95)
            );

        box-shadow:
            0 16px 40px
            rgba(0, 0, 0, 0.18);
    }

    .mouseql-best-label {
        color: #beb0d7;
        font-size: 0.68rem;
        font-weight: 760;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        margin-bottom: 0.58rem;
    }

    .mouseql-best-name {
        color: #f6f2ea;

        font-size:
            clamp(
                1.8rem,
                4.6vw,
                2.6rem
            );

        font-weight: 740;
        line-height: 1.1;
        letter-spacing: -0.04em;
    }

    .mouseql-best-total {
        color: #d8c894;
        font-size: 0.9rem;
        margin-top: 0.7rem;
    }

    .mouseql-itinerary {
        position: relative;

        margin:
            1.2rem
            0;
    }

    .mouseql-step {
        position: relative;

        padding:
            1rem
            1rem
            1rem
            3.7rem;

        margin-bottom: 0.75rem;

        border-radius: 16px;

        border:
            1px solid
            rgba(184, 174, 215, 0.13);

        background:
            linear-gradient(
                135deg,
                rgba(23, 30, 52, 0.86),
                rgba(17, 23, 40, 0.86)
            );
    }

    .mouseql-step-number {
        position: absolute;

        left: 1rem;
        top: 1rem;

        width: 2rem;
        height: 2rem;

        display: flex;
        align-items: center;
        justify-content: center;

        border-radius: 999px;

        color: #171b2a;
        background: #c5b8da;

        font-size: 0.78rem;
        font-weight: 800;
    }

    .mouseql-step-name {
        color: #f2eee7;
        font-size: 1rem;
        font-weight: 680;
        line-height: 1.3;
    }

    .mouseql-step-details {
        color: #979eaf;
        font-size: 0.8rem;
        line-height: 1.5;
        margin-top: 0.3rem;
    }

    .mouseql-step-time {
        color: #d6c58f;
        font-size: 0.76rem;
        margin-top: 0.35rem;
    }

    .mouseql-plan-summary {
        padding:
            1rem
            1.1rem;

        margin-top: 0.9rem;

        border-radius: 15px;

        background:
            rgba(215, 195, 145, 0.06);

        border:
            1px solid
            rgba(215, 195, 145, 0.15);

        color: #cfc4a5;
        font-size: 0.84rem;
    }

    .mouseql-other-option {
        padding:
            0.9rem
            1rem;

        margin-bottom: 0.65rem;

        border-radius: 14px;

        border:
            1px solid
            rgba(184, 174, 215, 0.11);

        background:
            rgba(19, 25, 43, 0.60);
    }

    .mouseql-other-name {
        color: #ece8e1;
        font-weight: 650;
        font-size: 0.96rem;
    }

    .mouseql-other-details {
        color: #9298aa;
        font-size: 0.79rem;
        margin-top: 0.25rem;
    }

    .mouseql-unavailable {
        padding:
            1.1rem
            1.15rem;

        border-radius: 16px;

        margin:
            1.2rem
            0
            0.5rem;

        background:
            rgba(24, 43, 69, 0.68);

        border:
            1px solid
            rgba(117, 164, 214, 0.20);
    }

    .mouseql-unavailable-title {
        color: #d9e3f1;
        font-size: 0.95rem;
        font-weight: 650;
        margin-bottom: 0.3rem;
    }

    .mouseql-unavailable-copy {
        color: #9eabbc;
        font-size: 0.83rem;
        line-height: 1.5;
    }

    [data-testid="stMetric"] {
        background:
            linear-gradient(
                145deg,
                rgba(23, 30, 51, 0.92),
                rgba(18, 24, 42, 0.92)
            );

        border:
            1px solid
            rgba(184, 174, 215, 0.15);

        border-radius: 17px;

        padding:
            1rem
            1.1rem;

        box-shadow:
            0 12px 30px
            rgba(0, 0, 0, 0.13);
    }

    [data-testid="stMetricLabel"] {
        color: #979daf;
    }

    [data-testid="stMetricValue"] {
        color: #f5f1e9;
        font-weight: 680;
        letter-spacing: -0.03em;
    }

    div[data-baseweb="select"] > div {
        background:
            rgba(21, 28, 48, 0.91);

        border-color:
            rgba(184, 174, 215, 0.17);

        border-radius: 12px;
    }

    div[data-baseweb="select"] > div:hover {
        border-color:
            rgba(198, 185, 226, 0.32);
    }

    [data-baseweb="tag"] {
        border-radius: 8px;
    }

    [data-testid="stExpander"] {
        background:
            rgba(20, 27, 46, 0.65);

        border:
            1px solid
            rgba(184, 174, 215, 0.14);

        border-radius: 15px;
        overflow: hidden;
    }

    [data-testid="stAlert"] {
        border-radius: 15px;

        border:
            1px solid
            rgba(184, 174, 215, 0.13);
    }

    [data-testid="stDataFrame"] {
        border:
            1px solid
            rgba(184, 174, 215, 0.10);

        border-radius: 15px;
        overflow: hidden;
    }

    [data-testid="stPydeckChart"] {
        border-radius: 20px;
        overflow: hidden;

        border:
            1px solid
            rgba(184, 174, 215, 0.15);

        box-shadow:
            0 16px 42px
            rgba(0, 0, 0, 0.16);
    }

    @media (max-width: 700px) {
        .block-container {
            padding-top: 0.8rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .mouseql-hero {
            padding:
                1.4rem
                1.25rem
                1.35rem;

            border-radius: 20px;

            margin-bottom: 1.55rem;
        }

        .mouseql-eyebrow {
            font-size: 0.62rem;
            margin-bottom: 0.55rem;
        }

        .mouseql-title {
            font-size: 2.8rem;
        }

        .mouseql-subtitle {
            font-size: 0.9rem;
            line-height: 1.5;
            margin-top: 0.75rem;
            margin-bottom: 1rem;
        }

        .mouseql-status {
            font-size: 0.68rem;

            padding:
                0.45rem
                0.65rem;
        }

        .mouseql-section-title {
            font-size: 1.75rem;
        }

        .mouseql-best-card {
            padding: 1.3rem;
            border-radius: 18px;
        }

        .mouseql-step {
            padding:
                0.9rem
                0.9rem
                0.9rem
                3.4rem;
        }

        .mouseql-step-number {
            left: 0.85rem;
            top: 0.9rem;
        }

        [data-testid="stMetric"] {
            padding:
                0.8rem
                0.85rem;
        }
    }
    </style>
    """
)


def normalize_attraction_name(value):
    if value is None:
        return ""

    value = str(value).strip()

    while (
        len(value) >= 2
        and value[0] == '"'
        and value[-1] == '"'
    ):
        value = value[
            1:-1
        ].strip()

    return value


def normalize_wait_data(data):
    if data is None:
        return pd.DataFrame()

    if data.empty:
        return pd.DataFrame()

    required_columns = [
        "recorded_at",
        "attraction",
        "wait_minutes",
        "status",
    ]

    for column in required_columns:
        if column not in data.columns:
            data[
                column
            ] = None

    data = data[
        required_columns
    ].copy()

    data[
        "recorded_at"
    ] = pd.to_datetime(
        data[
            "recorded_at"
        ],
        utc=True,
        errors="coerce",
    )

    data[
        "wait_minutes"
    ] = pd.to_numeric(
        data[
            "wait_minutes"
        ],
        errors="coerce",
    )

    data[
        "attraction"
    ] = (
        data[
            "attraction"
        ]
        .map(
            normalize_attraction_name
        )
    )

    data[
        "status"
    ] = (
        data[
            "status"
        ]
        .fillna(
            "UNKNOWN"
        )
        .astype(str)
        .str.strip()
        .str.upper()
    )

    data = (
        data.dropna(
            subset=[
                "recorded_at",
            ]
        )
        .copy()
    )

    data = (
        data[
            data[
                "attraction"
            ]
            != ""
        ]
        .copy()
    )

    data[
        "recorded_at"
    ] = (
        data[
            "recorded_at"
        ]
        .dt.tz_convert(
            "America/New_York"
        )
    )

    return data


@st.cache_data(ttl=120)
def load_data():
    frames = []

    if DB_PATH.exists():
        try:
            conn = sqlite3.connect(
                DB_PATH
            )

            db_waits = (
                pd.read_sql_query(
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
            )

            conn.close()

            db_waits = (
                normalize_wait_data(
                    db_waits
                )
            )

            if not db_waits.empty:
                db_waits[
                    "source"
                ] = "SQLite"

                frames.append(
                    db_waits
                )

        except Exception:
            pass

    if WAITS_CSV_PATH.exists():
        try:
            csv_waits = (
                pd.read_csv(
                    WAITS_CSV_PATH
                )
            )

            csv_waits = (
                normalize_wait_data(
                    csv_waits
                )
            )

            if not csv_waits.empty:
                csv_waits[
                    "source"
                ] = "CSV"

                frames.append(
                    csv_waits
                )

        except Exception:
            pass

    if not frames:
        return pd.DataFrame(
            columns=[
                "recorded_at",
                "attraction",
                "wait_minutes",
                "status",
                "source",
            ]
        )

    waits = pd.concat(
        frames,
        ignore_index=True,
    )

    waits = (
        waits.drop_duplicates(
            subset=[
                "recorded_at",
                "attraction",
                "wait_minutes",
                "status",
            ],
            keep="last",
        )
        .sort_values(
            "recorded_at"
        )
        .reset_index(
            drop=True
        )
    )

    return waits


@st.cache_data(ttl=300)
def load_locations():
    locations = pd.read_csv(
        LOCATIONS_PATH
    )

    locations[
        "attraction"
    ] = (
        locations[
            "attraction"
        ]
        .map(
            normalize_attraction_name
        )
    )

    locations[
        "latitude"
    ] = pd.to_numeric(
        locations[
            "latitude"
        ],
        errors="coerce",
    )

    locations[
        "longitude"
    ] = pd.to_numeric(
        locations[
            "longitude"
        ],
        errors="coerce",
    )

    return locations.dropna(
        subset=[
            "latitude",
            "longitude",
        ]
    )


def select_latest_usable_snapshot(
    data
):
    if data.empty:
        return (
            pd.DataFrame(),
            None,
        )

    candidates = (
        data[
            data[
                "wait_minutes"
            ].notna()
            & (
                data[
                    "wait_minutes"
                ]
                >= 0
            )
            & (
                data[
                    "status"
                ]
                == "OPERATING"
            )
        ]
        .copy()
    )

    if candidates.empty:
        return (
            pd.DataFrame(),
            None,
        )

    snapshot_counts = (
        candidates
        .groupby(
            "recorded_at"
        )
        .size()
        .reset_index(
            name="usable_waits"
        )
        .sort_values(
            "recorded_at",
            ascending=False,
        )
    )

    healthy_snapshots = (
        snapshot_counts[
            snapshot_counts[
                "usable_waits"
            ]
            >= MIN_USABLE_WAITS_PER_SNAPSHOT
        ]
    )

    if not healthy_snapshots.empty:
        selected_timestamp = (
            healthy_snapshots.iloc[
                0
            ][
                "recorded_at"
            ]
        )

    else:
        selected_timestamp = (
            snapshot_counts.iloc[
                0
            ][
                "recorded_at"
            ]
        )

    selected_snapshot = (
        candidates[
            candidates[
                "recorded_at"
            ]
            == selected_timestamp
        ]
        .copy()
    )

    selected_snapshot = (
        selected_snapshot
        .sort_values(
            "recorded_at"
        )
        .groupby(
            "attraction",
            as_index=False,
        )
        .tail(1)
        .reset_index(
            drop=True
        )
    )

    return (
        selected_snapshot,
        selected_timestamp,
    )


def format_hour(hour):
    hour = int(
        hour
    )

    if hour == 0:
        return "12 AM"

    if hour < 12:
        return (
            f"{hour} AM"
        )

    if hour == 12:
        return "12 PM"

    return (
        f"{hour - 12} PM"
    )


def format_duration(
    minutes
):
    minutes = int(
        round(
            minutes
        )
    )

    hours = (
        minutes
        // 60
    )

    remaining = (
        minutes
        % 60
    )

    if hours == 0:
        return (
            f"{remaining} min"
        )

    if remaining == 0:
        if hours == 1:
            return "1 hr"

        return (
            f"{hours} hrs"
        )

    if hours == 1:
        return (
            f"1 hr {remaining} min"
        )

    return (
        f"{hours} hrs {remaining} min"
    )


def build_historical_waits(
    data,
    current_hour,
):
    history = (
        data.dropna(
            subset=[
                "wait_minutes"
            ]
        )
        .copy()
    )

    history[
        "hour"
    ] = (
        history[
            "recorded_at"
        ].dt.hour
    )

    history = (
        history[
            history[
                "hour"
            ]
            == current_hour
        ]
    )

    if history.empty:
        return pd.DataFrame(
            columns=[
                "attraction",
                "typical_wait",
                "observations",
            ]
        )

    return (
        history
        .groupby(
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


def render_park_map(
    locations,
    latest_waits,
    current_attraction=None,
    recommendations=None,
):
    if locations.empty:
        st.info(
            "No attraction location data available."
        )

        return

    if recommendations is None:
        recommendations = []

    map_data = (
        locations.merge(
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
        .copy()
    )

    map_data[
        "wait_display"
    ] = (
        map_data[
            "wait_minutes"
        ]
        .fillna(
            0
        )
        .astype(
            int
        )
        .astype(
            str
        )
        + " min"
    )

    map_data.loc[
        map_data[
            "wait_minutes"
        ].isna(),
        "wait_display",
    ] = (
        "No current wait"
    )

    map_data[
        "status"
    ] = (
        map_data[
            "status"
        ]
        .fillna(
            "Unknown"
        )
        .astype(
            str
        )
    )

    map_data[
        "marker_size"
    ] = 90

    map_data[
        "marker_color"
    ] = [
        [
            139,
            131,
            168,
            185,
        ]
        for _ in range(
            len(
                map_data
            )
        )
    ]

    if (
        current_attraction
        is not None
    ):
        current_mask = (
            map_data[
                "attraction"
            ]
            == current_attraction
        )

        map_data.loc[
            current_mask,
            "marker_size",
        ] = 150

        for index in (
            map_data.index[
                current_mask
            ]
        ):
            map_data.at[
                index,
                "marker_color",
            ] = [
                215,
                195,
                145,
                230,
            ]

    if recommendations:
        best_attraction = (
            recommendations[
                0
            ][
                "attraction"
            ]
        )

        best_mask = (
            map_data[
                "attraction"
            ]
            == best_attraction
        )

        map_data.loc[
            best_mask,
            "marker_size",
        ] = 180

        for index in (
            map_data.index[
                best_mask
            ]
        ):
            map_data.at[
                index,
                "marker_color",
            ] = [
                173,
                164,
                204,
                245,
            ]

    attraction_layer = (
        pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position=[
                "longitude",
                "latitude",
            ],
            get_radius=(
                "marker_size"
            ),
            get_fill_color=(
                "marker_color"
            ),
            radius_min_pixels=5,
            radius_max_pixels=14,
            pickable=True,
            auto_highlight=True,
            opacity=0.9,
            stroked=True,
            get_line_color=[
                243,
                239,
                230,
                150,
            ],
            line_width_min_pixels=1,
        )
    )

    layers = [
        attraction_layer
    ]

    if recommendations:
        best_route = (
            recommendations[
                0
            ]
        )

        path_nodes = (
            best_route.get(
                "path_nodes",
                [],
            )
        )

        if path_nodes:
            route_coordinates = (
                get_route_coordinates(
                    path_nodes
                )
            )

            if (
                len(
                    route_coordinates
                )
                >= 2
            ):
                route_data = (
                    pd.DataFrame(
                        [
                            {
                                "path":
                                    route_coordinates
                            }
                        ]
                    )
                )

                route_layer = (
                    pdk.Layer(
                        "PathLayer",
                        data=route_data,
                        get_path="path",
                        get_width=6,
                        get_color=[
                            173,
                            164,
                            204,
                            220,
                        ],
                        width_min_pixels=4,
                        pickable=False,
                    )
                )

                layers.append(
                    route_layer
                )

    view_state = (
        pdk.ViewState(
            latitude=(
                map_data[
                    "latitude"
                ].mean()
            ),
            longitude=(
                map_data[
                    "longitude"
                ].mean()
            ),
            zoom=15.5,
            pitch=0,
        )
    )

    tooltip = {
        "html": """
        <div style="
            padding: 6px;
            font-family: sans-serif;
        ">
            <div style="
                font-size: 15px;
                font-weight: 650;
                margin-bottom: 6px;
            ">
                {attraction}
            </div>

            <div>
                Current wait:
                {wait_display}
            </div>

            <div>
                Status:
                {status}
            </div>
        </div>
        """,

        "style": {
            "backgroundColor":
                "#12192B",

            "color":
                "#F3EFE6",

            "fontSize":
                "13px",

            "border":
                "1px solid #383D55",
        },
    }

    deck = (
        pdk.Deck(
            layers=layers,
            initial_view_state=(
                view_state
            ),
            tooltip=tooltip,
            map_style=None,
        )
    )

    st.pydeck_chart(
        deck,
        width="stretch",
    )

    if recommendations:
        st.caption(
            "Gold marks your current location. "
            "The larger lavender marker is "
            "MOUSEQL's best next ride."
        )

    else:
        st.caption(
            "Explore attraction locations and "
            "hover over markers for the latest "
            "available wait and status."
        )


df = load_data()
locations = load_locations()


if df.empty:
    st.warning(
        "No wait time data has been collected yet."
    )

    st.stop()


(
    latest_waits,
    live_timestamp,
) = select_latest_usable_snapshot(
    df
)


if live_timestamp is None:
    latest_timestamp = (
        df[
            "recorded_at"
        ].max()
    )

else:
    latest_timestamp = (
        live_timestamp
    )


current_hour = (
    latest_timestamp.hour
)


historical_waits = (
    build_historical_waits(
        df,
        current_hour,
    )
)


latest_data_text = (
    latest_timestamp.strftime(
        "%B %d, %Y at %I:%M %p"
    )
)


render_html(
    f"""
    <div class="mouseql-hero">
        <div class="mouseql-eyebrow">
            Magic Kingdom park intelligence
        </div>

        <div class="mouseql-title">
            MOUSEQL
        </div>

        <div class="mouseql-subtitle">
            Make your next move using current waits,
            walking distance, ride priorities, and
            historical park data.
        </div>

        <div class="mouseql-status">
            Latest usable park data · {latest_data_text}
        </div>
    </div>
    """
)


render_html(
    """
    <div class="mouseql-section">
        <div class="mouseql-kicker">
            Park planner
        </div>

        <div class="mouseql-section-title">
            Where should you go next?
        </div>

        <div class="mouseql-section-copy">
            Choose the attractions you're considering
            and how much park time you want MOUSEQL
            to plan.
        </div>
    </div>
    """
)


location_choices = sorted(
    locations[
        "attraction"
    ]
    .dropna()
    .unique()
)


recommendations = []
itinerary = []
wanted_attractions = []
current_attraction = None
priorities = {}
time_budget_minutes = 120


if location_choices:

    current_attraction = (
        st.selectbox(
            "Current location",
            location_choices,
            key="current_location",
        )
    )

    ride_choices = [
        attraction
        for attraction
        in location_choices
        if attraction
        != current_attraction
    ]

    wanted_attractions = (
        st.multiselect(
            "Attractions you're considering",
            ride_choices,
            default=[],
        )
    )

    st.caption(
        "Pick the rides you still want to do. "
        "You can add or remove them anytime."
    )

    time_budget_minutes = (
        st.slider(
            "How much time do you want to plan?",
            min_value=60,
            max_value=240,
            value=120,
            step=30,
            format="%d min",
        )
    )

    st.caption(
        "MOUSEQL will stop adding rides when "
        "the next option would push the plan "
        "past your time budget."
    )

    if wanted_attractions:

        with st.expander(
            "Ride priorities",
            expanded=False,
        ):

            st.caption(
                "Priority affects the recommendation "
                "while walking time, current waits, "
                "and historical waits are also considered."
            )

            must_do = (
                st.multiselect(
                    "Must Do",
                    wanted_attractions,
                    default=[],
                    key="must_do_rides",
                )
            )

            remaining_after_must = [
                attraction
                for attraction
                in wanted_attractions
                if attraction
                not in must_do
            ]

            want_to_do = (
                st.multiselect(
                    "Want to Do",
                    remaining_after_must,
                    default=[],
                    key="want_to_do_rides",
                )
            )

            if_theres_time = [
                attraction
                for attraction
                in wanted_attractions
                if attraction
                not in must_do
                and attraction
                not in want_to_do
            ]

            st.caption(
                "If There's Time: "
                f"{len(if_theres_time)} attractions"
            )

        priorities = {}

        for attraction in must_do:
            priorities[
                attraction
            ] = "Must Do"

        for attraction in want_to_do:
            priorities[
                attraction
            ] = "Want to Do"

        for attraction in if_theres_time:
            priorities[
                attraction
            ] = "If There's Time"

        selected_locations = (
            locations[
                locations[
                    "attraction"
                ].isin(
                    wanted_attractions
                    + [
                        current_attraction
                    ]
                )
            ]
            .copy()
        )

        selected_waits = (
            latest_waits[
                latest_waits[
                    "attraction"
                ].isin(
                    wanted_attractions
                )
            ]
            .copy()
        )

        selected_history = (
            historical_waits[
                historical_waits[
                    "attraction"
                ].isin(
                    wanted_attractions
                )
            ]
            .copy()
        )

        recommendations = (
            rank_attractions(
                current_attraction,
                selected_locations,
                selected_waits,
                selected_history,
                priorities,
            )
        )

        itinerary = (
            build_itinerary(
                current_attraction=(
                    current_attraction
                ),
                wanted_attractions=(
                    wanted_attractions
                ),
                locations=(
                    selected_locations
                ),
                latest_waits=(
                    selected_waits
                ),
                historical_waits=(
                    selected_history
                ),
                priorities=(
                    priorities
                ),
                time_budget_minutes=(
                    time_budget_minutes
                ),
            )
        )


if wanted_attractions:

    if recommendations:

        best = (
            recommendations[
                0
            ]
        )

        render_html(
            f"""
            <div class="mouseql-best-card">
                <div class="mouseql-best-label">
                    Best next ride
                </div>

                <div class="mouseql-best-name">
                    {best["attraction"]}
                </div>

                <div class="mouseql-best-total">
                    About {best["total_minutes"]} minutes
                    including the walk and current wait
                </div>
            </div>
            """
        )

        col1, col2, col3, col4 = (
            st.columns(4)
        )

        col1.metric(
            "Priority",
            best[
                "priority"
            ],
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

        if (
            best[
                "typical_wait"
            ]
            is not None
        ):
            difference = (
                best[
                    "difference"
                ]
            )

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
                comparison = (
                    "at the typical wait"
                )

            st.write(
                "The current wait is "
                f"**{comparison}** "
                f"for {format_hour(current_hour)}."
            )

            st.caption(
                "Typical wait: "
                f"{best['typical_wait']:.1f} min | "
                f"{best['observations']} observations | "
                f"{best['confidence']} confidence"
            )

        else:
            st.caption(
                "Not enough historical data "
                "for a same-hour comparison yet."
            )

        if best.get(
            "path_nodes"
        ):
            st.caption(
                "Walking route calculated "
                "using the Magic Kingdom "
                "park path network."
            )

        else:
            st.caption(
                "Walking route is currently "
                "estimated from attraction coordinates."
            )

    else:

        render_html(
            """
            <div class="mouseql-unavailable">
                <div class="mouseql-unavailable-title">
                    No usable recommendation for these rides
                </div>

                <div class="mouseql-unavailable-copy">
                    MOUSEQL found live park data, but none of
                    the selected attractions currently have
                    usable operating wait times.
                </div>
            </div>
            """
        )

else:

    st.info(
        "Choose at least one attraction above "
        "to get a recommendation."
    )


st.divider()


render_html(
    """
    <div class="mouseql-section">
        <div class="mouseql-kicker">
            Park view
        </div>

        <div class="mouseql-section-title">
            Your route through Magic Kingdom
        </div>

        <div class="mouseql-section-copy">
            See where you are, where MOUSEQL recommends
            going next, and the park-network route when
            one is available.
        </div>
    </div>
    """
)


render_park_map(
    locations=locations,
    latest_waits=latest_waits,
    current_attraction=(
        current_attraction
    ),
    recommendations=(
        recommendations
    ),
)


if itinerary:

    st.divider()

    render_html(
        f"""
        <div class="mouseql-section">
            <div class="mouseql-kicker">
                Game plan
            </div>

            <div class="mouseql-section-title">
                Your next {format_duration(time_budget_minutes)}
            </div>

            <div class="mouseql-section-copy">
                MOUSEQL recalculates each leg from the ride
                before it, so every stop becomes the starting
                point for the next decision.
            </div>
        </div>
        """
    )

    itinerary_html = (
        '<div class="mouseql-itinerary">'
    )

    for stop in itinerary:

        itinerary_html += f"""
        <div class="mouseql-step">

            <div class="mouseql-step-number">
                {stop["step"]}
            </div>

            <div class="mouseql-step-name">
                {stop["attraction"]}
            </div>

            <div class="mouseql-step-details">
                {stop["walking_minutes"]} min walk
                · {stop["wait_minutes"]} min wait
                · {stop["segment_minutes"]} min for this stop
            </div>

            <div class="mouseql-step-time">
                {stop["cumulative_minutes"]} minutes into your plan
            </div>

        </div>
        """

    itinerary_html += (
        "</div>"
    )

    render_html(
        itinerary_html
    )

    total_planned = (
        itinerary[
            -1
        ][
            "cumulative_minutes"
        ]
    )

    time_remaining = (
        max(
            0,
            time_budget_minutes
            - total_planned,
        )
    )

    rides_planned = (
        len(
            itinerary
        )
    )

    render_html(
        f"""
        <div class="mouseql-plan-summary">
            {rides_planned} rides fit into the plan
            · {total_planned} minutes scheduled
            · {time_remaining} minutes left
        </div>
        """
    )

elif wanted_attractions:

    render_html(
        """
        <div
            class="mouseql-unavailable"
            style="margin-top: 2rem;"
        >
            <div class="mouseql-unavailable-title">
                No multi-ride game plan is available yet
            </div>

            <div class="mouseql-unavailable-copy">
                MOUSEQL needs at least one selected attraction
                with a usable operating wait before it can
                build the itinerary.
            </div>
        </div>
        """
    )


if recommendations:

    st.divider()

    render_html(
        """
        <div class="mouseql-section">
            <div class="mouseql-kicker">
                Other options
            </div>

            <div class="mouseql-section-title">
                What else makes sense?
            </div>

            <div class="mouseql-section-copy">
                These rides ranked just behind your
                best next option.
            </div>
        </div>
        """
    )

    top_recommendations = (
        recommendations[
            1:6
        ]
    )

    if top_recommendations:

        for number, ride in enumerate(
            top_recommendations,
            start=2,
        ):

            details = (
                f"{ride['walking_minutes']} min walk"
                f" · {ride['wait_minutes']} min wait"
                f" · {ride['total_minutes']} min total"
            )

            if (
                ride[
                    "priority"
                ]
                != "If There's Time"
            ):
                details += (
                    " · "
                    + ride[
                        "priority"
                    ]
                )

            render_html(
                f"""
                <div class="mouseql-other-option">
                    <div class="mouseql-other-name">
                        {number}. {ride["attraction"]}
                    </div>

                    <div class="mouseql-other-details">
                        {details}
                    </div>
                </div>
                """
            )

    with st.expander(
        "View full recommendation table"
    ):

        recommendations_df = (
            pd.DataFrame(
                recommendations
            )
        )

        recommendations_df = (
            recommendations_df.rename(
                columns={
                    "attraction":
                        "Attraction",

                    "priority":
                        "Priority",

                    "walking_minutes":
                        "Walk",

                    "wait_minutes":
                        "Wait Now",

                    "typical_wait":
                        "Typical",

                    "difference":
                        "Difference",

                    "observations":
                        "History",

                    "confidence":
                        "Confidence",

                    "wait_message":
                        "Wait Status",

                    "total_minutes":
                        "Walk + Wait",

                    "routing_method":
                        "Routing",

                    "recommendation_score":
                        "Score",
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
            "Routing",
            "Walk + Wait",
        ]

        available_columns = [
            column
            for column
            in display_columns
            if column
            in recommendations_df.columns
        ]

        st.dataframe(
            recommendations_df[
                available_columns
            ],
            width="stretch",
            hide_index=True,
        )


st.divider()


render_html(
    """
    <div class="mouseql-section">
        <div class="mouseql-kicker">
            Park data
        </div>

        <div class="mouseql-section-title">
            Wait intelligence
        </div>

        <div class="mouseql-section-copy">
            Explore the history behind the recommendations
            and see how attraction waits change over time.
        </div>
    </div>
    """
)


col1, col2, col3 = (
    st.columns(3)
)


col1.metric(
    "Observations",
    f"{len(df):,}",
)


col2.metric(
    "Attractions",
    df[
        "attraction"
    ].nunique(),
)


col3.metric(
    "Overall Average Wait",
    f"{df['wait_minutes'].mean():.1f} min",
)


st.subheader(
    "Attraction Lookup"
)


attractions = sorted(
    df[
        "attraction"
    ]
    .dropna()
    .unique()
)


selected_attraction = (
    st.selectbox(
        "Choose an attraction",
        attractions,
        index=(
            attractions.index(
                "TRON Lightcycle / Run"
            )
            if
            "TRON Lightcycle / Run"
            in attractions
            else 0
        ),
    )
)


date_range = (
    st.selectbox(
        "Date range",
        [
            "Today",
            "Last 7 days",
            "Last 30 days",
            "All data",
        ],
    )
)


ride_data = (
    df[
        df[
            "attraction"
        ]
        == selected_attraction
    ]
    .dropna(
        subset=[
            "wait_minutes"
        ]
    )
    .sort_values(
        "recorded_at"
    )
    .copy()
)


if not ride_data.empty:

    today = (
        latest_timestamp.date()
    )

    if date_range == "Today":

        ride_data = (
            ride_data[
                ride_data[
                    "recorded_at"
                ].dt.date
                == today
            ]
        )

    elif (
        date_range
        == "Last 7 days"
    ):

        cutoff = (
            latest_timestamp
            - pd.Timedelta(
                days=7
            )
        )

        ride_data = (
            ride_data[
                ride_data[
                    "recorded_at"
                ]
                >= cutoff
            ]
        )

    elif (
        date_range
        == "Last 30 days"
    ):

        cutoff = (
            latest_timestamp
            - pd.Timedelta(
                days=30
            )
        )

        ride_data = (
            ride_data[
                ride_data[
                    "recorded_at"
                ]
                >= cutoff
            ]
        )


if not ride_data.empty:

    latest = (
        ride_data.iloc[
            -1
        ]
    )

    latest_wait = (
        latest[
            "wait_minutes"
        ]
    )

    average_wait = (
        ride_data[
            "wait_minutes"
        ].mean()
    )

    lowest_wait = (
        ride_data[
            "wait_minutes"
        ].min()
    )

    highest_wait = (
        ride_data[
            "wait_minutes"
        ].max()
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

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
        "in selected date range"
    )

    st.subheader(
        "Wait Time History"
    )

    history = (
        ride_data[
            [
                "recorded_at",
                "wait_minutes",
            ]
        ]
        .set_index(
            "recorded_at"
        )
    )

    st.line_chart(
        history
    )

    ride_data[
        "hour"
    ] = (
        ride_data[
            "recorded_at"
        ].dt.hour
    )

    ride_hourly = (
        ride_data
        .groupby(
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

    ride_hourly[
        "average_wait"
    ] = (
        ride_hourly[
            "average_wait"
        ].round(
            1
        )
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
        .iloc[
            0
        ]
    )

    st.write(
        "Best observed hour: "
        f"**{format_hour(best_hour['hour'])}** "
        "with an average wait of "
        f"**{best_hour['average_wait']:.1f} minutes** "
        "across "
        f"**{int(best_hour['observations'])} observations**."
    )


else:

    st.info(
        "No observations are available "
        "for this attraction during the "
        "selected date range."
    )


st.divider()


st.subheader(
    "Average Wait by Attraction"
)


attraction_summary = (
    df
    .dropna(
        subset=[
            "wait_minutes"
        ]
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


attraction_summary[
    "average_wait"
] = (
    attraction_summary[
        "average_wait"
    ].round(
        1
    )
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
    width="stretch",
    hide_index=True,
)


st.subheader(
    "Highest Average Waits"
)


top_attractions = (
    attraction_summary
    .head(
        10
    )
    .copy()
)


st.bar_chart(
    top_attractions,
    x="attraction",
    y="average_wait",
)


st.subheader(
    "Average Wait by Hour"
)


hourly = (
    df
    .dropna(
        subset=[
            "wait_minutes"
        ]
    )
    .copy()
)


hourly[
    "hour"
] = (
    hourly[
        "recorded_at"
    ].dt.hour
)


hourly_summary = (
    hourly
    .groupby(
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


hourly_summary[
    "average_wait"
] = (
    hourly_summary[
        "average_wait"
    ].round(
        1
    )
)


st.line_chart(
    hourly_summary,
    x="hour",
    y="average_wait",
)


st.subheader(
    "Latest Observations"
)


latest = (
    df
    .sort_values(
        "recorded_at",
        ascending=False,
    )
    .head(
        25
    )
    .copy()
)


latest[
    "recorded_at"
] = (
    latest[
        "recorded_at"
    ]
    .dt.strftime(
        "%B %d, %Y %I:%M %p"
    )
)


latest_display_columns = [
    "recorded_at",
    "attraction",
    "wait_minutes",
    "status",
    "source",
]


latest_display_columns = [
    column
    for column
    in latest_display_columns
    if column
    in latest.columns
]


st.dataframe(
    latest[
        latest_display_columns
    ],
    width="stretch",
    hide_index=True,
)