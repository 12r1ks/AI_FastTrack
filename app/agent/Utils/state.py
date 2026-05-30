from typing import TypedDict, Annotated, NotRequired
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    llm_calls: NotRequired[int]
    session_id: NotRequired[str]
    proposed_reservation: NotRequired[dict]
    approved_reservation: NotRequired[dict]
    is_admin: NotRequired[bool]
    reservation_status: NotRequired[str]

reservation_base = {
    "spot_id": None, 
    "location": None,
    "clients_name": None,
    "car_number": None,
    "start_dt": None,
    "end_dt": None,
    "price": None,
    "phone_number": None
}
