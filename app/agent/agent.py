from langgraph.graph import StateGraph, START, END
from app.agent.Utils.state import MessagesState
from app.agent.Utils.nodes import llm_call, tool_node, should_continue, guard_route, reject_node
from langchain_core.messages import HumanMessage


print("Tracing module loading... Graph.py is loading")

agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("reject", reject_node)

agent_builder.add_conditional_edges(START, guard_route, ["llm_call", "reject"])
agent_builder.add_edge("reject", END)
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")

agent = agent_builder.compile()

if __name__ == "__main__":
    import asyncio
    from dotenv import load_dotenv
    load_dotenv()

    async def test():
        config = {"configurable": {"thread_id": "test"}}
        messages = [HumanMessage(content="what locations do u have? and will be there availiable spots tomorrow??")]
        result = await agent.ainvoke({"messages": messages}, config=config)
        for m in result["messages"]:
            m.pretty_print()

    asyncio.run(test())

    import os
    from datetime import datetime
    os.makedirs("app/agent/graphs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"app/agent/graphs/graph_{timestamp}.png"
    img = agent.get_graph(xray=True).draw_mermaid_png()
    with open(path, "wb") as f:
        f.write(img)
    print(f"Saved to {path}")
