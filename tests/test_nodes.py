import pytest
from typing import cast
from unittest.mock import MagicMock, patch, AsyncMock
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from app.agent.Utils.state import MessagesState

from app.agent.Utils.nodes import (
    guard_route,
    reject_node,
    tool_node,
    should_continue,
    pre_end_guard,
    init_node,
    _mask_phone,
)

def ms(d: dict) -> MessagesState:
    return cast(MessagesState, d)


# ── init_node ─────────────────────────────────────────────────────────────────

def test_init_node_resets_llm_calls():
    result = init_node(ms({"messages": [], "llm_calls": 5}))
    assert result == {"llm_calls": 0}

def test_init_node_sets_llm_calls_when_missing():
    result = init_node(ms({"messages": []}))
    assert result == {"llm_calls": 0}


# ── guard_route ───────────────────────────────────────────────────────────────

def test_guard_route_returns_llm_call_for_parking():
    mock_result = MagicMock()
    mock_result.route = "llm_call"

    with patch("app.agent.Utils.nodes.model") as mock_model:
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_result
        mock_model.with_structured_output.return_value = mock_structured

        result = guard_route(ms({"messages": [HumanMessage(content="What are the parking hours?")]}))

    assert result == "llm_call"

def test_guard_route_returns_reject_for_offtopic():
    mock_result = MagicMock()
    mock_result.route = "reject"

    with patch("app.agent.Utils.nodes.model") as mock_model:
        mock_structured = MagicMock()
        mock_structured.invoke.return_value = mock_result
        mock_model.with_structured_output.return_value = mock_structured

        result = guard_route(ms({"messages": [HumanMessage(content="What is the weather today?")]}))

    assert result == "reject"


# ── reject_node ───────────────────────────────────────────────────────────────

def test_reject_node_returns_message():
    result = reject_node(ms({"messages": [HumanMessage(content="tell me a joke")]}))
    assert "messages" in result
    assert isinstance(result["messages"][0], AIMessage)

def test_reject_node_message_mentions_parking():
    result = reject_node(ms({"messages": []}))
    assert "parking" in result["messages"][0].content.lower()


# ── should_continue ───────────────────────────────────────────────────────────

def test_should_continue_routes_to_tool_node_when_tool_calls():
    last = AIMessage(content="")
    last.tool_calls = [MagicMock()]
    assert should_continue(ms({"messages": [last], "llm_calls": 1})) == "tool_node"

def test_should_continue_routes_to_pre_end_guard_when_no_tool_calls():
    last = AIMessage(content="Here is your answer.")
    assert should_continue(ms({"messages": [last], "llm_calls": 1})) == "pre_end_guard"

def test_should_continue_routes_to_pre_end_guard_at_limit():
    last = AIMessage(content="")
    last.tool_calls = [MagicMock()]
    assert should_continue(ms({"messages": [last], "llm_calls": 10})) == "pre_end_guard"

def test_should_continue_still_routes_to_tool_node_below_limit():
    last = AIMessage(content="")
    last.tool_calls = [MagicMock()]
    assert should_continue(ms({"messages": [last], "llm_calls": 9})) == "tool_node"


# ── tool_node ─────────────────────────────────────────────────name────────────

@pytest.mark.asyncio
async def test_tool_node_returns_tool_message():
    tool_call = {"name": "Price_Calculator", "args": {"Hours": 2, "Days": 0}, "id": "tc1"}
    last = AIMessage(content="")
    last.tool_calls = [tool_call]

    with patch("app.agent.Utils.nodes.tools_by_name") as mock_tools:
        mock_tool = AsyncMock()
        mock_tool.ainvoke.return_value = "10"
        mock_tools.__getitem__.return_value = mock_tool
        result = await tool_node(ms({"messages": [last]}))

    assert any(isinstance(m, ToolMessage) for m in result["messages"])

@pytest.mark.asyncio
async def test_tool_node_handles_tool_error_gracefully():
    tool_call = {"name": "Price_Calculator", "args": {"Hours": -1, "Days": 0}, "id": "tc2"}
    last = AIMessage(content="")
    last.tool_calls = [tool_call]

    with patch("app.agent.Utils.nodes.tools_by_name") as mock_tools:
        mock_tool = AsyncMock()
        mock_tool.ainvoke.side_effect = ValueError("Hours and Days must be non-negative")
        mock_tools.__getitem__.return_value = mock_tool
        result = await tool_node(ms({"messages": [last]}))

    msg = result["messages"][0]
    assert isinstance(msg, ToolMessage)
    assert "Tool error" in msg.content

@pytest.mark.asyncio
async def test_tool_node_updates_proposed_reservation():
    args = {
        "spot_id": "A1", "location": "central", "clients_name": "John",
        "car_number": "ABC123", "phone_number": "+1234567890",
        "start_dt": "2027-01-01 10:00", "end_dt": "2027-01-01 14:00",
        "price": 50,
    }
    tool_call = {"name": "store_or_update_info_for_parking_proposal", "args": args, "id": "tc3"}
    last = AIMessage(content="")
    last.tool_calls = [tool_call]

    with patch("app.agent.Utils.nodes.tools_by_name") as mock_tools:
        mock_tool = AsyncMock()
        mock_tool.ainvoke.return_value = str(args)
        mock_tools.__getitem__.return_value = mock_tool
        result = await tool_node(ms({"messages": [last]}))

    assert result.get("proposed_reservation") == args


# ── pre_end_guard ─────────────────────────────────────────────────────────────

def test_pre_end_guard_masks_phone_number():
    last = AIMessage(content="Call us at +375293267600 for info.", id="msg1")
    result = pre_end_guard(ms({"messages": [last]}))
    content = result["messages"][0].content
    assert "+375293267600" not in content
    assert "*" in content

def test_pre_end_guard_leaves_dates_unchanged():
    last = AIMessage(content="Reservation from 2026-06-28 18:00 to 2026-06-29 18:00", id="msg2")
    result = pre_end_guard(ms({"messages": [last]}))
    assert result == {}

@pytest.mark.parametrize("date_str", [
    "2026 06 01",
    "01 06 2026",
    "01-06-2026",
    "2026/06/01",
    "01.06.2026",
])
def test_pre_end_guard_leaves_various_date_formats_unchanged(date_str):
    last = AIMessage(content=f"Your booking date is {date_str}.", id="msg_date")
    result = pre_end_guard(ms({"messages": [last]}))
    assert result == {}

def test_pre_end_guard_no_change_preserves_content():
    last = AIMessage(content="No phone numbers here.", id="msg3")
    result = pre_end_guard(ms({"messages": [last]}))
    assert result == {}


# ── _mask_phone ───────────────────────────────────────────────────────────────

def test_mask_phone_long_number():
    match = MagicMock()
    match.group.return_value = "+375293267600"
    result = _mask_phone(match)
    assert result.startswith("+37")
    assert "*" in result
    assert result.endswith("7600")

def test_mask_phone_short_number():
    match = MagicMock()
    match.group.return_value = "1234567"
    result = _mask_phone(match)
    assert result.endswith("7")
    assert "*" in result
