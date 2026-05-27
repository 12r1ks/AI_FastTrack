import pytest
from unittest.mock import AsyncMock, patch
from app.agent.Utils.tools import price_calculator, retrieve_rag_data1, query_available_spots_tool


# ── price_calculator ──────────────────────────────────────────────────────────

def test_price_calculator_hours_only():
    assert price_calculator.invoke({"Hours": 3, "Days": 0}) == 15

def test_price_calculator_days_only():
    assert price_calculator.invoke({"Hours": 0, "Days": 2}) == 40

def test_price_calculator_hours_and_days():
    assert price_calculator.invoke({"Hours": 2, "Days": 1}) == 30

def test_price_calculator_zero():
    assert price_calculator.invoke({"Hours": 0, "Days": 0}) == 0


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
        mock_retrieve.assert_called_once_with("test query", top_k=2)


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
