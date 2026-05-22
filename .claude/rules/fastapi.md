# FastAPI Rules

## App structure

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("app/frontend/chat.html")

@app.get("/admin")
async def admin():
    return FileResponse("app/frontend/admin.html")
```

## Route conventions

- `POST /chat` — accepts `{"session_id": str, "message": str}`, returns `{"reply": str}`
- `GET /admin/pending` — returns list of pending reservation requests
- `POST /admin/decision` — accepts `{"session_id": str, "decision": "approved"|"rejected"}`
- All request/response bodies use Pydantic models

## Pydantic models

```python
from pydantic import BaseModel

class ChatRequest(BaseModel):
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str

class AdminDecision(BaseModel):
    session_id: str
    decision: str  # "approved" | "rejected"
```

## LangGraph integration

- Each chat request maps `session_id` → LangGraph `thread_id`
- Graph is a module-level singleton (compiled once at startup)
- Checkpointer connection is also a singleton; use `check_same_thread=False` for SQLite

```python
# app/agent/graph.py
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

_conn = sqlite3.connect("data/checkpoints.db", check_same_thread=False)
checkpointer = SqliteSaver(_conn)
graph = builder.compile(checkpointer=checkpointer)
```

## Error handling

Only handle errors at the API boundary (route level). Don't add try/except inside agent or RAG logic unless catching a specific known exception.

```python
from fastapi import HTTPException

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        result = graph.invoke({"messages": [("user", req.message)]},
                              config={"configurable": {"thread_id": req.session_id}})
        return ChatResponse(reply=result["messages"][-1].content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```
