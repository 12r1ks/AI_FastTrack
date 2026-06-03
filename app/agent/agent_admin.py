from langgraph.graph import StateGraph, START, END
from app.agent.Utils.state import MessagesState
from app.agent.Utils.nodes_admin import (init_node, llm_call_admin,
                                         approval_node)

agent_builder = StateGraph(MessagesState)

agent_builder.add_node("llm_call_admin", llm_call_admin)
agent_builder.add_node("approval_node", approval_node)
agent_builder.add_node("init_node", init_node)

#───Admin Agent────────────────────────────────────────────────────────────
agent_builder.add_edge(START, "init_node")
agent_builder.add_edge("init_node", "approval_node")
agent_builder.add_edge("approval_node", "llm_call_admin")
agent_builder.add_edge("llm_call_admin", END)

admin_agent = agent_builder.compile()
