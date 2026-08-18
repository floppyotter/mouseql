from math import radians, sin, cos, sqrt, atan2

# Average walking speed in miles per hour
WALKING_SPEED_MPH = 3.0

# Approximate multiplier because people cannot walk
# in a perfectly straight line through the park
WALKING_DISTANCE_MULTIPLIER = 1.25


def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate straight-line distance between two points
    using the Haversine formula.

    Returns distance in miles.
    """

    earth_radius_miles = 3958.8

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

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
        distance_miles * WALKING_DISTANCE_MULTIPLIER
    )

    walking_hours = (
        walking_distance / WALKING_SPEED_MPH
    )

    return walking_hours * 60


def rank_attractions(
    current_attraction,
    locations,
    latest_waits,
):
    """
    Rank attractions based on estimated walking time
    plus the latest posted wait.
    """

    current_location = locations[
        locations["attraction"] == current_attraction
    ]

    if current_location.empty:
        return []

    current_location = current_location.iloc[0]

    current_lat = float(
        current_location["latitude"]
    )

    current_lon = float(
        current_location["longitude"]
    )

    results = []

    for _, location in locations.iterrows():

        attraction = location["attraction"]

        if attraction == current_attraction:
            continue

        wait_row = latest_waits[
            latest_waits["attraction"] == attraction
        ]

        if wait_row.empty:
            continue

        wait_minutes = wait_row.iloc[0]["wait_minutes"]

        if wait_minutes is None:
            continue

        try:
            wait_minutes = float(wait_minutes)
        except (TypeError, ValueError):
            continue

        target_lat = float(
            location["latitude"]
        )

        target_lon = float(
            location["longitude"]
        )

        distance = calculate_distance(
            current_lat,
            current_lon,
            target_lat,
            target_lon,
        )

        walking_minutes = estimate_walking_time(
            distance
        )

        total_minutes = (
            walking_minutes + wait_minutes
        )

        results.append(
            {
                "attraction": attraction,
                "distance_miles": round(
                    distance, 2
                ),
                "walking_minutes": round(
                    walking_minutes
                ),
                "wait_minutes": round(
                    wait_minutes
                ),
                "total_minutes": round(
                    total_minutes
                ),
            }
        )

    results.sort(
        key=lambda item: item["total_minutes"]
    )

    return results
