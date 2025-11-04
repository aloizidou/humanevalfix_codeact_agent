from organized_agent.state_schema import State

def evaluate_result_node(state: State):
    
    print("Evaluating test result...")
    result = state.get("result", "unknown")
    retries = state.get("retries", 0)

    if result == "pass":
        print(f"SUCCESS! All tests passed for {state.get('problem_id', 'unknown')}")
        state["next_action"] = "log_result"

    else:
        retries += 1
        print(f"FAILED attempt #{retries} — retrying...")
        state["retries"] = retries
        state["next_action"] = "analyze_bug"

    return state