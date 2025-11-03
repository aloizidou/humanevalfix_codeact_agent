from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
import os
from datasets import load_dataset
from dataset import load_humanevalpack_local
from agent_helper_toolbox import get_text_response, log_result_to_jsonl, extract_error_hint
import io
import contextlib
import traceback
import re
from typing import TypedDict, List, Optional, Dict, Any


DATASET = load_humanevalpack_local()

class State(TypedDict):
# --- Metadata about the current task ---
    current_index: int
    problem_id: str
    description: str
    bug_type: str
    failure_symptoms: str

    # --- Core dataset contents ---
    buggy_code: str
    fixed_code: str
    expected_solution: str
    test_code: str
    entry_point: str
    instruction: str

    # --- Agent reasoning & diagnostic info ---
    reasoning: str
    error_hint: str
    test_output: str
    result: str
    last_error: dict        
    error_type: str         
    error_message: str      

    # --- Retry & history management ---
    retries: int
    save_history: bool
    history: list

# Node 1: Load problem 
def load_problem_node(state: State):
    print("=================================")
    print(">>>> Loading problem...")
    print("=================================")

    # Reset transient fields before loading new data
    for key in ["reasoning", "error_hint", "result", "test_output", "last_error", "error_message"]:
        state[key] = ""
    state["retries"] = 0

    index = state.get("current_index", 0)  
    problem = DATASET[index]
    state["problem_id"] = problem["task_id"]
    state["docstring_description"] = problem["docstring"]
    state["buggy_code"] = problem["buggy_solution"]
    state["fixed_code"] = "" 
    state["test_code"] = problem["test"]
    state["entry_point"] = problem["entry_point"]
    state["expected_solution"] = problem["canonical_solution"]
    state["human_question"] = problem["instruction"]
    state["bug_type"] =  problem["bug_type"]
    state["failure_symptoms"] = problem["failure_symptoms"]
    
    print(f"Loaded Problem: {state['problem_id']} - {state['entry_point']}")
    return state

# Node 2: Analyze bug
def analyze_bug_node(state: State):
    print("=================================")
    print(">>>> Analyzing bug using reasoning...")
    print("=================================")

    buggy_code = state.get("buggy_code", "")
    last_fixed = state.get("fixed_code", "")
    docstring_description = state.get("docstring_description", "")
    human_question = state.get("human_question", "")
    entry_point = state.get("entry_point", "")
    bug_type = state.get("bug_type", "")
    error_hint = state.get("error_hint", "")
    last_error = state.get("last_error", {}) or {}

    # Extract structured error info (if available)
    error_type = last_error.get("type", "UnknownError")
    state["error_type"] =  error_type
    error_message = last_error.get("message", "")
    traceback_snippet = (
        "\n".join(last_error.get("traceback", "").splitlines()[-6:])
        if last_error.get("traceback")
        else ""
    )

    prompt = f"""
        You are a Python debugging expert. Analyze why the last version of this function failed its unit tests and explain how to fix it.

        ### Task Description
        {docstring_description}

        ### Human Instruction
        {human_question}

        ### Function Name
        {entry_point}

        ### Bug Type
        {bug_type}

        ### Last Failed Version
        {last_fixed}

        ### Test Feedback
        Error Type: {error_type}
        Error Message: {error_message}
        Hint: {error_hint}
        Traceback (last lines):
        {traceback_snippet}

        ### Expected Output Format
        1. Intended Purpose: Describe clearly what the function should achieve.
        2. Bug Location: Identify where or why the failure occurred.
        3. Error Explanation: Explain the root cause using the error info above.
        4. Suggested Fix (in English): Describe step by step what should be changed, no code.
        5. Edge Case Handling: Note how to handle special cases.

        Rules:
        - Do NOT return any Python code.
        - Be concise and technical.
        - Use the feedback above to guide your reasoning.
        """

    reasoning = get_text_response(prompt)
    state["reasoning"] = reasoning
    print("Reasoning:\n", reasoning)
    return state

