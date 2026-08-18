import pandas as pd

from route_planner import (
    clean_name,
    rank_attractions,
)


def build_itinerary(
    current_attraction,
    wanted_attractions,
    locations,
    latest_waits,
    historical_waits=None,
    priorities=None,
    time_budget_minutes=120,
):
    if priorities is None:
        priorities = {}

    try:
        time_budget_minutes = int(
            time_budget_minutes
        )
    except (TypeError, ValueError):
        return []

    if time_budget_minutes <= 0:
        return []

    if not current_attraction:
        return []

    if not wanted_attractions:
        return []

    remaining = [
        clean_name(attraction)
        for attraction in wanted_attractions
        if clean_name(attraction)
        != clean_name(current_attraction)
    ]

    current_location = clean_name(
        current_attraction
    )

    elapsed_minutes = 0
    itinerary = []
    step_number = 1

    while remaining:
        selected_names = set(
            remaining
            + [current_location]
        )

        location_mask = (
            locations["attraction"]
            .astype(str)
            .map(clean_name)
            .isin(selected_names)
        )

        selected_locations = (
            locations[
                location_mask
            ].copy()
        )

        wait_mask = (
            latest_waits["attraction"]
            .astype(str)
            .map(clean_name)
            .isin(remaining)
        )

        selected_waits = (
            latest_waits[
                wait_mask
            ].copy()
        )

        if (
            historical_waits
            is not None
            and not historical_waits.empty
        ):
            history_mask = (
                historical_waits[
                    "attraction"
                ]
                .astype(str)
                .map(clean_name)
                .isin(remaining)
            )

            selected_history = (
                historical_waits[
                    history_mask
                ].copy()
            )
        else:
            selected_history = (
                pd.DataFrame()
            )

        rankings = rank_attractions(
            current_location,
            selected_locations,
            selected_waits,
            selected_history,
            priorities,
        )

        if not rankings:
            break

        remaining_time = (
            time_budget_minutes
            - elapsed_minutes
        )

        chosen = None

        for candidate in rankings:
            candidate_time = int(
                candidate[
                    "total_minutes"
                ]
            )

            if (
                candidate_time
                <= remaining_time
            ):
                chosen = candidate
                break

        if chosen is None:
            break

        segment_minutes = int(
            chosen[
                "total_minutes"
            ]
        )

        arrival_elapsed = (
            elapsed_minutes
            + int(
                chosen[
                    "walking_minutes"
                ]
            )
        )

        elapsed_minutes += (
            segment_minutes
        )

        itinerary.append(
            {
                "step":
                    step_number,

                "from_attraction":
                    current_location,

                "attraction":
                    chosen[
                        "attraction"
                    ],

                "priority":
                    chosen[
                        "priority"
                    ],

                "walking_minutes":
                    chosen[
                        "walking_minutes"
                    ],

                "wait_minutes":
                    chosen[
                        "wait_minutes"
                    ],

                "segment_minutes":
                    segment_minutes,

                "arrival_elapsed_minutes":
                    arrival_elapsed,

                "cumulative_minutes":
                    elapsed_minutes,

                "time_remaining_minutes":
                    max(
                        0,
                        time_budget_minutes
                        - elapsed_minutes,
                    ),

                "typical_wait":
                    chosen[
                        "typical_wait"
                    ],

                "difference":
                    chosen[
                        "difference"
                    ],

                "confidence":
                    chosen[
                        "confidence"
                    ],

                "wait_message":
                    chosen[
                        "wait_message"
                    ],

                "distance_miles":
                    chosen[
                        "distance_miles"
                    ],

                "path_nodes":
                    chosen[
                        "path_nodes"
                    ],

                "routing_method":
                    chosen[
                        "routing_method"
                    ],

                "recommendation_score":
                    chosen[
                        "recommendation_score"
                    ],
            }
        )

        current_location = (
            chosen[
                "attraction"
            ]
        )

        remaining = [
            attraction
            for attraction
            in remaining
            if attraction
            != current_location
        ]

        step_number += 1

    return itinerary