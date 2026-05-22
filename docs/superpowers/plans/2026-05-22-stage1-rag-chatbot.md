# Stage 1 — RAG Chatbot Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Working parking chatbot — users can ask about parking info and start a reservation via chat; FastAPI serves the chat page; LangGraph manages state from the first message.

**Architecture:** LangGraph `StateGraph` with three nodes (router → rag_node | collect_details). FAISS for static knowledge, SQLite for dynamic data. FastAPI serves the two-page UI and a `/chat` endpoint. Admin page is a static stub — the approval flow comes in Stage 2.

**Tech Stack:** Python, LangGraph, LangChain, FAISS (`langchain-community`), SQLite (`langgraph.checkpoint.sqlite`), FastAPI, `langchain-openai` (embeddings), `langchain-anthropic` or `langchain-openai` (chat LLM), uv

---

## File Map

| File | Responsibility |
|---|---|
| `pyproject.toml` | uv dependency manifest |
| `config.py` | env loading, `get_llm()`, `get_embeddings()` |
| `app/db/models.py` | SQLite schema + `create_tables()` |
| `app/seed/dynamic_seed.py` | Populate SQLite with fake spaces + slots |
| `app/seed/static_seed.py` | Build FAISS index from fake parking docs |
| `app/rag/retriever.py` | Load FAISS index, expose `get_retriever()` |
| `app/agent/state.py` | `State` TypedDict |
| `app/agent/nodes.py` | `router_node`, `rag_node`, `collect_details_node` |
| `app/agent/graph.py` | Assemble `StateGraph`, compile with `SqliteSaver` |
| `app/api/routes.py` | `/chat`, `/admin/pending` (stub), `/admin/decision` (stub) |
| `main.py` | FastAPI app, mount static files, include router |
| `app/frontend/chat.html` | User chat UI |
| `app/frontend/admin.html` | Admin stub UI |
| `tests/test_models.py` | SQLite schema tests |
| `tests/test_retriever.py` | FAISS retriever tests |
| `tests/test_nodes.py` | Node unit tests |
| `tests/test_api.py` | FastAPI route tests |

---

## Task 1: Project setup

**Files:**
- Create: `pyproject.toml`
- Create: `config.py`
- Create: `app/__init__.py`, `app/db/__init__.py`, `app/rag/__init__.py`, `app/agent/__init__.py`, `app/api/__init__.py`, `app/seed/__init__.py`, `app/frontend/`
- Create: `data/` (empty, gitignored)
- Create: `tests/__init__.py`

- [ ] **Step 1: Initialise project with uv**

```bash
uv init --no-readme
uv add langchain langchain-community langchain-openai langchain-anthropic langgraph "langgraph[sqlite]" faiss-cpu fastapi "uvicorn[standard]" python-dotenv
uv add --dev pytest httpx pytest-asyncio
```

Expected: `pyproject.toml` and `uv.lock` created.

- [ ] **Step 2: Create package directories**

```bash
mkdir -p app/db app/rag app/agent app/api app/frontend app/seed data tests
touch app/__init__.py app/db/__init__.py app/rag/__init__.py app/agent/__init__.py app/api/__init__.py app/seed/__init__.py tests/__init__.py
```

- [ ] **Step 3: Write `config.py`**

```python
import os
from dotenv import load_dotenv

load_dotenv()

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
FAISS_INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "data/faiss_index")
DB_PATH = os.getenv("DB_PATH", "data/parking.db")
CHECKPOINTS_DB_PATH = os.getenv("CHECKPOINTS_DB_PATH", "data/checkpoints.db")


def get_llm():
    if LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY)
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model="claude-sonnet-4-6", api_key=ANTHROPIC_API_KEY)


def get_embeddings():
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(api_key=OPENAI_API_KEY)
```

Note: embeddings always use OpenAI — both `OPENAI_API_KEY` entries in `.env` are required.

- [ ] **Step 4: Copy `.env.example` to `.env` and fill in keys**

