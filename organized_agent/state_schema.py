from typing import TypedDict, List, Dict, Any

""" Define the shared state structure for the LangGraph agent. """
class State(TypedDict):
    # Metadata
    current_index: int
    problem_id: str
    description: str
    bug_type: str
    failure_symptoms: str

    # Core dataset
    buggy_code: str
    fixed_code: str
    expected_solution: str
    test_code: str
    entry_point: str
    instruction: str

    # Reasoning & diagnostics
    reasoning: str
    error_hint: str
    test_output: str
    result: str
    last_error: dict
    error_type: str
    error_message: str

    # Retry & history
    retries: int
    save_history: bool
    history: list
