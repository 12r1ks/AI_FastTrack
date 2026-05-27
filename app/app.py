from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.agent.agent import agent_builder
from langgraph.checkpoint.memory import InMemorySaver

_checkpointer = InMemorySaver()
agent = agent_builder.compile(checkpointer=_checkpointer)
from langchain_core.messages import HumanMessage
from datetime import datetime

def getcurrentdaytime() -> str:
    return datetime.now().strftime("[%Y-%m-%d %H:%M]")

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/frontend"), name="static")

@app.get("/")
async def root():
    return FileResponse("app/frontend/chat.html")

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat")
async def chat(req: ChatRequest):
    config = {"configurable": {"thread_id": req.session_id}}
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=getcurrentdaytime() + " " + req.message)]},
        config=config,
    )
    return {"reply": result["messages"][-1].content}