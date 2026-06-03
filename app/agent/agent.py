from langgraph.graph import StateGraph, START, END
from app.agent.Utils.state import MessagesState
from app.agent.Utils.nodes import (init_node,
                                   llm_call, tool_node, should_continue,
                                   guard_route, reject_node, pre_end_guard)
from app.agent.agent_admin import admin_agent





agent_builder = StateGraph(MessagesState)
agent_builder.add_node("llm_call", llm_call)
agent_builder.add_node("tool_node", tool_node)
agent_builder.add_node("reject", reject_node)
agent_builder.add_node("sub_agen_admin", admin_agent)
agent_builder.add_node("pre_end_guard", pre_end_guard)
agent_builder.add_node("init", init_node)

agent_builder.add_edge(START, "init")
agent_builder.add_conditional_edges("init", guard_route, ["llm_call", "reject"])
agent_builder.add_edge("reject", "pre_end_guard")
agent_builder.add_conditional_edges("llm_call", should_continue, ["tool_node", "pre_end_guard", "sub_agen_admin"])
agent_builder.add_edge("tool_node", "llm_call")
agent_builder.add_edge("pre_end_guard", END)
agent_builder.add_edge("sub_agen_admin", "llm_call")

agent = agent_builder.compile()