# Node 3: Generating Fix based on evaluation of bug
def generate_fix_node(state: State):
    print("=================================")
    print(">>>> Generating fix using reasoning...")
    print("=================================")

    buggy_code = state.get("buggy_code", "")
    reasoning = state.get("reasoning", "")
    description_of_question = state.get("human_question", "")
    entry_point = state.get("entry_point", "")
    docstring_description = state.get("docstring_description", "")

    prompt = f"""
    You are a Python expert. Your task is to fix a buggy function so that it passes all its unit tests.

    ### Problem description
    {description_of_question or docstring_description}

    ### Buggy function
    {buggy_code}

    ### Your previous reasoning
    {reasoning}

    ### Critical requirements:
    1. The function **must keep the exact same name and parameters** as the original:
    - It must start exactly with: def {entry_point}(
    2. The goal of the function is to satisfy the described behavior above.
    3. Do **not** rename variables, remove parameters, or change the return type unless needed for correctness.
    4. Use only the Python standard library (no external imports).
    5. The corrected version must be **logically complete and pass all provided tests**.
    6. Handle edge cases safely (empty lists, zero division, invalid inputs, etc.).
    7. Return **only valid Python code** — no Markdown, explanations, or comments.
    8. Keep the exact same function signature: do not add or remove parameters.

    Make sure the function behaves correctly for typical and edge-case inputs implied by the description (e.g., positive, negative, zero, decimal values).
    ### Now output ONLY the corrected function below:

    """

    fixed_code = get_text_response(prompt)

    # Clean and sanitize model output
    cleaned_code = (
        fixed_code.replace("```python", "")
        .replace("```", "")
        .strip()
    )

    # Extra safety: ensure correct function name
    import re
    if not cleaned_code.strip().startswith(f"def {entry_point}("):
        cleaned_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", cleaned_code)

    state["fixed_code"] = cleaned_code

    print("Generated Fix:\n", state["fixed_code"])
    return state

# Node 4: run tests in sandbox to see if the code is correct
def run_tests_node(state: State):
    print("=================================")
    print(">>>> Running tests on the fixed code...")
    print("=================================")

    import re
    import io
    import contextlib
    import traceback

    # --- Reset transient test data ---
    state["test_output"] = ""
    state["last_error"] = {}
    state["error_type"] = ""
    state["error_message"] = ""

    fixed_code = state.get("fixed_code", "")
    test_code = state.get("test_code", "")
    entry_point = state.get("entry_point", "unknown_function")

    # ==============================================================
    # STEP 1 — Force-correct the function name
    # ==============================================================
    fixed_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", fixed_code)

    # ==============================================================
    # STEP 2 — Syntax validation before running
    # ==============================================================
    try:
        compile(fixed_code, "<string>", "exec")
    except SyntaxError as e:
        state["result"] = "fail"
        state["error_type"] = "SyntaxError"
        state["error_message"] = str(e)
        state["error_hint"] = "SyntaxError: Invalid syntax or indentation."
        state["last_error"] = {
            "type": "SyntaxError",
            "message": str(e),
            "traceback": traceback.format_exc(),
        }
        state["test_output"] = f"SyntaxError before execution: {e}"
        return state

    # ==============================================================
    # STEP 3 — Combine corrected code + dataset tests
    # ==============================================================
    full_code = f"{fixed_code}\n\n{test_code}"

    # ==============================================================
    # STEP 4 — Execute in sandbox and capture output
    # ==============================================================
    namespace = {}
    output_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(full_code, namespace)

        output_text = output_buffer.getvalue().strip()
        state["test_output"] = output_text or "SUCCESS: All tests executed successfully."
        state["result"] = "pass"

        # Clear errors (in case of retry success)
        state["last_error"] = {}
        state["error_type"] = ""
        state["error_message"] = ""
        print(f"SUCCESS ✅: All tests passed for {entry_point}")

    except Exception as e:
        # --- Capture traceback info ---
        error_trace = traceback.format_exc()
        error_type = type(e).__name__
        error_message = str(e)

        if error_type == "AssertionError":
            # Try to extract the failed assertion line
            match = re.search(r"assert\s+(.*?)\n", error_trace)
            if match:
                failed_line = match.group(1).strip()
                error_hint = f"Assertion failed on: {failed_line}"
            else:
                error_hint = "Assertion failed — output does not match expected result."

        state["result"] = "fail"
        state["test_output"] = output_buffer.getvalue().strip() + "\n" + error_trace
        state["last_error"] = {
            "type": error_type,
            "message": error_message,
            "traceback": error_trace,
        }
        state["error_type"] = error_type
        state["error_message"] = error_message

        # --- Generate readable hint ---
        error_hint = extract_error_hint(error_trace, error_type)
        if "positional argument" in error_message:
            error_hint = "Function signature mismatch — ensure correct parameters and name."
        state["error_hint"] = error_hint

        print(f"FAILED ❌: {entry_point} — {error_type}")
        print(f"HINT: {error_hint}\nTRACEBACK:\n{error_trace}")

    return state

