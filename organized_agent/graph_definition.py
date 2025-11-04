import os
from langgraph.graph import StateGraph, START, END
from organized_agent.state_schema import State
from organized_agent.nodes.load_problem_node import load_problem_node
from organized_agent.nodes.analyze_bug_node import analyze_bug_node
from organized_agent.nodes.generate_fix_node import generate_fix_node
from organized_agent.nodes.run_tests_node import run_tests_node
from organized_agent.nodes.evaluate_result_node import evaluate_result_node
from organized_agent.nodes.log_result_node import log_result_node

def route_result(state: State):
    """Define and compile the LangGraph workflow for the HumanEvalFix agent."""
    retries = state.get("retries", 0)
    result = state.get("result", "fail")

    if retries >= 5:
        print("Max retry limit reached. Logging result and moving on.")
        return "log_result"

    if result == "fail":
        return "analyze_bug"

    return "log_result"


def define_graph():
    """Construct the full LangGraph workflow."""
    graph = StateGraph(State)

    graph.add_node("load_problem", load_problem_node)
    graph.add_node("analyze_bug", analyze_bug_node)
    graph.add_node("generate_fix", generate_fix_node)
    graph.add_node("run_tests", run_tests_node)
    graph.add_node("evaluate_result", evaluate_result_node)
    graph.add_node("log_result", log_result_node)

    graph.add_edge(START, "load_problem")
    graph.add_edge("load_problem", "analyze_bug")
    graph.add_edge("analyze_bug", "generate_fix")
    graph.add_edge("generate_fix", "run_tests")
    graph.add_edge("run_tests", "evaluate_result")
    graph.add_conditional_edges(
        "evaluate_result",
        route_result,
        {
            "analyze_bug": "analyze_bug",
            "log_result": "log_result",
        },
    )

    graph.add_edge("log_result", END)
    return graph
    
def compile_graph():
    """Compile the graph into an executable LangGraph app."""
    graph = define_graph()
    return graph.compile()

def save_graph_visualization(app):
    """Generate and save a PNG visualization of the workflow."""
    try:
        png_graph = app.get_graph().draw_mermaid_png()
        os.makedirs("./reports/flow_graphs", exist_ok=True)
        with open("./reports/flow_graphs/agent_logic_graph.png", "wb") as f:
            f.write(png_graph)
        print("Graph visualization saved to ./reports/flow_graphs/agent_logic_graph.png")
    except Exception as e:
        print("FAILED: Visualization failed:", e)