```bash
cp .env.example .env
# Edit .env — fill in ANTHROPIC_API_KEY and OPENAI_API_KEY
```

- [ ] **Step 5: Verify imports work**

```bash
uv run python -c "import langchain, langgraph, faiss, fastapi; print('ok')"
```

Expected: `ok`

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock config.py app/ tests/ data/.gitkeep
git commit -m "feat: project scaffold — packages, deps, config"
```

---

## Task 2: SQLite models

**Files:**
- Create: `app/db/models.py`
- Create: `tests/test_models.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_models.py
import sqlite3
import pytest
from app.db.models import create_tables, get_connection


def test_create_tables_creates_all_tables():
    conn = sqlite3.connect(":memory:")
    create_tables(conn)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert "parking_spaces" in tables
    assert "availability_slots" in tables
    assert "reservations" in tables
    conn.close()


def test_parking_spaces_schema():
    conn = sqlite3.connect(":memory:")
    create_tables(conn)
    conn.execute("INSERT INTO parking_spaces (space_number, zone, is_available) VALUES ('A1', 'A', 1)")
    row = conn.execute("SELECT space_number, zone, is_available FROM parking_spaces").fetchone()
    assert row == ("A1", "A", 1)
    conn.close()
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_models.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Write `app/db/models.py`**

```python
import sqlite3
from config import DB_PATH


def get_connection(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS parking_spaces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            space_number TEXT NOT NULL UNIQUE,
            zone TEXT NOT NULL,
            is_available INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS availability_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id INTEGER NOT NULL REFERENCES parking_spaces(id),
            datetime_from TEXT NOT NULL,
            datetime_to TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'free' CHECK(status IN ('free', 'reserved', 'pending'))
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            car_number TEXT NOT NULL,
            datetime_from TEXT NOT NULL,
            datetime_to TEXT NOT NULL,
            approved_at TEXT NOT NULL
        );
    """)
    conn.commit()
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_models.py -v
```

Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add app/db/models.py tests/test_models.py
git commit -m "feat: SQLite schema — parking_spaces, availability_slots, reservations"
```

---

## Task 3: Dynamic seed data

**Files:**
- Create: `app/seed/dynamic_seed.py`

- [ ] **Step 1: Write `app/seed/dynamic_seed.py`**

```python
import sqlite3
from datetime import datetime, timedelta
from app.db.models import create_tables, get_connection


def seed(conn: sqlite3.Connection) -> None:
    create_tables(conn)

    spaces = [
        ("A1", "A"), ("A2", "A"), ("A3", "A"), ("A4", "A"), ("A5", "A"),
        ("B1", "B"), ("B2", "B"), ("B3", "B"), ("B4", "B"), ("B5", "B"),
    ]
    for number, zone in spaces:
        conn.execute(
            "INSERT OR IGNORE INTO parking_spaces (space_number, zone, is_available) VALUES (?, ?, 1)",
            (number, zone),
        )
    conn.commit()

    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    space_ids = [r[0] for r in conn.execute("SELECT id FROM parking_spaces").fetchall()]
    for space_id in space_ids:
        for day_offset in range(30):
            slot_start = now + timedelta(days=day_offset, hours=8)
            slot_end = slot_start + timedelta(hours=10)
            conn.execute(
                "INSERT OR IGNORE INTO availability_slots (space_id, datetime_from, datetime_to, status) VALUES (?, ?, ?, 'free')",
                (space_id, slot_start.strftime("%Y-%m-%d %H:%M"), slot_end.strftime("%Y-%m-%d %H:%M")),
            )
    conn.commit()
    print(f"Seeded {len(spaces)} spaces and {len(spaces) * 30} slots.")


if __name__ == "__main__":
    seed(get_connection())