# Node 5: evaluate results. If code is wrong loop back to node 2. otherwise log the result. 
def evaluate_result_node(state: State):
    print("=================================")
    print("Evaluating test result...")
    print("=================================")

    result = state.get("result", "unknown")
    retries = state.get("retries", 0)

    if result == "pass":
        print(f"SUCCESS!!! All tests passed for {state.get('problem_id', 'unknown')}")
        state["next_action"] = "log_result"

    else:
        retries += 1
        print(f"FAILED attempt #{retries} — retrying...")
        state["retries"] = retries
        state["next_action"] = "analyze_bug"

    return state

# Node 6: Log result
def log_result_node(state):
    print("=================================")
    print("Logging result...")
    print("=================================")

    print(f"Task {state['problem_id']} completed with result: {state['result']}")
    log_result_to_jsonl(state)
    return state

def route_result(state: State):
    retries = state.get("retries", 0)
    result = state.get("result", "fail")

    # if max retries reached, stop
    if retries >= 2:
        print("Max retry limit reached. Logging result and moving on.")
        return "log_result"

    # if failed, try again
    if result == "fail":
        return "analyze_bug"

    # otherwise success
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
            "analyze_bug": "analyze_bug",
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
        os.makedirs("./reports/flow_graphs", exist_ok=True)
        with open("./reports/flow_graphs/agent_logic_graph.png", "wb") as f:
            f.write(png_graph)
        print("Graph visualization saved to ./reports/flow_graphs/agent_logic_graph.png")
    except Exception as e:
        print("FAILED: Visualization failed:", e)

# if __name__ == "__main__":
# app = compile_graph()
# save_graph_visualization(app)
# state = {}
# # state = {"save_history": True}
# result = app.invoke(state)
# print("\nFinal state:\n", result)

def humanevalfix_batch_run():
    """
    Run all HumanEvalFix problems through the LangGraph agent sequentially.
    """
    app = compile_graph()
    save_graph_visualization(app)
    total = len(DATASET)

    counts = {"pass": 0, "fail": 0}

    for idx in range(total):
        try:
            state = {
                "current_index": idx,
                "retries": 0,
                "save_history": True,
                "history": [],
            }

            result = app.invoke(
                state,
                config={"configurable": {"thread_id": f"problem-{idx}"}}
            )
            print("\nFinal state:\n", result)
            outcome = result.get("result", "fail")
            counts[outcome] = counts.get(outcome, 0) + 1

            print(f"[{idx+1}/{total}] {result.get('problem_id')} → {outcome.upper()}")

        except Exception as e:
            print(f"Error on problem {idx}: {e}")

    print("\n✅ Batch run completed.")
    print("Final counts:", counts)
    
humanevalfix_batch_run()