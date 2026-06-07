from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, RemoveMessage, AIMessage
from app.agent.Utils.state import MessagesState
from app.agent.Utils.tools import get_llm
from langgraph.types import interrupt
from app.mcp.mcp_client import client
from langgraph.graph import END
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from typing_extensions import Literal

model = get_llm()

#───MCP_TOOL─────────────────────────────────────────────────────────────────
# MCP tools are loaded lazily on first use (NOT at import).
_tools_by_name = None
_model_with_tools = None

async def _ensure_tools():
    global _tools_by_name, _model_with_tools
    if _model_with_tools is None:
        tools = await client.get_tools()
        _tools_by_name = {t.name: t for t in tools}
        _model_with_tools = model.bind_tools(tools)
    return _model_with_tools, _tools_by_name

def init_node(state: MessagesState) -> dict:
    return {"is_admin": True, "message_admin": [RemoveMessage(id=REMOVE_ALL_MESSAGES)]}

#───Human in the loop────────────────────────────────────────────────────────
# Made as an interrupt from chatbot agent to subagent (takes admin input)
def approval_node(state: MessagesState):
    
    approval = interrupt("Do you approve this action?\n"
                         f"Proposed reservation details: {state.get('proposed_reservation')}\n "
                         "Specify reason if you reject, if you approve just press 'approved'. ")
    
    #example = {"decision": "rejected", "reason": "Something wrong with a name. ask for more details"}

    return {"message_admin": [HumanMessage(content="Reservation "
                                            f"{state.get('proposed_reservation')} "
                                            f"was {approval['decision']}.\n"
                                            f"{'Comment from admin: ' + approval['reason'] if approval['reason'] else ''}")],
            "reservation_status": approval['decision'],
            "approved_reservation": state.get('proposed_reservation') if approval['decision']=="approved" else None}

#───Central Admin Subagent Node───────────────────────────────────────────────
# Calling an agent to decide: calling a tool if approved (to store data),
# Communicate with a main Chatbot Agent on admin review results
async def llm_call_admin(state: MessagesState) -> MessagesState:

        model_with_tools, _ = await _ensure_tools()
        answer = await model_with_tools.ainvoke(
                    [
                        SystemMessage(
                            content=(
                                f"## Role\n"
                                " You are an administrator for handling parking reservations and saving approved in the system.\n\n"
                                "## Goals\n"
                                "- Handle reservation review and aproval status from an administrator\n" \
                                "- Save approved resrvation by using Dictionary_saver tool\n"
                                "- If not ask administrator for a reason, if they didnt mention any\n"
                                "- Provide short summary for chat bot who speaks with a client.\n"
                                "- Save reservation to Json (by using a tool) if its approve\n"
                                "- If no information provided, just say so, but state rejection.\n"
                                "- If you get error from the tool return request to chatbot agent to verify info. \n\n"
                                "## Current Session State\n"
                                f"Proposed reservation: {state.get('proposed_reservation') or 'None yet'}\n"
                                f"Reservation status: {state.get('reservation_status') or 'No reservation submitted'}\n"
                            )        
                        )
                    ] + state.get("message_admin", []))
        out = {"message_admin": [answer], "llm_calls": state.get("llm_calls", 0)+ 1}
        
        if not getattr(answer, "tool_calls", None):
             out["messages"] = [AIMessage(content=f"Message from the Administrator agent: {answer.content}")]
        
        return out

#───Tool Node───────────────────────────────────────────────
# Handles tool using by agent
async def tool_node_adm(state: MessagesState):
    _, tools_by_name = await _ensure_tools()
    result = []
    updates = {}
    for tool_call in state["message_admin"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        try:
            observation = await tool.ainvoke(tool_call["args"])
        except Exception as e:
            observation = f"Tool error: {e}"
            updates["reservation_status"] = "rejected"
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"message_admin": result, **updates}
     
#───Logic for routing edge─────────────────────────────────
def should_continue(state: MessagesState) -> Literal["tool_node_adm", END]:
    last_message = state["message_admin"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
         if state.get('llm_calls',0)>=10:
            return END
         return "tool_node_adm"
    return END
        
         
         