```

- [ ] **Step 2: Run the seed**

```bash
uv run python -m app.seed.dynamic_seed
```

Expected: `Seeded 10 spaces and 300 slots.`

- [ ] **Step 3: Verify data**

```bash
uv run python -c "
from app.db.models import get_connection
conn = get_connection()
print('spaces:', conn.execute('SELECT COUNT(*) FROM parking_spaces').fetchone()[0])
print('slots:', conn.execute('SELECT COUNT(*) FROM availability_slots').fetchone()[0])
"
```

Expected: `spaces: 10`, `slots: 300`

- [ ] **Step 4: Commit**

```bash
git add app/seed/dynamic_seed.py
git commit -m "feat: dynamic seed — 10 parking spaces, 300 availability slots"
```

---

## Task 4: Static seed + FAISS index

**Files:**
- Create: `app/seed/static_seed.py`
- Create: `app/rag/retriever.py`
- Create: `tests/test_retriever.py`

- [ ] **Step 1: Write failing retriever test**

```python
# tests/test_retriever.py
import pytest
from unittest.mock import MagicMock, patch
from app.rag.retriever import get_retriever


def test_get_retriever_returns_retriever():
    mock_embeddings = MagicMock()
    mock_vs = MagicMock()
    mock_vs.as_retriever.return_value = MagicMock()

    with patch("app.rag.retriever.FAISS.load_local", return_value=mock_vs):
        retriever = get_retriever(mock_embeddings, index_path="data/faiss_index")

    mock_vs.as_retriever.assert_called_once()
    assert retriever is not None
```

- [ ] **Step 2: Run test — expect failure**

```bash
uv run pytest tests/test_retriever.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `app/rag/retriever.py`**

```python
from langchain_community.vectorstores import FAISS
from langchain_core.vectorstores import VectorStoreRetriever
from config import FAISS_INDEX_PATH, get_embeddings


def get_retriever(embeddings=None, index_path: str = FAISS_INDEX_PATH) -> VectorStoreRetriever:
    if embeddings is None:
        embeddings = get_embeddings()
    vectorstore = FAISS.load_local(
        index_path, embeddings, allow_dangerous_deserialization=True
    )
    return vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 4})
```

- [ ] **Step 4: Write `app/seed/static_seed.py`**

```python
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from config import get_embeddings, FAISS_INDEX_PATH

DOCUMENTS = [
    Document(page_content="Downtown ParkBot is a modern, secure parking facility located in the city centre. We offer 10 spaces across two zones: Zone A (covered) and Zone B (open air).", metadata={"category": "general"}),
    Document(page_content="Our parking facility is located at 15 Central Boulevard, Cityville. Nearest landmark: City Hall. GPS: 48.8566° N, 2.3522° E. Public transport: Bus lines 12, 34, 45 stop within 100m.", metadata={"category": "location"}),
    Document(page_content="Opening hours: Monday to Friday 07:00–22:00. Saturday 08:00–20:00. Sunday 09:00–18:00. The facility is closed on public holidays.", metadata={"category": "hours"}),
    Document(page_content="Pricing: Zone A (covered) costs €5.00/hour or €30.00/day. Zone B (open air) costs €3.00/hour or €20.00/day. Weekly rates available on request. Payment accepted: card and mobile payments only.", metadata={"category": "pricing"}),
    Document(page_content="Reservation rules: Minimum reservation is 1 hour. Maximum is 30 days. Cancellations must be made at least 2 hours before the start time. No-shows forfeit the reservation. Reservations require: full name, car registration number, start and end datetime.", metadata={"category": "rules"}),
    Document(page_content="Frequently asked questions: Q: Can I extend my reservation? A: Yes, contact the admin before your slot ends. Q: Is the facility CCTV monitored? A: Yes, 24/7. Q: Are electric vehicle chargers available? A: Zone A has 2 EV charging points (Type 2). Q: Can I park a motorcycle? A: Yes, at a reduced rate of €1.50/hour in Zone B.", metadata={"category": "faq"}),
]


def seed(index_path: str = FAISS_INDEX_PATH) -> None:
    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(DOCUMENTS, embeddings)
    vectorstore.save_local(index_path)
    print(f"FAISS index saved to {index_path} ({len(DOCUMENTS)} documents).")


if __name__ == "__main__":
    seed()
```

