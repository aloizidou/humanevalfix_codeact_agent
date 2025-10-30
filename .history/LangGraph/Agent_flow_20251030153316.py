from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os

# --- State ---
class State(TypedDict):
    problem_id: str
    description: str
    buggy_code: str
    fixed_code: str
    reasoning: str
    result: str  # pass/fail

# --- Node 1: Load problem ---
def load_problem_node(state: State):
    print("Loading problem...")
    # Dummy data for now
    state["problem_id"] = "001"
    state["description"] = "Add two numbers"
    state["buggy_code"] = "def add(a, b): return a - b"
    return state

# --- Node 2: Analyze bug ---
def analyze_bug_node(state: State):
    print("Analyzing bug...")
    desc = state.get("description", "")
    buggy = state.get("buggy_code", "")
    # Placeholder logic
    reasoning = f"Bug found in function: likely wrong operator in '{buggy}'"
    state["reasoning"] = reasoning
    return state

# --- Node 3: Generate fix ---
def generate_fix_node(state: State):
    print("Generating fix...")
    # Dummy corrected code
    state["fixed_code"] = "def add(a, b): return a + b"
    return state

# --- Node 4: Evaluate result ---
def evaluate_result_node(state: State):
    print("Evaluating fixed code...")
    # Dummy evaluation logic
    state["result"] = "pass"
    print(f"✅ Evaluation result for problem {state['problem_id']}: {state['result']}")
    return state

# --- Define the LangGraph ---
def define_graph():
    graph = StateGraph(State)

    # Nodes
    graph.add_node("load_problem", load_problem_node)
    graph.add_node("analyze_bug", analyze_bug_node)
    graph.add_node("generate_fix", generate_fix_node)
    graph.add_node("evaluate_result", evaluate_result_node)

    # Edges (flow)
    graph.add_edge(START, "load_problem")
    graph.add_edge("load_problem", "analyze_bug")
    graph.add_edge("analyze_bug", "generate_fix")
    graph.add_edge("generate_fix", "evaluate_result")
    graph.add_edge("evaluate_result", END)

    return graph

# --- Compile graph ---
def compile_graph():
    graph = define_graph()
    return graph.compile()

# --- Save Graph Visualization ---
def save_graph_visualization(app):
    """Save LangGraph structure as a PNG image."""
    try:
        png_graph = app.get_graph().draw_mermaid_png()
        os.makedirs("./data/flow_graphs", exist_ok=True)

        if png_graph:
            with open("./data/flow_graphs/flow_graph1.png", "wb") as f:
                f.write(png_graph)
            print("✅ Graph visualization saved to ./data/flow_graphs/flow_graph1.png")
        else:
            print("⚠️ No graph data returned!")
    except Exception as e:
        print("❌ Failed to save graph visualization:", e)

# --- Run graph ---
if __name__ == "__main__":
    app = compile_graph()
    save_graph_visualization(app)
    state = {}
    result = app.invoke(state)
    print("\nFinal state:\n", result)
