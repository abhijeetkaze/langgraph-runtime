import os
from typing import Annotated
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableLambda
from langgraph.graph.message import add_messages
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Define a simple state for the graph
class GraphState(dict):
    messages : Annotated[list, add_messages]
    previous_agent : str #previous agent that was called
    current_agent : str #current agent that is being called
    previous_agent_query: str # any query from the previous agent
    next : str #next agent to call can only be "creator" or "executor" or "human"


# Supervisor agent: decides which agent to call next
def supervisor_agent(state: GraphState) -> str:
    print("[Supervisor Agent] Deciding next step...")
    # Example logic: if no task, go to creator; if task exists, go to executor
    return {
        "next": "creator" if "task" not in state else "executor"
    }

def human_agent(state: GraphState) -> GraphState:
    print("[Human Agent] Interacting with user...")
    # Simulate human interaction
    return state

# Creator agent: creates a task or message
def creator_agent(state: GraphState) -> GraphState:
    print("[Creator Agent] Generating task...")
    state["task"] = "Translate 'Hello, world!' to French."
    return state

# Executor agent: executes the task
def executor_agent(state: GraphState) -> GraphState:
    print("[Executor Agent] Executing task:", state.get("task"))
    return state

# Example tool for supervisor only
def supervisor_tool():
    print("[Supervisor Tool] Tool used by supervisor.")
    return "Tool result"

def create_supervisor_graph():
    # Build the graph
    workflow = StateGraph(GraphState)
    workflow.add_node("supervisor", supervisor_agent)
    workflow.add_node("creator", creator_agent)
    workflow.add_node("executor", executor_agent)
    workflow.add_node("human", human_agent)

    # Conditional edge from supervisor to creator or executor
    def supervisor_router(state: GraphState):
        if state.get("next") == "creator":
            return "creator"
        elif state.get("next") == "executor":
            return "executor"
        elif state.get("next") == "human":
            return "human"

    workflow.set_entry_point("supervisor")
    workflow.add_conditional_edges(
        "supervisor",
        supervisor_router,
        {
          "creator": "creator",
          "executor": "executor",
          "human": "human"
        }
    )
    workflow.add_edge("creator", "supervisor")
    workflow.add_edge("executor", END)

    graph = workflow.compile()

    return graph

if __name__ == "__main__":
    # Run the graph
    result = create_supervisor_graph().invoke({})
    print("\nFinal result:", result.get("result"))