- [ ] **Step 5: Build the FAISS index**

```bash
uv run python -m app.seed.static_seed
```

Expected: `FAISS index saved to data/faiss_index (6 documents).`

- [ ] **Step 6: Run retriever test — expect pass**

```bash
uv run pytest tests/test_retriever.py -v
```

Expected: 1 passed

- [ ] **Step 7: Commit**

```bash
git add app/seed/static_seed.py app/rag/retriever.py tests/test_retriever.py
git commit -m "feat: FAISS index and retriever — 6 static parking docs"
```

---

## Task 5: LangGraph state schema

**Files:**
- Create: `app/agent/state.py`

- [ ] **Step 1: Write `app/agent/state.py`**

```python
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class State(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    intent: str | None          # "info" | "reservation"
    reservation: dict | None    # {name, surname, car_number, datetime_from, datetime_to}
    approval_status: str | None # "pending" | "approved" | "rejected"
```

- [ ] **Step 2: Verify import**

```bash
uv run python -c "from app.agent.state import State; print(State.__annotations__.keys())"
```

Expected: `dict_keys(['messages', 'intent', 'reservation', 'approval_status'])`

- [ ] **Step 3: Commit**

```bash
git add app/agent/state.py
git commit -m "feat: LangGraph State schema"
```

---

## Task 6: Agent nodes

**Files:**
- Create: `app/agent/nodes.py`
- Create: `tests/test_nodes.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_nodes.py
from unittest.mock import MagicMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from app.agent.state import State
from app.agent.nodes import router_node, collect_details_node


def _state(**kwargs) -> State:
    defaults = {"messages": [], "intent": None, "reservation": None, "approval_status": None}
    defaults.update(kwargs)
    return defaults


def test_router_sets_intent_to_info():
    state = _state(messages=[HumanMessage(content="What are the opening hours?")])
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="info")
    with patch("app.agent.nodes.get_llm", return_value=mock_llm):
        result = router_node(state)
    assert result["intent"] == "info"


def test_router_sets_intent_to_reservation():
    state = _state(messages=[HumanMessage(content="I want to reserve a parking space")])
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="reservation")
    with patch("app.agent.nodes.get_llm", return_value=mock_llm):
        result = router_node(state)
    assert result["intent"] == "reservation"


def test_collect_details_asks_for_name_when_empty():
    state = _state(intent="reservation", reservation={})
    result = collect_details_node(state)
    last_msg = result["messages"][-1]
    assert "name" in last_msg.content.lower()


def test_collect_details_asks_for_next_missing_field():
    state = _state(
        intent="reservation",
        reservation={"name": "John", "surname": "Smith"},
        messages=[],
    )
    result = collect_details_node(state)
    last_msg = result["messages"][-1]
    assert "car" in last_msg.content.lower() or "registration" in last_msg.content.lower()
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_nodes.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `app/agent/nodes.py`**

```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from app.agent.state import State
from app.rag.retriever import get_retriever
from app.db.models import get_connection
from config import get_llm

_RESERVATION_FIELDS = [
    ("name", "What is your first name?"),
    ("surname", "What is your last name?"),
    ("car_number", "What is your car registration number?"),
    ("datetime_from", "From when do you need the space? (format: YYYY-MM-DD HH:MM)"),
    ("datetime_to", "Until when do you need the space? (format: YYYY-MM-DD HH:MM)"),
]


def router_node(state: State) -> dict:
    last_message = state["messages"][-1].content
    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "Classify the user message as exactly one word: 'info' or 'reservation'.\n"
            "'reservation' = user wants to book/reserve a parking space.\n"
            "'info' = any question about parking (hours, pricing, location, availability, rules).\n"
            "Reply with only the single word."
        )),
        HumanMessage(content=last_message),
    ])
    response = llm.invoke(prompt.format_messages())
    intent = "reservation" if "reservation" in response.content.lower() else "info"
    return {"intent": intent}


