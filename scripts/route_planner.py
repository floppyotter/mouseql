from math import radians, sin, cos, sqrt, atan2, isfinite
from pathlib import Path
import heapq

import pandas as pd


WALKING_SPEED_MPH = 3.0

# The path network already represents actual walkable segments,
# so we use a smaller adjustment than the old straight-line model.
WALKING_DISTANCE_MULTIPLIER = 1.05

MIN_HISTORY_OBSERVATIONS = 5
FULL_HISTORY_OBSERVATIONS = 20
MAX_HISTORY_ADJUSTMENT = 10

PRIORITY_ADJUSTMENTS = {
    "Must Do": -15,
    "Want to Do": -7,
    "If There's Time": 0,
}


DATA_DIR = Path(__file__).resolve().parent.parent / "data"

PATHS_FILE = DATA_DIR / "park_paths.csv"
NODES_FILE = DATA_DIR / "attraction_nodes.csv"


# --------------------------------------------------
# Old distance calculation
# Used as a fallback if an attraction cannot be
# connected to the park routing network.
# --------------------------------------------------

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


# --------------------------------------------------
# Walking time
# --------------------------------------------------

def estimate_walking_time(distance_miles):
    """
    Convert walking distance into estimated minutes.
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


# --------------------------------------------------
# Load park routing network
# --------------------------------------------------

def load_park_paths():
    """
    Load the modeled Magic Kingdom walkway network.

    Returns a dictionary where each node contains
    connected nodes and their distances.
    """

    if not PATHS_FILE.exists():
        return {}

    try:
        paths = pd.read_csv(PATHS_FILE)
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

        from_node = str(
            row["from_node"]
        ).strip()

        to_node = str(
            row["to_node"]
        ).strip()

        try:
            distance = float(
                row["distance_miles"]
            )
        except (TypeError, ValueError):
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

        # Walking paths work both directions.
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
    """
    Load attraction -> park node relationships.
    """

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

        attraction = str(
            row["attraction"]
        ).strip()

        node = str(
            row["node"]
        ).strip()

        if not attraction or not node:
            continue

        attraction_nodes[
            attraction
        ] = node

    return attraction_nodes


# Load once when the module is imported.
PARK_GRAPH = load_park_paths()
ATTRACTION_NODES = load_attraction_nodes()


# --------------------------------------------------
# Shortest path
# --------------------------------------------------

def find_shortest_path(
    start_node,
    end_node,
):
    """
    Find the shortest walking path between two
    nodes using Dijkstra's algorithm.

    Returns:

        distance_miles
        path_nodes

    or:

        None
    """

    if not PARK_GRAPH:
        return None

    if start_node not in PARK_GRAPH:
        return None

    if end_node not in PARK_GRAPH:
        return None

    if start_node == end_node:
        return 0.0, [start_node]

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

        visited.add(current_node)

        if current_node == end_node:
            break

        for neighbor, edge_distance in (
            PARK_GRAPH.get(
                current_node,
                [],
            )
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

                distances[neighbor] = (
                    new_distance
                )

                previous[neighbor] = (
                    current_node
                )

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

        path.append(current)

        if current not in previous:
            return None

        current = previous[current]

    path.append(start_node)

    path.reverse()

    return (
        distances[end_node],
        path,
    )


# --------------------------------------------------
# Attraction-to-attraction routing
# --------------------------------------------------

def calculate_walking_route(
    current_attraction,
    target_attraction,
    locations,
):
    """
    Calculate a walking route between two attractions.

    First attempts to use the modeled park network.

    Falls back to coordinate-based distance if either
    attraction is not connected to the network.
    """

    start_node = ATTRACTION_NODES.get(
        current_attraction
    )

    end_node = ATTRACTION_NODES.get(
        target_attraction
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

            distance_miles, path_nodes = route

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


    # --------------------------------------------------
    # Fallback
    # --------------------------------------------------

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

    except (TypeError, ValueError):
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


# --------------------------------------------------
# History confidence
# --------------------------------------------------

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


# --------------------------------------------------
# Recommendation engine
# --------------------------------------------------

def rank_attractions(
    current_attraction,
    locations,
    latest_waits,
    historical_waits=None,
    priorities=None,
):
    """
    Rank attractions using:

    - park-network walking distance
    - current wait
    - historical wait performance
    - user priority
    """

    if priorities is None:
        priorities = {}

    if not current_attraction:
        return []

    if locations.empty:
        return []

    current_location = locations[
        locations["attraction"]
        == current_attraction
    ]

    if current_location.empty:
        return []

    results = []

    for _, location in locations.iterrows():

        attraction = location[
            "attraction"
        ]

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
        except (TypeError, ValueError):
            continue

        if not isfinite(
            wait_minutes
        ):
            continue

        if wait_minutes < 0:
            continue

        # ------------------------------------------
        # Walking route
        # ------------------------------------------

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

        # ------------------------------------------
        # Historical wait
        # ------------------------------------------

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

        # ------------------------------------------
        # Priority
        # ------------------------------------------

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

        # ------------------------------------------
        # Score
        # ------------------------------------------

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

                "routing_method": (
                    routing_method
                ),
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
