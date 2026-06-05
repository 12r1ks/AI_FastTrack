from fastmcp import FastMCP
from pathlib import Path
import sqlite3
from datetime import datetime

mcp = FastMCP("reservation_saver")
DB_PATH = Path(__file__).resolve().parent.parent / "db" / "Dynamic_SQLite_DB.db"

REQUIRED = ("spot_id", "location", "name", "car_number",
            "phone", "start_dt", "end_dt", "price")


@mcp.tool("Dictionary_saver",
          description="Save a confirmed parking reservation to the bookings database.")
def save_dict_as_json(reservation: dict) -> str:

    dict_db = {"clients_name": "name", "phone_number": "phone"}   # reservation key -> column
    reservation_keys_changed = {dict_db.get(k, k): v for k, v in reservation.items()}

    for key in REQUIRED:
        if key not in reservation_keys_changed:
            raise ValueError(f"{key} is missing. reservation must contain {key}")

    for key, value in reservation.items():
        if value in ("", None):
            raise ValueError(f"{key} is empty. {key} must contain data")

    row = reservation_keys_changed
    row["booking_type"] = "reservation"
    row["reason"]       = None
    row["status"]       = "approved"
    row["created_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.execute(
            """INSERT INTO BOOKINGS
                (spot_id, location, booking_type, name, car_number, reason,
                 start_dt, end_dt, status, created_at, phone, price)
                VALUES (:spot_id, :location, :booking_type, :name, :car_number, :reason,
                        :start_dt, :end_dt, :status, :created_at, :phone, :price)""",
            row,
        )
        conn.commit()
        booking_id = cur.lastrowid
    finally:
        conn.close()

    return f"Reservation saved as booking #{booking_id}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