def rag_node(state: State) -> dict:
    last_message = state["messages"][-1].content
    retriever = get_retriever()
    docs = retriever.invoke(last_message)
    static_context = "\n\n".join(d.page_content for d in docs)

    conn = get_connection()
    available_count = conn.execute(
        "SELECT COUNT(*) FROM availability_slots WHERE status = 'free'"
    ).fetchone()[0]
    dynamic_context = f"Currently available slots: {available_count}"

    llm = get_llm()
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=(
            "You are ParkBot, a helpful parking reservation assistant.\n"
            "Answer using ONLY the context below. If the answer is not in the context, say you don't have that information.\n\n"
            f"Parking information:\n{static_context}\n\n"
            f"Live data:\n{dynamic_context}"
        )),
        *state["messages"],
    ])
    response = llm.invoke(prompt.format_messages())
    return {"messages": [AIMessage(content=response.content)]}


def collect_details_node(state: State) -> dict:
    reservation = state.get("reservation") or {}

    for field, question in _RESERVATION_FIELDS:
        if not reservation.get(field):
            last_message = state["messages"][-1].content if state["messages"] else ""
            if last_message and state.get("intent") == "reservation":
                prev_missing = _get_last_asked_field(state)
                if prev_missing and not reservation.get(prev_missing):
                    reservation[prev_missing] = last_message.strip()

            if not reservation.get(field):
                return {
                    "reservation": reservation,
                    "messages": [AIMessage(content=question)],
                }

    summary = (
        f"Here is your reservation request:\n"
        f"- Name: {reservation['name']} {reservation['surname']}\n"
        f"- Car: {reservation['car_number']}\n"
        f"- From: {reservation['datetime_from']}\n"
        f"- To: {reservation['datetime_to']}\n\n"
        "Shall I submit this for admin approval? (yes / no)"
    )
    return {
        "reservation": reservation,
        "messages": [AIMessage(content=summary)],
    }


def _get_last_asked_field(state: State) -> str | None:
    for msg in reversed(state["messages"][:-1]):
        if isinstance(msg, AIMessage):
            for field, question in _RESERVATION_FIELDS:
                if question.lower() in msg.content.lower():
                    return field
    return None
```

- [ ] **Step 4: Run tests — expect pass**

```bash
uv run pytest tests/test_nodes.py -v
```

Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add app/agent/nodes.py tests/test_nodes.py
git commit -m "feat: agent nodes — router, rag_node, collect_details"
```

---

## Task 7: LangGraph graph assembly

**Files:**
- Create: `app/agent/graph.py`

- [ ] **Step 1: Write `app/agent/graph.py`**

```python
import sqlite3
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.sqlite import SqliteSaver
from app.agent.state import State
from app.agent.nodes import router_node, rag_node, collect_details_node
from config import CHECKPOINTS_DB_PATH


def _route_after_router(state: State) -> str:
    return state.get("intent") or "info"


def build_graph() -> StateGraph:
    builder = StateGraph(State)
    builder.add_node("router", router_node)
    builder.add_node("rag", rag_node)
    builder.add_node("collect_details", collect_details_node)
    builder.add_edge(START, "router")
    builder.add_conditional_edges("router", _route_after_router, {
        "info": "rag",
        "reservation": "collect_details",
    })
    builder.add_edge("rag", END)
    builder.add_edge("collect_details", END)
    return builder


_conn = sqlite3.connect(CHECKPOINTS_DB_PATH, check_same_thread=False)
_checkpointer = SqliteSaver(_conn)
graph = build_graph().compile(checkpointer=_checkpointer)
```

- [ ] **Step 2: Verify graph compiles**

```bash
uv run python -c "from app.agent.graph import graph; print('graph ok:', type(graph))"
```

Expected: `graph ok: <class 'langgraph.graph.state.CompiledStateGraph'>`

- [ ] **Step 3: Commit**

```bash
git add app/agent/graph.py
git commit -m "feat: LangGraph graph — router → rag | collect_details, SQLite checkpointer"
```

