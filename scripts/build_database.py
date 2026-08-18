import csv
import sqlite3
from pathlib import Path

DATA_FILE = Path("data/magic_kingdom_waits.csv")
DATABASE_FILE = Path("data/mouseql.db")


def build_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Rebuild the table from the latest CSV
    cursor.execute("DROP TABLE IF EXISTS wait_times")

    cursor.execute("""
        CREATE TABLE wait_times (
            recorded_at TEXT NOT NULL,
            attraction TEXT NOT NULL,
            wait_minutes INTEGER,
            status TEXT,
            lightning_lane_cents INTEGER
        )
    """)

    with DATA_FILE.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        rows = [
            (
                row["recorded_at"],
                row["attraction"],
                row["wait_minutes"] or None,
                row["status"],
                row["lightning_lane_cents"] or None
            )
            for row in reader
        ]

    cursor.executemany("""
        INSERT INTO wait_times (
            recorded_at,
            attraction,
            wait_minutes,
            status,
            lightning_lane_cents
        )
        VALUES (?, ?, ?, ?, ?)
    """, rows)

    conn.commit()
    conn.close()

    print(f"Loaded {len(rows)} wait-time records into {DATABASE_FILE}")


if __name__ == "__main__":
    build_database()