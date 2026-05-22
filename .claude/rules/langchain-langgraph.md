# LangChain / LangGraph Rules

Current API (2025). Do not use deprecated patterns.

## Deprecated — never use

| Deprecated | Replacement |
|---|---|
| `LLMChain` | LCEL pipe: `prompt \| llm \| parser` |
| `AgentExecutor` | `StateGraph` (LangGraph) |
| `RetrievalQA` | LangGraph node that calls retriever |
| `ConversationChain` | `MessagesState` in LangGraph |
| `langchain.chains.*` imports | LCEL or LangGraph |

## LangGraph — state schema

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    # add domain fields (reservation_details, approval_status, etc.)
```

## LangGraph — graph construction

```python
from langgraph.graph import StateGraph, START, END

builder = StateGraph(State)
builder.add_node("node_name", node_fn)        # node_fn(state) -> dict
builder.add_edge(START, "node_name")
builder.add_conditional_edges("node_name", routing_fn)
builder.add_edge("node_name", END)

# SQLite checkpointer (required for interrupt/resume and conversation persistence)
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver
checkpointer = SqliteSaver(sqlite3.connect("data/checkpoints.db", check_same_thread=False))
graph = builder.compile(checkpointer=checkpointer)

# Always pass thread_id — it's the persistent cursor for the conversation
config = {"configurable": {"thread_id": "user-session-id"}}
graph.invoke({"messages": [...]}, config=config)
```

## LangGraph — human-in-the-loop

```python
from langgraph.types import interrupt, Command

def admin_approval_node(state: State):
    decision = interrupt({"reservation": state["reservation_details"]})
    return {"approval_status": decision}

# Resume after admin acts
graph.invoke(Command(resume="approved"), config=config)
```

Rules:
- Never wrap `interrupt()` in try/except
- Code before `interrupt()` re-runs on resume — make it idempotent
- `thread_id` in config is mandatory for interrupt to work

## LLM provider switching

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

def get_llm(provider: str = "anthropic"):
    if provider == "openai":
        return ChatOpenAI(model="gpt-4o")
    return ChatAnthropic(model="claude-sonnet-4-6")
```

## FAISS / RAG

```python
from langchain_community.vectorstores import FAISS

# Build and persist
vectorstore = FAISS.from_documents(docs, embeddings)
vectorstore.save_local("data/faiss_index")

# Load
vectorstore = FAISS.load_local(
    "data/faiss_index", embeddings, allow_dangerous_deserialization=True
)
retriever = vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4})
```

## LCEL (simple chains outside LangGraph)

```python
chain = prompt | llm | output_parser
result = chain.invoke({"input": "..."})
await chain.ainvoke({"input": "..."})  # async variant
```
