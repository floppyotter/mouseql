import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

URL = "https://ropedropnews.com/parks/magic-kingdom/live"
OUTPUT = Path("data/magic_kingdom_waits.csv")

with urlopen(URL) as response:
    data = json.load(response)

OUTPUT.parent.mkdir(exist_ok=True)

file_exists = OUTPUT.exists()

with OUTPUT.open("a", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)

    if not file_exists:
        writer.writerow([
            "recorded_at",
            "attraction",
            "wait_minutes",
            "status",
            "lightning_lane_cents"
        ])

    recorded_at = datetime.now().astimezone().isoformat()

    for ride in data["rides"]:
        writer.writerow([
            recorded_at,
            ride["name"],
            ride["wait"],
            ride["status"],
            ride.get("lightningLaneCents")
        ])