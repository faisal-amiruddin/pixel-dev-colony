from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes import (
    commander_node,
    architect_node,
    backend_dev_node,
    frontend_dev_node,
    qa_node,
    devops_node
)

def build_graph():
    # Initialize the graph with the state
    builder = StateGraph(AgentState)
    
    # Add all nodes
    builder.add_node("commander", commander_node)
    builder.add_node("architect", architect_node)
    builder.add_node("backend_dev", backend_dev_node)
    builder.add_node("frontend_dev", frontend_dev_node)
    builder.add_node("qa", qa_node)
    builder.add_node("devops", devops_node)
    
    # Define the flow
    builder.set_entry_point("commander")
    builder.add_edge("commander", "architect")
    builder.add_edge("architect", "backend_dev")
    builder.add_edge("backend_dev", "frontend_dev")
    builder.add_edge("frontend_dev", "qa")
    builder.add_edge("qa", "devops")
    builder.add_edge("devops", END)
    
    # Compile the graph
    return builder.compile()