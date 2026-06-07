from typing import TypedDict, Annotated, NotRequired, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class MessagesState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    message_admin: NotRequired[Annotated[list[BaseMessage], add_messages]]
    is_admin: NotRequired[bool]
    llm_calls: NotRequired[int]
    session_id: NotRequired[str]
    proposed_reservation: NotRequired[dict]
    approved_reservation: NotRequired[dict]
    reservation_status: NotRequired[Literal["pending administrator review",
                                            "approved", "rejected",
                                            "rejected with follow-up"]]