---

## Task 8: FastAPI routes and app

**Files:**
- Create: `app/api/routes.py`
- Create: `main.py`
- Create: `tests/test_api.py`

- [ ] **Step 1: Write failing API tests**

```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from langchain_core.messages import AIMessage


@pytest.fixture
def client():
    mock_graph = MagicMock()
    mock_graph.invoke.return_value = {
        "messages": [AIMessage(content="Hello! How can I help?")],
        "intent": "info",
        "reservation": None,
        "approval_status": None,
    }
    with patch("app.api.routes.graph", mock_graph):
        from main import app
        yield TestClient(app)


def test_chat_returns_reply(client):
    response = client.post("/chat", json={"session_id": "test-123", "message": "Hello"})
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "status" in data


def test_chat_status_is_chatting(client):
    response = client.post("/chat", json={"session_id": "test-123", "message": "Hi"})
    assert response.json()["status"] == "chatting"


def test_admin_pending_returns_list(client):
    response = client.get("/admin/pending")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

- [ ] **Step 2: Run tests — expect failure**

```bash
uv run pytest tests/test_api.py -v
```

Expected: `ModuleNotFoundError`

- [ ] **Step 3: Write `app/api/routes.py`**

```python
from fastapi import APIRouter
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from app.agent.graph import graph

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    reply: str
    status: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    result = graph.invoke(
        {"messages": [HumanMessage(content=req.message)]},
        config=config,
    )
    last_message = result["messages"][-1].content
    approval_status = result.get("approval_status")
    if approval_status == "pending":
        status = "awaiting_approval"
    elif approval_status == "approved":
        status = "confirmed"
    elif approval_status == "rejected":
        status = "rejected"
    else:
        status = "chatting"
    return ChatResponse(reply=last_message, status=status)


@router.get("/admin/pending")
def admin_pending():
    # Stage 2: return sessions awaiting approval
    return []


@router.post("/admin/decision")
def admin_decision(payload: dict):
    # Stage 2: resume graph with Command(resume=decision)
    return {"ok": True}
```

- [ ] **Step 4: Write `main.py`**

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.api.routes import router

app = FastAPI(title="ParkBot")
app.include_router(router)
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")


@app.get("/")
def serve_chat():
    return FileResponse("app/frontend/chat.html")


@app.get("/admin")
def serve_admin():
    return FileResponse("app/frontend/admin.html")
```

- [ ] **Step 5: Run tests — expect pass**

```bash
uv run pytest tests/test_api.py -v
```

Expected: 3 passed

- [ ] **Step 6: Commit**

```bash
git add app/api/routes.py main.py tests/test_api.py
git commit -m "feat: FastAPI routes — /chat, /admin/pending stub, /admin/decision stub"
```

---

## Task 9: Chat frontend

**Files:**
- Create: `app/frontend/chat.html`

