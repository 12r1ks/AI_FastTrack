from langchain_core.messages import SystemMessage, HumanMessage
from app.agent.Utils.state import MessagesState
from app.agent.Utils.tools import get_llm
from langgraph.types import interrupt

model = get_llm()

def init_node(state: MessagesState) -> dict:
    return {"is_admin": True, "message_admin": []}



#───Human in the loop────────────────────────────────────────────────────────
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

def llm_call_admin(state: MessagesState) -> MessagesState:
        
        answer = model.invoke(
                    [
                        SystemMessage(
                            content=(
                                f"## Role\n"
                                " You are an administrator for handling parking reservations.\n\n"
                                "## Goals\n"
                                "- Handle reservation review and aproval status from an administrator\n"
                                "- If not ask administrator for a reason, if they didnt mention any\n"
                                "- Provide short summary for chat bot who speaks with a client.\n" \
                                "- If no information provided, just say so, but state rejection.\n\n"
                                "## Current Session State\n"
                                f"Proposed reservation: {state.get('proposed_reservation') or 'None yet'}\n"
                                f"Reservation status: {state.get('reservation_status') or 'No reservation submitted'}\n"
                            )        
                        )
                    ] + state.get("message_admin", []))
        
        return {"messages": [answer],
                "message_admin": [answer],
                "llm_calls": state.get("llm_calls", 0) + 1}
    