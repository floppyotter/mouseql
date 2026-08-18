from math import radians, sin, cos, sqrt, atan2, isfinite
from pathlib import Path
import heapq

import pandas as pd


WALKING_SPEED_MPH = 3.0
WALKING_DISTANCE_MULTIPLIER = 1.05

MIN_HISTORY_OBSERVATIONS = 5
FULL_HISTORY_OBSERVATIONS = 20
MAX_HISTORY_ADJUSTMENT = 10

PRIORITY_ADJUSTMENTS = {
    "Must Do": -15,
    "Want to Do": -7,
    "If There's Time": 0,
}


DATA_DIR = (
    Path(__file__).resolve().parent.parent / "data"
)

PATHS_FILE = DATA_DIR / "park_paths.csv"
NODES_FILE = DATA_DIR / "attraction_nodes.csv"
PARK_NODES_FILE = DATA_DIR / "park_nodes.csv"


def clean_name(value):
    if value is None:
        return ""

    return str(value).strip().strip('"').strip("'")


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2,
):
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
    walking_distance = (
        distance_miles
        * WALKING_DISTANCE_MULTIPLIER
    )

    walking_hours = (
        walking_distance
        / WALKING_SPEED_MPH
    )

    return walking_hours * 60


def load_park_paths():
    if not PATHS_FILE.exists():
        return {}

    try:
        paths = pd.read_csv(
            PATHS_FILE
        )
    except Exception:
        return {}

    required_columns = {
        "from_node",
        "to_node",
        "distance_miles",
    }

    if not required_columns.issubset(
        paths.columns
    ):
        return {}

    graph = {}

    for _, row in paths.iterrows():

        from_node = clean_name(
            row["from_node"]
        )

        to_node = clean_name(
            row["to_node"]
        )

        try:
            distance = float(
                row["distance_miles"]
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if (
            not from_node
            or not to_node
            or not isfinite(distance)
            or distance <= 0
        ):
            continue

        graph.setdefault(
            from_node,
            [],
        ).append(
            (
                to_node,
                distance,
            )
        )

        graph.setdefault(
            to_node,
            [],
        ).append(
            (
                from_node,
                distance,
            )
        )

    return graph


def load_attraction_nodes():
    if not NODES_FILE.exists():
        return {}

    try:
        nodes = pd.read_csv(
            NODES_FILE
        )
    except Exception:
        return {}

    required_columns = {
        "attraction",
        "node",
    }

    if not required_columns.issubset(
        nodes.columns
    ):
        return {}

    attraction_nodes = {}

    for _, row in nodes.iterrows():

        attraction = clean_name(
            row["attraction"]
        )

        node = clean_name(
            row["node"]
        )

        if not attraction or not node:
            continue

        attraction_nodes[
            attraction
        ] = node

    return attraction_nodes


def load_park_nodes():
    if not PARK_NODES_FILE.exists():
        return {}

    try:
        nodes = pd.read_csv(
            PARK_NODES_FILE
        )
    except Exception:
        return {}

    required_columns = {
        "node",
        "latitude",
        "longitude",
    }

    if not required_columns.issubset(
        nodes.columns
    ):
        return {}

    park_nodes = {}

    for _, row in nodes.iterrows():

        node = clean_name(
            row["node"]
        )

        try:
            latitude = float(
                row["latitude"]
            )

            longitude = float(
                row["longitude"]
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if not (
            isfinite(latitude)
            and isfinite(longitude)
        ):
            continue

        park_nodes[node] = {
            "latitude": latitude,
            "longitude": longitude,
        }

    return park_nodes


PARK_GRAPH = load_park_paths()
ATTRACTION_NODES = load_attraction_nodes()
PARK_NODES = load_park_nodes()


def get_route_coordinates(
    path_nodes
):
    coordinates = []

    for node in path_nodes:

        node = clean_name(node)

        location = PARK_NODES.get(
            node
        )

        if location is None:
            continue

        coordinates.append(
            [
                location["longitude"],
                location["latitude"],
            ]
        )

    return coordinates


def find_shortest_path(
    start_node,
    end_node,
):
    if not PARK_GRAPH:
        return None

    start_node = clean_name(
        start_node
    )

    end_node = clean_name(
        end_node
    )

    if start_node not in PARK_GRAPH:
        return None

    if end_node not in PARK_GRAPH:
        return None

    if start_node == end_node:
        return (
            0.0,
            [start_node],
        )

    distances = {
        start_node: 0.0
    }

    previous = {}

    queue = [
        (
            0.0,
            start_node,
        )
    ]

    visited = set()

    while queue:

        current_distance, current_node = (
            heapq.heappop(queue)
        )

        if current_node in visited:
            continue

        visited.add(
            current_node
        )

        if current_node == end_node:
            break

        for (
            neighbor,
            edge_distance,
        ) in PARK_GRAPH.get(
            current_node,
            [],
        ):

            new_distance = (
                current_distance
                + edge_distance
            )

            if (
                neighbor not in distances
                or new_distance
                < distances[neighbor]
            ):

                distances[
                    neighbor
                ] = new_distance

                previous[
                    neighbor
                ] = current_node

                heapq.heappush(
                    queue,
                    (
                        new_distance,
                        neighbor,
                    ),
                )

    if end_node not in distances:
        return None

    path = []

    current = end_node

    while current != start_node:

        path.append(
            current
        )

        if current not in previous:
            return None

        current = previous[
            current
        ]

    path.append(
        start_node
    )

    path.reverse()

    return (
        distances[end_node],
        path,
    )


def calculate_walking_route(
    current_attraction,
    target_attraction,
    locations,
):
    current_attraction = clean_name(
        current_attraction
    )

    target_attraction = clean_name(
        target_attraction
    )

    start_node = (
        ATTRACTION_NODES.get(
            current_attraction
        )
    )

    end_node = (
        ATTRACTION_NODES.get(
            target_attraction
        )
    )

    if (
        start_node
        and end_node
    ):

        route = find_shortest_path(
            start_node,
            end_node,
        )

        if route is not None:

            distance_miles, path_nodes = (
                route
            )

            walking_minutes = (
                estimate_walking_time(
                    distance_miles
                )
            )

            return {
                "distance_miles": distance_miles,
                "walking_minutes": walking_minutes,
                "path_nodes": path_nodes,
                "routing_method": "Park path",
            }

    current_location = locations[
        locations["attraction"]
        == current_attraction
    ]

    target_location = locations[
        locations["attraction"]
        == target_attraction
    ]

    if (
        current_location.empty
        or target_location.empty
    ):
        return None

    current_location = (
        current_location.iloc[0]
    )

    target_location = (
        target_location.iloc[0]
    )

    try:
        current_lat = float(
            current_location["latitude"]
        )

        current_lon = float(
            current_location["longitude"]
        )

        target_lat = float(
            target_location["latitude"]
        )

        target_lon = float(
            target_location["longitude"]
        )

    except (
        TypeError,
        ValueError,
    ):
        return None

    if not (
        isfinite(current_lat)
        and isfinite(current_lon)
        and isfinite(target_lat)
        and isfinite(target_lon)
    ):
        return None

    distance = calculate_distance(
        current_lat,
        current_lon,
        target_lat,
        target_lon,
    )

    walking_minutes = (
        estimate_walking_time(
            distance
        )
    )

    return {
        "distance_miles": distance,
        "walking_minutes": walking_minutes,
        "path_nodes": [],
        "routing_method": "Coordinate estimate",
    }


def get_history_confidence(
    observations
):
    if observations < MIN_HISTORY_OBSERVATIONS:
        return "Low"

    if observations < FULL_HISTORY_OBSERVATIONS:
        return "Medium"

    return "High"


def get_history_weight(
    observations
):
    if observations < MIN_HISTORY_OBSERVATIONS:
        return 0.0

    if observations >= FULL_HISTORY_OBSERVATIONS:
        return 1.0

    return (
        observations
        - MIN_HISTORY_OBSERVATIONS
    ) / (
        FULL_HISTORY_OBSERVATIONS
        - MIN_HISTORY_OBSERVATIONS
    )


def get_wait_message(
    difference
):
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
    priorities=None,
):
    if priorities is None:
        priorities = {}

    if not current_attraction:
        return []

    if locations.empty:
        return []

    current_attraction = clean_name(
        current_attraction
    )

    current_location = locations[
        locations["attraction"]
        == current_attraction
    ]

    if current_location.empty:
        return []

    results = []

    for _, location in (
        locations.iterrows()
    ):

        attraction = clean_name(
            location["attraction"]
        )

        if attraction == current_attraction:
            continue

        wait_row = latest_waits[
            latest_waits["attraction"]
            == attraction
        ]

        if wait_row.empty:
            continue

        wait_minutes = (
            wait_row.iloc[0][
                "wait_minutes"
            ]
        )

        try:
            wait_minutes = float(
                wait_minutes
            )
        except (
            TypeError,
            ValueError,
        ):
            continue

        if not isfinite(
            wait_minutes
        ):
            continue

        if wait_minutes < 0:
            continue

        route = calculate_walking_route(
            current_attraction,
            attraction,
            locations,
        )

        if route is None:
            continue

        distance = route[
            "distance_miles"
        ]

        walking_minutes = route[
            "walking_minutes"
        ]

        path_nodes = route[
            "path_nodes"
        ]

        routing_method = route[
            "routing_method"
        ]

        typical_wait = None
        difference = None
        observations = 0
        confidence = "Low"
        wait_message = (
            "Not enough history"
        )

        history_adjustment = 0.0

        if (
            historical_waits is not None
            and not historical_waits.empty
        ):

            history_row = (
                historical_waits[
                    historical_waits[
                        "attraction"
                    ]
                    == attraction
                ]
            )

            if not history_row.empty:

                history_row = (
                    history_row.iloc[0]
                )

                try:
                    typical_wait = float(
                        history_row[
                            "typical_wait"
                        ]
                    )

                    observations = int(
                        history_row[
                            "observations"
                        ]
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    typical_wait = None
                    observations = 0

                if (
                    typical_wait is not None
                    and isfinite(
                        typical_wait
                    )
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

        priority = priorities.get(
            attraction,
            "If There's Time",
        )

        priority_adjustment = (
            PRIORITY_ADJUSTMENTS.get(
                priority,
                0,
            )
        )

        base_total = (
            walking_minutes
            + wait_minutes
        )

        recommendation_score = (
            base_total
            + history_adjustment
            + priority_adjustment
        )

        results.append(
            {
                "attraction": attraction,
                "priority": priority,
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
                    round(
                        typical_wait,
                        1,
                    )
                    if typical_wait
                    is not None
                    else None
                ),
                "difference": (
                    round(
                        difference,
                        1,
                    )
                    if difference
                    is not None
                    else None
                ),
                "observations": observations,
                "confidence": confidence,
                "wait_message": wait_message,
                "total_minutes": round(
                    base_total
                ),
                "history_adjustment": round(
                    history_adjustment,
                    1,
                ),
                "priority_adjustment": (
                    priority_adjustment
                ),
                "recommendation_score": round(
                    recommendation_score,
                    1,
                ),
                "path_nodes": path_nodes,
                "routing_method": routing_method,
            }
        )

    results.sort(
        key=lambda item: (
            item[
                "recommendation_score"
            ],
            item[
                "walking_minutes"
            ],
        )
    )

    return results
