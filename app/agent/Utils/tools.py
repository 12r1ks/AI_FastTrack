from langchain.tools import tool
from langchain.chat_models import init_chat_model
from typing_extensions import Literal, Annotated
import os
from dotenv import load_dotenv
from app.rag.retriever import retrieve
from app.agent.Utils.SQLquery import query_available_spots
from app.agent.Utils.state import MessagesState

load_dotenv(override=True)

#-- Getting the LLM provider from environment variable ---------------------------------
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "openai":
        return init_chat_model(model="gpt-4o", temperature=0.1)
    return init_chat_model(model="claude-haiku-20240930", temperature=0.1)

#-- Calculate price tool ---------------------------------------------------------------
# This tool calculates the price of parking based on the duration (in hours and days).
@tool("Price_Calculator",
      description=(
          """Calculate the price of parking for a user
          based on the parking duration and the parking lot location."""
      )
)
def price_calculator(Hours: int = 0, Days: int = 0) -> int:
    """Calculate the price of parking for a user.
    Args:
        Hours: The number of hours to park
        Days: The number of days to park
    """
    price_per_hour = 5
    price_per_day = 20
    return (Hours * price_per_hour) + (Days * price_per_day)

#-- RAG tool ---------------------------------------------------------------------------
# This tool retrieves relevant information from (RAG) system based on a user's query.
@tool("retrieve_data_from_RAG",
      description=("Retrieve data from the Retrieval-Augmented Generation system"
                   "Use it to get a better context about the company or "
                   "anwer client's question"
      )
      )
def retrieve_rag_data1(query: str) -> str:
    retrieved_data = retrieve(query, top_k=2)
    return f"Retrieved data for query: {retrieved_data}"

#-- Query available parking spots tool ------------------------------------------------
# This tool queries the available parking spots based on location, time, and spot type.
@tool("query_available_spots",
      description=(
          "Query available parking spots based on location, time, and spot type. "
          "To check if desired time slot is availiable for a user, or when client is asking "
      )
      )
async def query_available_spots_tool(
        location: Annotated[Literal["east", "central"], "Location of the parking lot"],
        start_time: str,
        end_time: str,
        parking_spot_type: Annotated[Literal["A", "B", "T"], "Type of parking spot needed by a customer"]) -> str:
    spots = await query_available_spots(location, start_time, end_time, parking_spot_type)
    return f"Available spots: {spots}"

#-- Store proposed resrvation info-----------------------------------------------------
@tool("store_or_update_info_for_parking_proposal",
      description="stores information for proposal_reservations in MessageState"
)
async def store_or_update_info_for_parking_proposal(
    spot_id: Annotated[str, "parking spot ID"],
    location: Annotated[Literal["east", "central"], "Location of the parking lot"],
    clients_name: Annotated[str, "Clients Full Name"],
    car_number: str,
    start_dt: Annotated[str, "start-parking date in YYYY-MM-DD HH:MM format"],
    end_dt: Annotated[str, "end-parking date in YYYY-MM-DD HH:MM format"],
):
    proposed_reservation = {
        "spot_id": spot_id,
        "location": location,
        "clients_name": clients_name,
        "car_number": car_number,
        "start_dt": start_dt,
        "end_dt": end_dt
        }
    
    return str(proposed_reservation)
