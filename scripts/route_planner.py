from functools import lru_cache
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
    Path(__file__)
    .resolve()
    .parent
    .parent
    / "data"
)

PATHS_FILE = (
    DATA_DIR
    / "park_paths.csv"
)

NODES_FILE = (
    DATA_DIR
    / "attraction_nodes.csv"
)

PARK_NODES_FILE = (
    DATA_DIR
    / "park_nodes.csv"
)


def clean_name(value):
    if value is None:
        return ""

    value = str(value).strip()

    while (
        len(value) >= 2
        and value[0] == value[-1]
        and value[0] in {'"', "'"}
    ):
        value = value[1:-1].strip()

    return value


def normalize_key(value):
    return clean_name(
        value
    ).casefold()


def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2,
):
    earth_radius_miles = 3958.8

    lat1 = radians(
        float(lat1)
    )

    lon1 = radians(
        float(lon1)
    )

    lat2 = radians(
        float(lat2)
    )

    lon2 = radians(
        float(lon2)
    )

    lat_difference = (
        lat2 - lat1
    )

    lon_difference = (
        lon2 - lon1
    )

    a = (
        sin(
            lat_difference / 2
        ) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(
            lon_difference / 2
        ) ** 2
    )

    c = (
        2
        * atan2(
            sqrt(a),
            sqrt(1 - a),
        )
    )

    return (
        earth_radius_miles
        * c
    )


def estimate_walking_time(
    distance_miles,
):
    walking_distance = (
        distance_miles
        * WALKING_DISTANCE_MULTIPLIER
    )

    walking_hours = (
        walking_distance
        / WALKING_SPEED_MPH
    )

    return (
        walking_hours
        * 60
    )


