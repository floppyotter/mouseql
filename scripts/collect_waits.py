import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen


URL = "https://ropedropnews.com/parks/magic-kingdom/live"

WAITS_OUTPUT = Path("data/magic_kingdom_waits.csv")
LOCATIONS_OUTPUT = Path("data/attraction_locations.csv")


with urlopen(URL) as response:
    data = json.load(response)


WAITS_OUTPUT.parent.mkdir(exist_ok=True)

recorded_at = datetime.now().astimezone().isoformat()


# Save wait-time history

wait_file_exists = WAITS_OUTPUT.exists()

with WAITS_OUTPUT.open("a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    if not wait_file_exists:
        writer.writerow([
            "recorded_at",
            "attraction",
            "wait_minutes",
            "status",
            "lightning_lane_cents"
        ])

    for ride in data["rides"]:
        writer.writerow([
            recorded_at,
            ride["name"],
            ride["wait"],
            ride["status"],
            ride.get("lightningLaneCents")
        ])


# Save attraction locations

with LOCATIONS_OUTPUT.open("w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    writer.writerow([
        "attraction",
        "latitude",
        "longitude"
    ])

    for ride in data["rides"]:
        latitude = ride.get("lat")
        longitude = ride.get("lon")

        if latitude is not None and longitude is not None:
            writer.writerow([
                ride["name"],
                latitude,
                longitude
            ])


print(f"Wait times saved to {WAITS_OUTPUT}")
print(f"Attraction locations saved to {LOCATIONS_OUTPUT}")
