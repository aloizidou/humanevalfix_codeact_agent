from organized_agent.state_schema import State
from organized_agent.dataset_loader import load_humanevalpack_local


DATASET = load_humanevalpack_local()
def load_problem_node(state: State):
    """Load the current problem into the agent state."""
    print(f"Loading problem {state.get('current_index', 0)}")

    # reseting fields before loading new data, because we don't want to pass reasoning from another problem
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