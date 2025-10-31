from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os
from datasets import load_dataset
from dataset import load_humanevalpack_local
from agent_helper_toolbox import get_text_response
import io
import contextlib
import traceback
import re

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
    result: str  
    test_output: str
    history:list 

# Node 1: Load problem 
def load_problem_node(state: State):
    print("Loading problem...")
    problem = DATASET[0]
    state["problem_id"] = problem["task_id"]
    state["docstring_description"] = problem["docstring"]
    state["buggy_code"] = problem["buggy_solution"]
    state["fixed_code"] = ""  # to be filled by generate_fix
    state["test_code"] = problem["test"]
    state["entry_point"] = problem["entry_point"]
    state["expected_solution"] = problem["canonical_solution"]

    print(f"Loaded Problem: {state['problem_id']} - {state['entry_point']}")
    return state

# Node 2 - Analyze the bug 
def analyze_bug_node(state: State):
    print("Analyzing bug with gemma reasoning...")

    buggy_code = state.get("buggy_code", "")
    description = state.get("docstring_description", "")

    prompt = f"""
    You are a Python code expert.
    Find and explain the bug in this code.

    Problem description:
    {description}

    Buggy code:
    {buggy_code}

    Explain what is wrong in the code and what should be changed.
    """
    reasoning = get_text_response(prompt)
    state["reasoning"] = reasoning
    print("Reasoning:", reasoning)
    return state

# Node 3 - here we Generate the correction 
def generate_fix_node(state: State):
    print("Generating fix using reasoning...")

    buggy_code = state.get("buggy_code", "")
    reasoning = state.get("reasoning", "")

    prompt = f"""
    You are a Python expert tasked with fixing code bugs.

    Buggy code:
    {buggy_code}

    Reasoning about the bug:
    {reasoning}

    Now write ONLY the corrected Python function code.
    Do not include explanations or Markdown code blocks.
    """
    fixed_code = get_text_response(prompt)
    cleaned_code = re.sub(r"```.*?```", lambda m: m.group(0).replace("```python", "").replace("```", ""), fixed_code, flags=re.S)
    state["fixed_code"] = cleaned_code.strip()

    print("Generated Fix:\n", state["fixed_code"])
    return state


def run_tests_node(state):
    print("🧪 Running real tests from dataset...")

    fixed_code = state.get("fixed_code", "")
    test_code = state.get("test_code", "")
    entry_point = state.get("entry_point", "unknown_function")
    fixed_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", fixed_code)
    # Combine the code and tests
    full_code = f"{fixed_code}\n\n{test_code}"

    # Sandbox setup
    namespace = {}

    try:
        # Capture stdout (for print output)
        output_buffer = io.StringIO()
        with contextlib.redirect_stdout(output_buffer):
            print("🧠 Final code being tested:\n", full_code)

            exec(full_code, namespace)

        # If no errors raised, all tests passed
        output_text = output_buffer.getvalue()
        state["test_output"] = output_text or "✅ All tests executed successfully."
        state["result"] = "pass"
        print(f"✅ All tests passed for {entry_point}")

    except Exception as e:
        # Capture traceback for debugging
        error_trace = traceback.format_exc()
        state["test_output"] = f"❌ Test failure:\n{error_trace}"
        state["result"] = "fail"
        print(f"❌ Tests failed for {entry_point}\n{error_trace}")

    return state


# Node 4: Evaluate result 
# def evaluate_result_node(state: State):
#     print("Evaluating test result...")

#     result = state.get("result", "unknown")
#     test_output = state.get("test_output", "")
#     retries = state.get("retries", 0)

#     if result == "pass":
#         print(f"✅ All tests passed for problem {state.get('problem_id', 'unknown')}")
#         state["next_action"] = "log_result"
#     else:
#         print(f"❌ Tests failed. Passing error info back to fixer...")
#         state["next_action"] = "generate_fix"
#         state["error_feedback"] = test_output
#         state["retries"] = retries + 1

#     return state

def evaluate_result_node(state: State):
    print("🧮 Evaluating test result...")

    result = state.get("result", "unknown")
    test_output = state.get("test_output", "")
    retries = state.get("retries", 0)

    # Optional history setup
    if state.get("save_history", False):
        history = state.get("history", [])
        history.append({
            "attempt": retries + 1,
            "fixed_code": state.get("fixed_code", ""),
            "reasoning": state.get("reasoning", ""),
            "result": result,
            "test_feedback": test_output[:300]  # keep first 300 chars for readability
        })
        state["history"] = history

    if result == "pass":
        print(f"✅ All tests passed for problem {state.get('problem_id', 'unknown')}")
        state["next_action"] = "log_result"
    else:
        print(f"❌ Tests failed. Passing error info back to fixer...")
        state["next_action"] = "generate_fix"
        state["error_feedback"] = test_output
        state["retries"] = retries + 1

    return state



def log_result_node(state):
    print("Logging result...")
    summary = f"Task {state['problem_id']} completed with result: {state['result']}"
    print(summary)
    state["summary"] = summary
    return state

# function for conditional edge 
# def route_result(state: State):
#     """Route to next step based on test result."""
#     if state.get("result") == "fail":
#         return "generate_fix"
#     else:
#         return "log_result"
def route_result(state: State):
    """Route to next step based on evaluation outcome."""
    next_action = state.get("next_action", "log_result")
    retries = state.get("retries", 0)

    # Stop endless loops
    if retries >= 3:
        print("Max retry limit reached. Logging result and moving on.")
        return "log_result"

    return next_action


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
        with open("./data/flow_graphs/agent_logic_graph.png", "wb") as f:
            f.write(png_graph)
        print("Graph visualization saved to ./data/flow_graphs/agent_logic_graph.png")
    except Exception as e:
        print("❌ Visualization failed:", e)

# if __name__ == "__main__":
app = compile_graph()
save_graph_visualization(app)
# state = {}
state = {"save_history": True}

result = app.invoke(state)
# print("\nFinal state:\n", result)