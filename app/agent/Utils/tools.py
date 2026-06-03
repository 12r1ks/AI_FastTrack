from langchain.tools import tool
from langchain.chat_models import init_chat_model
from typing_extensions import Literal, Annotated
import os
from dotenv import load_dotenv
from app.rag.retriever import retrieve
from app.agent.Utils.SQLquery import query_available_spots

load_dotenv(override=True)

# ── LLM provider ─────────────────────────────────────────────────────────────
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "openai":
        return init_chat_model(model="gpt-4o", temperature=0.1)
    return init_chat_model(model="claude-haiku-4-5-20251001", temperature=0.1)

# ── Price calculator tool ────────────────────────────────────────────────────
@tool("Price_Calculator",
      description=(
          """Calculate the price of parking for a user
          based on the parking duration and the parking lot location."""
      )
)
def price_calculator(Hours: int = 0, Days: int = 0, Price_Per_Hour: float = 0, Price_Per_Day: float = 0) -> float:
    """Calculate the price of parking for a user.
    Args:
        Hours: The number of hours to park
        Days: The number of days to park
        Price_Per_Hour: Hourly price of a parking spot. Based on location and parking spot type.
        Price_Per_Day: Daily price of a parking spot. Based on location and parking spot type.
    """
    if Hours < 0 or Days < 0:
        raise ValueError("Hours and Days must be non-negative")
    if Price_Per_Hour < 0 or Price_Per_Day < 0:
        raise ValueError("Price must be non-negative")
    if Hours > 0 and Price_Per_Hour == 0:
        raise ValueError("No price per hour for price calculation")
    if Days > 0 and Price_Per_Day == 0:
        raise ValueError("No price per day for price calculation")

    return (Hours * Price_Per_Hour) + (Days * Price_Per_Day)

# ── RAG tool ─────────────────────────────────────────────────────────────────
@tool("Retrieve_data_from_company_database",
      description=("Retrieve data from the Retrieval-Augmented Generation system. "
                   "Use it to get better context about the company or "
                   "answer client's question."
      )
      )
def retrieve_rag_data1(query: str) -> str:
    retrieved_data = retrieve(query, top_k=3)
    return f"Retrieved data for query: {retrieved_data}"

# ── Query available spots tool ───────────────────────────────────────────────
@tool("query_available_spots",
      description=(
          "Query available parking spots based on location, time, and spot type. "
          "Use it to check if a desired time slot is available for a user."
      )
      )
async def query_available_spots_tool(
        location: Annotated[Literal["east", "central"], "Location of the parking lot"],
        start_time: str,
        end_time: str,
        parking_spot_type: Annotated[Literal["A", "B", "T"], "Type of parking spot needed by a customer"]) -> str:
    spots = await query_available_spots(location, start_time, end_time, parking_spot_type)
    return f"Available spots: {spots}"

# ── Store reservation proposal tool ──────────────────────────────────────────
@tool("store_or_update_info_for_parking_proposal",
      description=(
          "Call this tool only when all reservation details have been collected and confirmed by the user. "
          "Before calling, present a clear summary of the details to the user and ask for explicit confirmation. "
          "Once called, the reservation is flagged for administrator review — the user should be informed it is pending approval."
      )
)
async def store_or_update_info_for_parking_proposal(
    spot_id: Annotated[str, "parking spot ID"],
    location: Annotated[Literal["east", "central"], "Location of the parking lot"],
    clients_name: Annotated[str, "Clients Full Name"],
    car_number: str,
    phone_number: Annotated[str, "Client's phone number"],
    start_dt: Annotated[str, "start-parking date in YYYY-MM-DD HH:MM format"],
    end_dt: Annotated[str, "end-parking date in YYYY-MM-DD HH:MM format"],
    price: Annotated[float, "cost of parking in euros"]
):
    from datetime import datetime
    if not clients_name.strip():
        raise ValueError("clients_name cannot be empty")
    if not car_number.strip():
        raise ValueError("car_number cannot be empty")
    if not phone_number.strip():
        raise ValueError("phone_number cannot be empty")
    if not price:
        raise ValueError("price cannot be empty")
    if price < 0:
        raise ValueError("price cannot be negative")
    try:
        start = datetime.strptime(start_dt, "%Y-%m-%d %H:%M")
        end = datetime.strptime(end_dt, "%Y-%m-%d %H:%M")
    except ValueError:
        raise ValueError("dates must be in YYYY-MM-DD HH:MM format")
    if start >= end:
        raise ValueError("start_dt must be before end_dt")
    if start <= datetime.now():
        raise ValueError("start_dt must be in the future")

    return str({
        "spot_id": spot_id,
        "location": location,
        "clients_name": clients_name,
        "car_number": car_number,
        "phone_number": phone_number,
        "start_dt": start_dt,
        "end_dt": end_dt,
        "price": price,
    })
