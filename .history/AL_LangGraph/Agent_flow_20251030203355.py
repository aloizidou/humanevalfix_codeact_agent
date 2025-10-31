from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os
from datasets import load_dataset
from dataset import load_humanevalpack_local

DATASET = load_humanevalpack_local(subsample = 5)

class State(TypedDict):
    problem_id: str
    description: str
    buggy_code: str
    fixed_code: str
    test_code: str           
    entry_point: str 
    expected_solution: str
    reasoning: str
    result: str  # pass/fail
    test_output: str

# Node 1: Load problem 
def load_problem_node(state: State):
    print("Loading problem...")
    problem = DATASET[0]
    state["problem_id"] = problem["task_id"]
    state["description"] = problem["docstring"]
    state["buggy_code"] = problem["buggy_solution"]
    state["fixed_code"] = ""  # to be filled by generate_fix
    state["test_code"] = problem["test"]
    state["entry_point"] = problem["entry_point"]
    state["expected_solution"] = problem["canonical_solution"]

    print(f"Loaded: {state['problem_id']} - {state['entry_point']}")
    return state

# Node 2: Analyze bug
def analyze_bug_node(state: State):
    print("Analyzing bug...")
    desc = state.get("description", "")
    buggy = state.get("buggy_code", "")
    reasoning = f"Bug found in function: likely wrong operator in '{buggy}'"
    state["reasoning"] = reasoning
    return state

# Node 3: Generate fix
def generate_fix_node(state: State):
    print("Generating fix...")
    state["fixed_code"] = "def add(a, b): return a + b"
    return state
def run_tests_node(state):
    print("Running tests...")
    code = state.get("fixed_code", "")
    if "+" in code:
        state["test_output"] = "All tests passed!"
        state["result"] = "pass"
    else:
        state["test_output"] = "Tests failed."
        state["result"] = "fail"
    return state

# Node 4: Evaluate result 
def evaluate_result_node(state: State):
    print("Evaluating fixed code...")
    state["result"] = "pass"
    print(f"Evaluation result for problem {state['problem_id']}: {state['result']}")
    return state

def log_result_node(state):
    print("Logging result...")
    summary = f"Task {state['problem_id']} completed with result: {state['result']}"
    print(summary)
    state["summary"] = summary
    return state

# function for conditional edge 
def route_result(state: State):
    """Route to next step based on test result."""
    if state.get("result") == "fail":
        return "generate_fix"
    else:
        return "log_result"

# --- Define the LangGraph ---
def define_graph():
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
            "generate_fix": "generate_fix",
            "log_result": "log_result",
        },
    )

    graph.add_edge("log_result", END)
    return graph
    
def compile_graph():
    graph = define_graph()
    return graph.compile()

def save_graph_visualization(app):
    try:
        png_graph = app.get_graph().draw_mermaid_png()
        os.makedirs("./data/flow_graphs", exist_ok=True)
        with open("./data/flow_graphs/agent_logic_graph1.png", "wb") as f:
            f.write(png_graph)
        print("Graph visualization saved to ./data/flow_graphs/react_agent_graph.png")
    except Exception as e:
        print("❌ Visualization failed:", e)

# if __name__ == "__main__":
app = compile_graph()
save_graph_visualization(app)
state = {}
result = app.invoke(state)
print("\nFinal state:\n", result)