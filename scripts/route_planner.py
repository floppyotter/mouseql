from math import radians, sin, cos, sqrt, atan2, isfinite

# Average walking speed in miles per hour
WALKING_SPEED_MPH = 3.0

# Temporary adjustment because park walking
# is not a perfect straight line
WALKING_DISTANCE_MULTIPLIER = 1.25

# Historical data needs at least this many observations
# before it starts affecting the recommendation score
MIN_HISTORY_OBSERVATIONS = 5

# Once we have this many observations, history gets full weight
FULL_HISTORY_OBSERVATIONS = 20

# Maximum number of minutes that historical performance
# can change the recommendation score
MAX_HISTORY_ADJUSTMENT = 10


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate straight-line distance between two points.

    Returns distance in miles.
    """

    earth_radius_miles = 3958.8

    lat1 = radians(float(lat1))
    lon1 = radians(float(lon1))
    lat2 = radians(float(lat2))
    lon2 = radians(float(lon2))

    lat_difference = lat2 - lat1
    lon_difference = lon2 - lon1

    a = (
        sin(lat_difference / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(lon_difference / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a),
    )

    return earth_radius_miles * c


def estimate_walking_time(distance_miles):
    """
    Convert distance in miles to estimated walking minutes.
    """

    walking_distance = (
        distance_miles
        * WALKING_DISTANCE_MULTIPLIER
    )

    walking_hours = (
        walking_distance
        / WALKING_SPEED_MPH
    )

    return walking_hours * 60


def get_history_confidence(observations):
    """
    Return a simple confidence label based on the
    number of historical observations available.
    """

    if observations < MIN_HISTORY_OBSERVATIONS:
        return "Low"

    if observations < FULL_HISTORY_OBSERVATIONS:
        return "Medium"

    return "High"


def get_history_weight(observations):
    """
    Return how strongly historical data should affect
    the recommendation.

    Very small samples receive no weight.
    """

    if observations < MIN_HISTORY_OBSERVATIONS:
        return 0.0

    if observations >= FULL_HISTORY_OBSERVATIONS:
        return 1.0

    return (
        observations - MIN_HISTORY_OBSERVATIONS
    ) / (
        FULL_HISTORY_OBSERVATIONS
        - MIN_HISTORY_OBSERVATIONS
    )


def get_wait_message(difference):
    """
    Turn the current-vs-typical difference into
    something readable in the dashboard.
    """

    if difference <= -10:
        return "Much lower than typical"

    if difference <= -5:
        return "Lower than typical"

    if difference >= 10:
        return "Much higher than typical"

    if difference >= 5:
        return "Higher than typical"

    return "Near typical"


def rank_attractions(
    current_attraction,
    locations,
    latest_waits,
    historical_waits=None,
):
    """
    Rank attractions using:

    - estimated walking time
    - latest posted wait
    - historical wait for the same hour

    Historical data only affects the score when
    enough observations are available.
    """

    current_location = locations[
        locations["attraction"]
        == current_attraction
    ]

    if current_location.empty:
        return []

    current_location = current_location.iloc[0]

    try:
        current_lat = float(
            current_location["latitude"]
        )

        current_lon = float(
            current_location["longitude"]
        )

    except (TypeError, ValueError):
        return []

    if not (
        isfinite(current_lat)
        and isfinite(current_lon)
    ):
        return []

    results = []

    for _, location in locations.iterrows():

        attraction = location["attraction"]

        if attraction == current_attraction:
            continue

        wait_row = latest_waits[
            latest_waits["attraction"]
            == attraction
        ]

        if wait_row.empty:
            continue

        wait_minutes = (
            wait_row.iloc[0]["wait_minutes"]
        )

        try:
            wait_minutes = float(
                wait_minutes
            )

        except (TypeError, ValueError):
            continue

        if not isfinite(wait_minutes):
            continue

        if wait_minutes < 0:
            continue

        try:
            target_lat = float(
                location["latitude"]
            )

            target_lon = float(
                location["longitude"]
            )

        except (TypeError, ValueError):
            continue

        if not (
            isfinite(target_lat)
            and isfinite(target_lon)
        ):
            continue

        distance = calculate_distance(
            current_lat,
            current_lon,
            target_lat,
            target_lon,
        )

        walking_minutes = estimate_walking_time(
            distance
        )

        typical_wait = None
        difference = None
        observations = 0
        confidence = "Low"
        wait_message = "Not enough history"
        history_adjustment = 0.0

        if (
            historical_waits is not None
            and not historical_waits.empty
        ):

            history_row = historical_waits[
                historical_waits["attraction"]
                == attraction
            ]

            if not history_row.empty:

                history_row = history_row.iloc[0]

                try:
                    typical_wait = float(
                        history_row["typical_wait"]
                    )

                    observations = int(
                        history_row["observations"]
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    typical_wait = None
                    observations = 0

                if (
                    typical_wait is not None
                    and isfinite(typical_wait)
                ):

                    difference = (
                        wait_minutes
                        - typical_wait
                    )

                    confidence = (
                        get_history_confidence(
                            observations
                        )
                    )

                    wait_message = (
                        get_wait_message(
                            difference
                        )
                    )

                    history_weight = (
                        get_history_weight(
                            observations
                        )
                    )

                    # Positive difference means the ride
                    # is currently worse than typical.
                    #
                    # Negative difference means it is
                    # currently better than typical.
                    raw_adjustment = (
                        difference
                        * history_weight
                    )

                    history_adjustment = max(
                        -MAX_HISTORY_ADJUSTMENT,
                        min(
                            MAX_HISTORY_ADJUSTMENT,
                            raw_adjustment,
                        ),
                    )

        base_total = (
            walking_minutes
            + wait_minutes
        )

        recommendation_score = (
            base_total
            + history_adjustment
        )

        results.append(
            {
                "attraction": attraction,

                "distance_miles": round(
                    distance,
                    2,
                ),

                "walking_minutes": round(
                    walking_minutes
                ),

                "wait_minutes": round(
                    wait_minutes
                ),

                "typical_wait": (
                    round(typical_wait, 1)
                    if typical_wait is not None
                    else None
                ),

                "difference": (
                    round(difference, 1)
                    if difference is not None
                    else None
                ),

                "observations": observations,

                "confidence": confidence,

                "wait_message": wait_message,

                "total_minutes": round(
                    base_total
                ),

                "recommendation_score": round(
                    recommendation_score,
                    1,
                ),
            }
        )

    results.sort(
        key=lambda item: (
            item["recommendation_score"],
            item["walking_minutes"],
        )
    )

    return results