@lru_cache(maxsize=1)
def get_park_graph():
    graph = {}

    if not PATHS_FILE.exists():
        return graph

    try:
        paths = pd.read_csv(
            PATHS_FILE
        )
    except Exception:
        return graph

    required_columns = {
        "from_node",
        "to_node",
        "distance_miles",
    }

    if not required_columns.issubset(
        paths.columns
    ):
        return graph

    for _, row in paths.iterrows():
        from_node = clean_name(
            row[
                "from_node"
            ]
        )

        to_node = clean_name(
            row[
                "to_node"
            ]
        )

        try:
            distance = float(
                row[
                    "distance_miles"
                ]
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


@lru_cache(maxsize=1)
def get_attraction_nodes():
    attraction_nodes = {}

    if not NODES_FILE.exists():
        return attraction_nodes

    try:
        nodes = pd.read_csv(
            NODES_FILE
        )
    except Exception:
        return attraction_nodes

    required_columns = {
        "attraction",
        "node",
    }

    if not required_columns.issubset(
        nodes.columns
    ):
        return attraction_nodes

    for _, row in nodes.iterrows():
        attraction = clean_name(
            row[
                "attraction"
            ]
        )

        node = clean_name(
            row[
                "node"
            ]
        )

        if (
            not attraction
            or not node
        ):
            continue

        attraction_nodes[
            normalize_key(
                attraction
            )
        ] = node

    return attraction_nodes


@lru_cache(maxsize=1)
def get_park_nodes():
    park_nodes = {}

    if not PARK_NODES_FILE.exists():
        return park_nodes

    try:
        nodes = pd.read_csv(
            PARK_NODES_FILE
        )
    except Exception:
        return park_nodes

    required_columns = {
        "node",
        "latitude",
        "longitude",
    }

    if not required_columns.issubset(
        nodes.columns
    ):
        return park_nodes

    for _, row in nodes.iterrows():
        node = clean_name(
            row[
                "node"
            ]
        )

        try:
            latitude = float(
                row[
                    "latitude"
                ]
            )

            longitude = float(
                row[
                    "longitude"
                ]
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

        park_nodes[
            node
        ] = {
            "latitude":
                latitude,

            "longitude":
                longitude,
        }

    return park_nodes


def clear_routing_cache():
    get_park_graph.cache_clear()
    get_attraction_nodes.cache_clear()
    get_park_nodes.cache_clear()


def get_route_coordinates(
    path_nodes,
):
    park_nodes = (
        get_park_nodes()
    )

    coordinates = []

    for node in path_nodes:
        node = clean_name(
            node
        )

        location = (
            park_nodes.get(
                node
            )
        )

        if location is None:
            continue

        coordinates.append(
            [
                location[
                    "longitude"
                ],
                location[
                    "latitude"
                ],
            ]
        )

    return coordinates


def find_attraction_node(
    attraction,
):
    attraction_nodes = (
        get_attraction_nodes()
    )

    return (
        attraction_nodes.get(
            normalize_key(
                attraction
            )
        )
    )


def find_shortest_path(
    start_node,
    end_node,
):
    graph = (
        get_park_graph()
    )

    if not graph:
        return None

    start_node = clean_name(
        start_node
    )

    end_node = clean_name(
        end_node
    )

    if (
        start_node
        not in graph
        or end_node
        not in graph
    ):
        return None

    if (
        start_node
        == end_node
    ):
        return (
            0.0,
            [
                start_node
            ],
        )

    distances = {
        start_node:
            0.0
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
        (
            current_distance,
            current_node,
        ) = heapq.heappop(
            queue
        )

        if (
            current_node
            in visited
        ):
            continue

        visited.add(
            current_node
        )

        if (
            current_node
            == end_node
        ):
            break

        for (
            neighbor,
            edge_distance,
        ) in graph.get(
            current_node,
            [],
        ):
            new_distance = (
                current_distance
                + edge_distance
            )

            if (
                neighbor
                not in distances
                or new_distance
                < distances[
                    neighbor
                ]
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

    if (
        end_node
        not in distances
    ):
        return None

    path = []

    current = end_node

    while (
        current
        != start_node
    ):
        path.append(
            current
        )

        if (
            current
            not in previous
        ):
            return None

        current = (
            previous[
                current
            ]
        )

    path.append(
        start_node
    )

    path.reverse()

    return (
        distances[
            end_node
        ],
        path,
    )


def get_routing_diagnostics(
    current_attraction,
    target_attraction,
):
    graph = (
        get_park_graph()
    )

    attraction_nodes = (
        get_attraction_nodes()
    )

    park_nodes = (
        get_park_nodes()
    )

    current_clean = clean_name(
        current_attraction
    )

    target_clean = clean_name(
        target_attraction
    )

    current_key = normalize_key(
        current_clean
    )

    target_key = normalize_key(
        target_clean
    )

    start_node = (
        attraction_nodes.get(
            current_key
        )
    )

    end_node = (
        attraction_nodes.get(
            target_key
        )
    )

    route = None

    if (
        start_node
        and end_node
    ):
        route = (
            find_shortest_path(
                start_node,
                end_node,
            )
        )

    if route is not None:
        (
            distance_miles,
            path_nodes,
        ) = route

        walking_minutes = (
            estimate_walking_time(
                distance_miles
            )
        )

    else:
        distance_miles = None
        path_nodes = []
        walking_minutes = None

    return {
        "data_directory":
            str(
                DATA_DIR
            ),

        "park_paths_file":
            str(
                PATHS_FILE
            ),

        "park_paths_exists":
            PATHS_FILE.exists(),

        "attraction_nodes_file":
            str(
                NODES_FILE
            ),

        "attraction_nodes_exists":
            NODES_FILE.exists(),

        "park_nodes_file":
            str(
                PARK_NODES_FILE
            ),

        "park_nodes_exists":
            PARK_NODES_FILE.exists(),

        "graph_nodes_loaded":
            len(
                graph
            ),

        "attraction_mappings_loaded":
            len(
                attraction_nodes
            ),

        "park_node_coordinates_loaded":
            len(
                park_nodes
            ),

        "current_attraction":
            current_clean,

        "current_normalized":
            current_key,

        "target_attraction":
            target_clean,

        "target_normalized":
            target_key,

        "start_node":
            start_node,

        "end_node":
            end_node,

        "start_node_in_graph":
            (
                start_node in graph
                if start_node
                else False
            ),

        "end_node_in_graph":
            (
                end_node in graph
                if end_node
                else False
            ),

        "route_found":
            route is not None,

        "path_nodes":
            path_nodes,

        "distance_miles":
            (
                round(
                    distance_miles,
                    3,
                )
                if distance_miles
                is not None
                else None
            ),

        "walking_minutes":
            (
                round(
                    walking_minutes,
                    1,
                )
                if walking_minutes
                is not None
                else None
            ),
    }


def calculate_coordinate_route(
    current_attraction,
    target_attraction,
    locations,
):
    if locations.empty:
        return None

    location_names = (
        locations[
            "attraction"
        ]
        .astype(str)
        .map(
            normalize_key
        )
    )

    current_location = (
        locations[
            location_names
            == normalize_key(
                current_attraction
            )
        ]
    )

    target_location = (
        locations[
            location_names
            == normalize_key(
                target_attraction
            )
        ]
    )

    if (
        current_location.empty
        or target_location.empty
    ):
        return None

    current_location = (
        current_location.iloc[
            0
        ]
    )

    target_location = (
        target_location.iloc[
            0
        ]
    )

    try:
        current_lat = float(
            current_location[
                "latitude"
            ]
        )

        current_lon = float(
            current_location[
                "longitude"
            ]
        )

        target_lat = float(
            target_location[
                "latitude"
            ]
        )

        target_lon = float(
            target_location[
                "longitude"
            ]
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

    distance = (
        calculate_distance(
            current_lat,
            current_lon,
            target_lat,
            target_lon,
        )
    )

    walking_minutes = (
        estimate_walking_time(
            distance
        )
    )

    return {
        "distance_miles":
            distance,

        "walking_minutes":
            walking_minutes,

        "path_nodes":
            [],

        "routing_method":
            "Coordinate estimate",

        "start_node":
            None,

        "end_node":
            None,
    }


def calculate_walking_route(
    current_attraction,
    target_attraction,
    locations,
):
    current_attraction = (
        clean_name(
            current_attraction
        )
    )

    target_attraction = (
        clean_name(
            target_attraction
        )
    )

    start_node = (
        find_attraction_node(
            current_attraction
        )
    )

    end_node = (
        find_attraction_node(
            target_attraction
        )
    )

    if (
        start_node
        and end_node
    ):
        route = (
            find_shortest_path(
                start_node,
                end_node,
            )
        )

        if route is not None:
            (
                distance_miles,
                path_nodes,
            ) = route

            walking_minutes = (
                estimate_walking_time(
                    distance_miles
                )
            )

            return {
                "distance_miles":
                    distance_miles,

                "walking_minutes":
                    walking_minutes,

                "path_nodes":
                    path_nodes,

                "routing_method":
                    "Park path",

                "start_node":
                    start_node,

                "end_node":
                    end_node,
            }

    return (
        calculate_coordinate_route(
            current_attraction,
            target_attraction,
            locations,
        )
    )


def get_history_confidence(
    observations,
):
    if (
        observations
        < MIN_HISTORY_OBSERVATIONS
    ):
        return "Low"

    if (
        observations
        < FULL_HISTORY_OBSERVATIONS
    ):
        return "Medium"

    return "High"


def get_history_weight(
    observations,
):
    if (
        observations
        < MIN_HISTORY_OBSERVATIONS
    ):
        return 0.0

    if (
        observations
        >= FULL_HISTORY_OBSERVATIONS
    ):
        return 1.0

    return (
        observations
        - MIN_HISTORY_OBSERVATIONS
    ) / (
        FULL_HISTORY_OBSERVATIONS
        - MIN_HISTORY_OBSERVATIONS
    )


def get_wait_message(
    difference,
):
    if difference <= -10:
        return (
            "Much lower than typical"
        )

    if difference <= -5:
        return (
            "Lower than typical"
        )

    if difference >= 10:
        return (
            "Much higher than typical"
        )

    if difference >= 5:
        return (
            "Higher than typical"
        )

    return (
        "Near typical"
    )


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

    current_attraction = (
        clean_name(
            current_attraction
        )
    )

    current_key = (
        normalize_key(
            current_attraction
        )
    )

    location_names = (
        locations[
            "attraction"
        ]
        .astype(str)
        .map(
            normalize_key
        )
    )

    current_location = (
        locations[
            location_names
            == current_key
        ]
    )

    if current_location.empty:
        return []

    wait_names = (
        latest_waits[
            "attraction"
        ]
        .astype(str)
        .map(
            normalize_key
        )
    )

    if (
        historical_waits
        is not None
        and not historical_waits.empty
    ):
        history_names = (
            historical_waits[
                "attraction"
            ]
            .astype(str)
            .map(
                normalize_key
            )
        )
    else:
        history_names = None

    normalized_priorities = {
        normalize_key(
            attraction
        ):
        priority

        for (
            attraction,
            priority,
        )
        in priorities.items()
    }

    results = []

    for _, location in (
        locations.iterrows()
    ):
        attraction = clean_name(
            location[
                "attraction"
            ]
        )

        attraction_key = (
            normalize_key(
                attraction
            )
        )

        if (
            attraction_key
            == current_key
        ):
            continue

        wait_row = (
            latest_waits[
                wait_names
                == attraction_key
            ]
        )

        if wait_row.empty:
            continue

        wait_minutes = (
            wait_row.iloc[
                0
            ][
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

        route = (
            calculate_walking_route(
                current_attraction,
                attraction,
                locations,
            )
        )

        if route is None:
            continue

        distance = (
            route[
                "distance_miles"
            ]
        )

        walking_minutes = (
            route[
                "walking_minutes"
            ]
        )

        typical_wait = None
        difference = None
        observations = 0
        confidence = "Low"

        wait_message = (
            "Not enough history"
        )

        history_adjustment = 0.0

        if (
            historical_waits
            is not None
            and not historical_waits.empty
            and history_names is not None
        ):
            history_row = (
                historical_waits[
                    history_names
                    == attraction_key
                ]
            )

            if not history_row.empty:
                history_row = (
                    history_row.iloc[
                        0
                    ]
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
                    typical_wait
                    is not None
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

                    history_adjustment = (
                        max(
                            -MAX_HISTORY_ADJUSTMENT,
                            min(
                                MAX_HISTORY_ADJUSTMENT,
                                raw_adjustment,
                            ),
                        )
                    )

        priority = (
            normalized_priorities.get(
                attraction_key,
                "If There's Time",
            )
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
                "attraction":
                    attraction,

                "priority":
                    priority,

                "distance_miles":
                    round(
                        distance,
                        2,
                    ),

                "walking_minutes":
                    round(
                        walking_minutes
                    ),

                "wait_minutes":
                    round(
                        wait_minutes
                    ),

                "typical_wait":
                    (
                        round(
                            typical_wait,
                            1,
                        )
                        if typical_wait
                        is not None
                        else None
                    ),

                "difference":
                    (
                        round(
                            difference,
                            1,
                        )
                        if difference
                        is not None
                        else None
                    ),

                "observations":
                    observations,

                "confidence":
                    confidence,

                "wait_message":
                    wait_message,

                "total_minutes":
                    round(
                        base_total
                    ),

                "history_adjustment":
                    round(
                        history_adjustment,
                        1,
                    ),

                "priority_adjustment":
                    priority_adjustment,

                "recommendation_score":
                    round(
                        recommendation_score,
                        1,
                    ),

                "path_nodes":
                    route[
                        "path_nodes"
                    ],

                "routing_method":
                    route[
                        "routing_method"
                    ],

                "start_node":
                    route.get(
                        "start_node"
                    ),

                "end_node":
                    route.get(
                        "end_node"
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