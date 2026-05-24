from fastapi import FastAPI
from pydantic import BaseModel
from app.agent.graph import agent
from langchain_core.messages import HumanMessage

app = FastAPI()

class ChatRequest(BaseModel):
    message: str

@app.get("/hello world")
async def root():
    return {"message": "Hello World!"}

@app.post("/ai-fasttrack")
async def root2(req: ChatRequest):
    result = await agent.ainvoke(
        {"messages": [HumanMessage(content=req.message)]})
    return {"reply": result["messages"][-1].content}