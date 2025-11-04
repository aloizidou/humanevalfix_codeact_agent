from organized_agent.state_schema import State
from organized_agent.agent_helper_toolbox import log_result_to_jsonl

def log_result_node(state):
    
    print("Logging result")
    print(f"Task {state['problem_id']} completed with result: {state['result']}")
    log_result_to_jsonl(state)

    return state