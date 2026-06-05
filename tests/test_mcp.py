import sqlite3
from pathlib import Path

import pytest

import app.mcp.mcp_server as srv


def _reservation(**overrides):
    base = {
        "spot_id": "A1",
        "location": "central",
        "clients_name": "John Doe",
        "car_number": "ABC123",
        "phone_number": "+1234567890",
        "start_dt": "2027-01-01 10:00",
        "end_dt": "2027-01-01 14:00",
        "price": 40.0,
    }
    base.update(overrides)
    return base


@pytest.fixture
def temp_db(tmp_path, monkeypatch):
    """A throwaway DB with a BOOKINGS table, so tests never touch the real DB."""
    db = tmp_path / "test.db"
    conn = sqlite3.connect(db)
    conn.execute(
        """CREATE TABLE BOOKINGS (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            spot_id TEXT, location TEXT, booking_type TEXT, name TEXT,
            car_number TEXT, reason TEXT, start_dt TEXT, end_dt TEXT,
            status TEXT, created_at TEXT, phone TEXT, price REAL
        )"""
    )
    conn.commit()
    conn.close()
    monkeypatch.setattr(srv, "DB_PATH", db)
    return db


# ── successful insert ───────────────────────────────────────────────────────────

def test_save_inserts_one_row(temp_db):
    srv.save_dict_as_json(_reservation())
    conn = sqlite3.connect(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM BOOKINGS").fetchone()[0]
    conn.close()
    assert count == 1

def test_save_renames_keys_and_sets_constants(temp_db):
    srv.save_dict_as_json(_reservation())
    conn = sqlite3.connect(temp_db)
    row = conn.execute(
        "SELECT name, phone, booking_type, status, price FROM BOOKINGS"
    ).fetchone()
    conn.close()
    name, phone, booking_type, status, price = row
    assert name == "John Doe"            # clients_name -> name
    assert phone == "+1234567890"        # phone_number -> phone
    assert booking_type == "reservation" # server-added constant
    assert status == "approved"          # server-added constant
    assert price == 40.0

def test_save_returns_booking_id_message(temp_db):
    msg = srv.save_dict_as_json(_reservation())
    assert "booking #" in msg
    assert msg.strip().endswith("#1")    # first row -> id 1


# ── validation ──────────────────────────────────────────────────────────────────

def test_missing_required_field_raises(temp_db):
    res = _reservation()
    del res["spot_id"]
    with pytest.raises(ValueError):
        srv.save_dict_as_json(res)

def test_empty_value_raises(temp_db):
    with pytest.raises(ValueError):
        srv.save_dict_as_json(_reservation(clients_name=""))

def test_validation_failure_writes_nothing(temp_db):
    with pytest.raises(ValueError):
        srv.save_dict_as_json(_reservation(car_number=None))
    conn = sqlite3.connect(temp_db)
    count = conn.execute("SELECT COUNT(*) FROM BOOKINGS").fetchone()[0]
    conn.close()
    assert count == 0


# ── mcp_client config ────────────────────────────────────────────────────────────

def test_client_server_path_points_to_mcp_server():
    from app.mcp.mcp_client import SERVER
    assert SERVER.endswith("mcp_server.py")
    assert Path(SERVER).is_file()

def test_client_is_multiserver_client():
    from app.mcp.mcp_client import client
    from langchain_mcp_adapters.client import MultiServerMCPClient
    assert isinstance(client, MultiServerMCPClient)
