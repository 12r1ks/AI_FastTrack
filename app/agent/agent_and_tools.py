
from langchain.messages import AnyMessage, HumanMessage, SystemMessage, ToolMessage
from typing_extensions import Literal, TypedDict, Annotated
import operator
from langchain.tools import tool
from langchain.chat_models import init_chat_model
import os
from langgraph.graph import END
from dotenv import load_dotenv
from app.rag.retriever import retrieve

load_dotenv()

def get_llm():
    provider = os.getenv("LLM_PROVIDER", "anthropic")
    if provider == "openai":
        return init_chat_model(model="gpt-4o", temperature=0.1)
    return init_chat_model(model="claude-sonnet-4-6", temperature=0.1)
    
class MessagesState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]
    llm_calls: int



@tool("Price_Calculator",
      description=(
          """Calculate the price of parking for a user
          based on the parking duration and the parking lot location."""
      )
)
def multiply(Hours: int = 0, Days: int = 0) -> int:
    
    """Calculate the price of parking for a user.
    Args:
        Hours: The number of hours to park
        Days: The number of days to park
    """
    price_per_hour = 5
    price_per_day = 20
    return (Hours * price_per_hour) + (Days * price_per_day)



@tool("retrieve_data_from_RAG",
      description="Retrieve data from the Retrieval-Augmented Generation system"
      )
def retrieve_rag_data1(query: str) -> str:
    """Retrieve data from the RAG system based on a query.
    Args:
        query: The search query for the RAG system
    Returns:
        The retrieved data from the RAG system
    """
    retrieved_data = retrieve(query, top_k=2)
    return f"Retrieved data for query: {retrieved_data}"

model = get_llm()
tools = [multiply, retrieve_rag_data1]
tools_by_name = {t.name: t for t in tools}
model_with_tools = model.bind_tools(tools)


def llm_call(state: MessagesState) -> MessagesState:
    """LLM decides whether to call a tool or not"""
    return {
        "messages": [
            model_with_tools.invoke(
                [
                    SystemMessage(
                        content="You are a helpful parking assistant"
                    )
                ]
                + state["messages"]
            )
        ],
        "llm_calls": state.get('llm_calls', 0) + 1
    }

# Node that performs the tool call, and returns results.
def tool_node(state: dict):
    """Performs the tool call"""

    result = []
    for tool_call in state["messages"][-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"])
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))
    return {"messages": result}


# For LLM TO decide whether to call a tool or not.
# Check the last message for any tool calls.
# There is T_Call -> tool_node, and No_T_Call -> END
def should_continue(state: MessagesState) -> Literal["tool_node", "__end__"]:
    
    messages = state["messages"]
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tool_node"

    return "__end__"













