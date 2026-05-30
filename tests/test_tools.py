import pytest
from unittest.mock import AsyncMock, patch
from app.agent.Utils.tools import price_calculator, retrieve_rag_data1, query_available_spots_tool, store_or_update_info_for_parking_proposal


# ── price_calculator ──────────────────────────────────────────────────────────

def test_price_calculator_hours_only():
    assert price_calculator.invoke({"Hours": 3, "Days": 0, "Price_Per_Hour": 2, "Price_Per_Day": 0}) == 6

def test_price_calculator_days_only():
    assert price_calculator.invoke({"Hours": 0, "Days": 2, "Price_Per_Hour": 0, "Price_Per_Day": 12}) == 24

def test_price_calculator_hours_and_days():
    assert price_calculator.invoke({"Hours": 2, "Days": 1, "Price_Per_Hour": 3, "Price_Per_Day": 20}) == 26

def test_price_calculator_zero():
    assert price_calculator.invoke({"Hours": 0, "Days": 0, "Price_Per_Hour": 0, "Price_Per_Day": 0}) == 0

def test_price_calculator_negative_hours_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": -1, "Days": 0, "Price_Per_Hour": 2, "Price_Per_Day": 0})

def test_price_calculator_negative_days_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": 0, "Days": -1, "Price_Per_Hour": 0, "Price_Per_Day": 12})

def test_price_calculator_negative_price_per_hour_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": 2, "Days": 0, "Price_Per_Hour": -1, "Price_Per_Day": 0})

def test_price_calculator_negative_price_per_day_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": 0, "Days": 1, "Price_Per_Hour": 0, "Price_Per_Day": -5})

def test_price_calculator_hours_without_rate_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": 3, "Days": 0, "Price_Per_Hour": 0, "Price_Per_Day": 0})

def test_price_calculator_fractional_rate():
    assert price_calculator.invoke({"Hours": 3, "Days": 0, "Price_Per_Hour": 2.5, "Price_Per_Day": 0}) == pytest.approx(7.5)

def test_price_calculator_fractional_hours_and_days():
    assert price_calculator.invoke({"Hours": 1, "Days": 1, "Price_Per_Hour": 2.5, "Price_Per_Day": 12.5}) == pytest.approx(15.0)

def test_price_calculator_days_without_rate_raises():
    with pytest.raises(Exception):
        price_calculator.invoke({"Hours": 0, "Days": 2, "Price_Per_Hour": 0, "Price_Per_Day": 0})


# ── retrieve_rag_data1 ────────────────────────────────────────────────────────

def test_retrieve_rag_returns_string():
    with patch("app.agent.Utils.tools.retrieve", return_value=["chunk1", "chunk2"]):
        result = retrieve_rag_data1.invoke({"query": "parking hours"})
    assert isinstance(result, str)
    assert "chunk1" in result

def test_retrieve_rag_calls_retrieve_with_query():
    with patch("app.agent.Utils.tools.retrieve") as mock_retrieve:
        mock_retrieve.return_value = []
        retrieve_rag_data1.invoke({"query": "test query"})
        mock_retrieve.assert_called_once_with("test query", top_k=3)


# ── query_available_spots_tool ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_query_available_spots_returns_string():
    with patch("app.agent.Utils.tools.query_available_spots", new=AsyncMock(return_value=["A1", "A2"])):
        result = await query_available_spots_tool.ainvoke({
            "location": "central",
            "start_time": "2026-06-20 10:00",
            "end_time": "2026-06-20 14:00",
            "parking_spot_type": "A",
        })
    assert "A1" in result
    assert "A2" in result

@pytest.mark.asyncio
async def test_query_available_spots_empty():
    with patch("app.agent.Utils.tools.query_available_spots", new=AsyncMock(return_value=[])):
        result = await query_available_spots_tool.ainvoke({
            "location": "east",
            "start_time": "2026-06-20 10:00",
            "end_time": "2026-06-20 14:00",
            "parking_spot_type": "T",
        })
    assert "[]" in result


# ── store_or_update_info_for_parking_proposal ─────────────────────────────────

@pytest.mark.asyncio
async def test_store_reservation_returns_string():
    result = await store_or_update_info_for_parking_proposal.ainvoke({
        "spot_id": "A1", "location": "central", "clients_name": "John Doe",
        "car_number": "ABC123", "phone_number": "+1234567890",
        "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
        "price": 50,
    })
    assert isinstance(result, str)

@pytest.mark.asyncio
async def test_store_reservation_contains_fields():
    result = await store_or_update_info_for_parking_proposal.ainvoke({
        "spot_id": "B2", "location": "east", "clients_name": "Jane Smith",
        "car_number": "XYZ999", "phone_number": "+9876543210",
        "start_dt": "2027-06-21 09:00", "end_dt": "2027-06-21 11:00",
        "price": 30,
    })
    assert "Jane Smith" in result
    assert "XYZ999" in result
    assert "east" in result
    assert "+9876543210" in result
    assert "30" in result

@pytest.mark.asyncio
async def test_store_reservation_empty_name_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
            "price": 50,
        })

@pytest.mark.asyncio
async def test_store_reservation_empty_car_number_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "", "phone_number": "+1234567890",
            "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
            "price": 50,
        })

@pytest.mark.asyncio
async def test_store_reservation_empty_phone_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "",
            "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
            "price": 50,
        })

@pytest.mark.asyncio
async def test_store_reservation_fractional_price():
    result = await store_or_update_info_for_parking_proposal.ainvoke({
        "spot_id": "A1", "location": "central", "clients_name": "John Doe",
        "car_number": "ABC123", "phone_number": "+1234567890",
        "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
        "price": 7.5,
    })
    assert "7.5" in result

@pytest.mark.asyncio
async def test_store_reservation_zero_price_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
            "price": 0,
        })

@pytest.mark.asyncio
async def test_store_reservation_negative_price_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "2027-06-20 10:00", "end_dt": "2027-06-20 14:00",
            "price": -10,
        })

@pytest.mark.asyncio
async def test_store_reservation_invalid_date_format_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "20-06-2026", "end_dt": "2027-06-20 14:00",
            "price": 50,
        })

@pytest.mark.asyncio
async def test_store_reservation_end_before_start_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "2027-06-20 14:00", "end_dt": "2027-06-20 10:00",
            "price": 50,
        })

@pytest.mark.asyncio
async def test_store_reservation_past_date_raises():
    with pytest.raises(Exception):
        await store_or_update_info_for_parking_proposal.ainvoke({
            "spot_id": "A1", "location": "central", "clients_name": "John Doe",
            "car_number": "ABC123", "phone_number": "+1234567890",
            "start_dt": "2020-01-01 10:00", "end_dt": "2020-01-01 14:00",
            "price": 50,
        })
