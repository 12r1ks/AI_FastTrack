from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessageChunk

router = APIRouter()


class ChatRequest(BaseModel):
    session_id: str
    message: str


@router.post("/chat")
async def chat(req: ChatRequest):
    from app.agent.graph import agent

    async def stream():
        config = {"configurable": {"thread_id": req.session_id}}
        async for event, chunk in agent.astream(
            {"messages": [HumanMessage(content=req.message)]},
            config=config,
            stream_mode="messages",
        ):
            if isinstance(chunk, AIMessageChunk) and chunk.content:
                text = chunk.content if isinstance(chunk.content, str) else ""
                if text:
                    yield f"data: {text}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(stream(), media_type="text/event-stream")
