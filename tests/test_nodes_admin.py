import pytest
from typing import cast
from unittest.mock import MagicMock, patch, AsyncMock

from langchain_core.messages import AIMessage, ToolMessage, RemoveMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agent.Utils.state import MessagesState
from app.agent.Utils.nodes_admin import (
    init_node,
    approval_node,
    should_continue,
    tool_node_adm,
)


def ms(d: dict) -> MessagesState:
    return cast(MessagesState, d)


RESERVATION = {"clients_name": "John Doe", "car_number": "ABC123",
               "start_dt": "2027-01-01 10:00", "end_dt": "2027-01-01 14:00"}


# ── init_node ─────────────────────────────────────────────────────────────────

def test_init_node_sets_is_admin():
    result = init_node(ms({"messages": []}))
    assert result["is_admin"] is True

def test_init_node_clears_message_admin():
    result = init_node(ms({"messages": []}))
    msg = result["message_admin"][0]
    assert isinstance(msg, RemoveMessage)
    assert msg.id == REMOVE_ALL_MESSAGES


# ── should_continue (admin) ─────────────────────────────────────────────────────

def test_should_continue_routes_to_tool_node_when_tool_calls():
    last = AIMessage(content="")
    last.tool_calls = [MagicMock()]
    assert should_continue(ms({"message_admin": [last], "llm_calls": 1})) == "tool_node_adm"

def test_should_continue_ends_when_no_tool_calls():
    last = AIMessage(content="Reservation approved.")
    assert should_continue(ms({"message_admin": [last], "llm_calls": 1})) == END

def test_should_continue_ends_at_call_limit():
    last = AIMessage(content="")
    last.tool_calls = [MagicMock()]
    assert should_continue(ms({"message_admin": [last], "llm_calls": 10})) == END


# ── Human-in-the-loop: interrupt / resume ───────────────────────────────────────
# A minimal graph (init -> approval -> END) exercises the interrupt and the
# decision handling without involving the LLM or the MCP server.

def _hitl_graph():
    b = StateGraph(MessagesState)
    b.add_node("init_node", init_node)
    b.add_node("approval_node", approval_node)
    b.add_edge(START, "init_node")
    b.add_edge("init_node", "approval_node")
    b.add_edge("approval_node", END)
    return b.compile(checkpointer=InMemorySaver())


@pytest.mark.asyncio
async def test_approval_node_interrupts_with_reservation():
    graph = _hitl_graph()
    config = {"configurable": {"thread_id": "hitl-pause"}}
    result = await graph.ainvoke({"messages": [], "proposed_reservation": RESERVATION}, config=config)
    assert "__interrupt__" in result
    # the admin is shown the reservation they must decide on
    assert "John Doe" in str(result["__interrupt__"][0].value)


@pytest.mark.asyncio
async def test_approval_node_approved_sets_status_and_reservation():
    graph = _hitl_graph()
    config = {"configurable": {"thread_id": "hitl-approve"}}
    await graph.ainvoke({"messages": [], "proposed_reservation": RESERVATION}, config=config)
    result = await graph.ainvoke(Command(resume={"decision": "approved", "reason": ""}), config=config)
    assert result["reservation_status"] == "approved"
    assert result["approved_reservation"] == RESERVATION


@pytest.mark.asyncio
async def test_approval_node_rejected_clears_approved_reservation():
    graph = _hitl_graph()
    config = {"configurable": {"thread_id": "hitl-reject"}}
    await graph.ainvoke({"messages": [], "proposed_reservation": RESERVATION}, config=config)
    result = await graph.ainvoke(
        Command(resume={"decision": "rejected", "reason": "name looks wrong"}), config=config)
    assert result["reservation_status"] == "rejected"
    assert result["approved_reservation"] is None


# ── tool_node_adm: approved-only save guard ─────────────────────────────────────
# _ensure_tools is mocked so no real MCP subprocess is spawned.

def _save_call():
    last = AIMessage(content="")
    last.tool_calls = [{"name": "Dictionary_saver",
                        "args": {"reservation": RESERVATION}, "id": "tc1"}]
    return last


@pytest.mark.asyncio
async def test_tool_node_adm_handles_tool_error_gracefully():
    fake_tool = AsyncMock()
    fake_tool.ainvoke.side_effect = RuntimeError("boom")
    fake = AsyncMock(return_value=(MagicMock(), {"Dictionary_saver": fake_tool}))
    with patch("app.agent.Utils.nodes_admin._ensure_tools", new=fake):
        result = await tool_node_adm(ms({"message_admin": [_save_call()],
                                         "reservation_status": "approved"}))
    msg = result["message_admin"][0]
    assert isinstance(msg, ToolMessage)
    assert "Tool error" in msg.content


@pytest.mark.asyncio
async def test_tool_node_adm_saves_when_approved():
    fake_tool = AsyncMock()
    fake_tool.ainvoke.return_value = "Reservation saved"
    fake = AsyncMock(return_value=(MagicMock(), {"Dictionary_saver": fake_tool}))
    with patch("app.agent.Utils.nodes_admin._ensure_tools", new=fake):
        result = await tool_node_adm(ms({"message_admin": [_save_call()],
                                         "reservation_status": "approved"}))
    fake_tool.ainvoke.assert_awaited_once()
    assert isinstance(result["message_admin"][0], ToolMessage)
