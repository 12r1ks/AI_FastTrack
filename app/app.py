from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.agent.agent import agent_builder
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from langchain_core.messages import HumanMessage

_checkpointer = InMemorySaver()
agent = agent_builder.compile(checkpointer=_checkpointer)

# session_id → proposed_reservation dict for pending admin reviews
_pending: dict[str, dict] = {}

# session_id → assistant messages awaiting delivery to an idle user chat
_outbox: dict[str, list[str]] = {}

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("app/frontend/chat.html")

@app.get("/admin")
async def admin_page():
    return FileResponse("app/frontend/admin.html")


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    try:
        config = {"configurable": {"thread_id": req.session_id}}
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
        )
        if "__interrupt__" in result:
            _pending[req.session_id] = True
            return {"pending": True}
        return {"reply": result["messages"][-1].content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/poll")
async def chat_poll(session_id: str):
    return {"messages": _outbox.pop(session_id, [])}


# ── Admin ─────────────────────────────────────────────────────────────────────

@app.get("/admin/pending")
async def get_pending():
    result = []
    for session_id in list(_pending.keys()):
        config = {"configurable": {"thread_id": session_id}}
        try:
            state = await agent.aget_state(config)
            result.append({
                "session_id": session_id,
                "proposed_reservation": state.values.get("proposed_reservation", {}),
            })
        except Exception:
            pass
    return result

class AdminDecision(BaseModel):
    session_id: str
    decision: str
    reason: str = ""

@app.post("/admin/decision")
async def admin_decision(req: AdminDecision):
    if req.session_id not in _pending:
        raise HTTPException(status_code=404, detail="No pending session found")
    try:
        config = {"configurable": {"thread_id": req.session_id}}
        result = await agent.ainvoke(
            Command(resume={"decision": req.decision, "reason": req.reason}),
            config=config,
        )
        _pending.pop(req.session_id, None)
        _outbox.setdefault(req.session_id, []).append(result["messages"][-1].content)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))