- [ ] **Step 1: Write `app/frontend/chat.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>ParkBot</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; height: 100vh; display: flex; flex-direction: column; }
    header { background: #252542; padding: 12px 20px; border-bottom: 1px solid #3d3d5c; font-weight: bold; font-size: 18px; }
    #messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 10px; }
    .msg { max-width: 75%; padding: 10px 14px; border-radius: 12px; line-height: 1.5; word-wrap: break-word; }
    .msg.bot { align-self: flex-start; background: #252542; }
    .msg.user { align-self: flex-end; background: #4f46e5; }
    .msg.system { align-self: center; background: #374151; font-size: 13px; color: #9ca3af; border-radius: 8px; }
    #input-bar { display: flex; gap: 8px; padding: 12px 16px; border-top: 1px solid #3d3d5c; background: #252542; }
    #input { flex: 1; background: #1a1a2e; border: 1px solid #3d3d5c; border-radius: 20px; padding: 10px 16px; color: #eee; font-size: 15px; outline: none; }
    #send { background: #4f46e5; color: #fff; border: none; border-radius: 20px; padding: 10px 20px; cursor: pointer; font-size: 15px; }
    #send:disabled { opacity: 0.5; cursor: not-allowed; }
  </style>
</head>
<body>
  <header>🅿 ParkBot</header>
  <div id="messages">
    <div class="msg bot">Hello! I can help you with parking information or make a reservation. What can I do for you?</div>
  </div>
  <div id="input-bar">
    <input id="input" type="text" placeholder="Type a message..." autocomplete="off" />
    <button id="send">Send</button>
  </div>

  <script>
    const sessionId = crypto.randomUUID();
    const messagesEl = document.getElementById('messages');
    const inputEl = document.getElementById('input');
    const sendBtn = document.getElementById('send');

    function addMessage(text, type) {
      const div = document.createElement('div');
      div.className = `msg ${type}`;
      div.textContent = text;
      messagesEl.appendChild(div);
      messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    async function sendMessage() {
      const text = inputEl.value.trim();
      if (!text) return;
      inputEl.value = '';
      sendBtn.disabled = true;
      addMessage(text, 'user');

      try {
        const res = await fetch('/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId, message: text }),
        });
        const data = await res.json();
        addMessage(data.reply, 'bot');
        if (data.status === 'awaiting_approval') {
          addMessage('⏳ Your request has been sent to the admin for approval.', 'system');
        } else if (data.status === 'confirmed') {
          addMessage('✅ Your reservation has been confirmed!', 'system');
        } else if (data.status === 'rejected') {
          addMessage('❌ Your reservation was rejected by the admin.', 'system');
        }
      } catch (e) {
        addMessage('Connection error. Please try again.', 'system');
      }

      sendBtn.disabled = false;
      inputEl.focus();
    }

    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keydown', e => { if (e.key === 'Enter') sendMessage(); });
  </script>
</body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add app/frontend/chat.html
git commit -m "feat: chat.html — classic chat UI"
```

---

## Task 10: Admin frontend (stub) + smoke test

**Files:**
- Create: `app/frontend/admin.html`

- [ ] **Step 1: Write `app/frontend/admin.html`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ParkBot Admin</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; min-height: 100vh; }
    header { background: #252542; padding: 12px 20px; border-bottom: 1px solid #3d3d5c; font-weight: bold; font-size: 18px; display: flex; align-items: center; justify-content: space-between; }
    #pending-badge { background: #374151; color: #9ca3af; border-radius: 10px; padding: 2px 10px; font-size: 13px; }
    #list { padding: 20px; max-width: 700px; margin: 0 auto; }
    .empty { text-align: center; color: #6b7280; margin-top: 60px; }
  </style>
</head>
<body>
  <header>
    🅿 ParkBot — Admin
    <span id="pending-badge">0 pending</span>
  </header>
  <div id="list">
    <p class="empty">No pending reservations. Stage 2 will populate this list.</p>
  </div>
</body>
</html>
```

- [ ] **Step 2: Run the full app**

```bash
uv run uvicorn main:app --reload
```

- [ ] **Step 3: Manual smoke test**

Open `http://localhost:8000` — chat page loads, type "What are the opening hours?" — bot replies with hours. Type "I want to reserve a space" — bot asks for your name.

Open `http://localhost:8000/admin` — admin stub page loads.

- [ ] **Step 4: Run full test suite**

```bash
uv run pytest -v
```

Expected: all tests pass

- [ ] **Step 5: Update CLAUDE.md commands section**

Replace the placeholder commands block with:

```bash
uv sync                               # install dependencies
uv run python -m app.seed.dynamic_seed  # seed SQLite
uv run python -m app.seed.static_seed   # build FAISS index
uv run uvicorn main:app --reload      # run the app
uv run pytest                         # run all tests
uv run pytest tests/test_api.py -v    # run a single test file
```

- [ ] **Step 6: Final commit**

```bash
git add app/frontend/admin.html CLAUDE.md
git commit -m "feat: admin stub UI + stage 1 complete"
```
