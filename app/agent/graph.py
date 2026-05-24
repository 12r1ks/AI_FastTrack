from langgraph.graph import StateGraph, START, END
from dotenv import load_dotenv
from app.agent.agent_and_tools import MessagesState, llm_call, get_llm, tool_node, should_continue
from langchain_core.messages import HumanMessage

print("Loading environment variables...")





agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)

agent_builder.add_edge(START, "llm_call")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", END])
agent_builder.add_edge("tool_node", "llm_call")


agent = agent_builder.compile()



if __name__ == "__main__":
    
    messages = [HumanMessage(content="how much cost parking in your company?")]
    messages = agent.invoke({"messages": messages})
    for m in messages["messages"]:
        m.pretty_print()

    import os
    from datetime import datetime
    os.makedirs("app/agent/graphs", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = f"app/agent/graphs/graph_{timestamp}.png"
    img = agent.get_graph(xray=True).draw_mermaid_png()
    with open(path, "wb") as f:
        f.write(img)
    print(f"Saved to {path}")













