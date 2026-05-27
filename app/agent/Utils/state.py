from typing import TypedDict, Annotated, NotRequired
from operator import add
from typing import Any as AnyMessage


class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], add]
    llm_calls: NotRequired[int]
    session_id: NotRequired[str]
    proposed_reservation: NotRequired[dict]
    approved_reservation: NotRequired[dict]
    is_admin: NotRequired[bool]

reservation_base = {
    "spot_id": None, 
    "location": None,
    "clients_name": None,
    "car_number": None,
    "start_dt": None,
    "end_dt": None,
    "price": None
}
