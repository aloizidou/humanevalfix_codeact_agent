from organized_agent.state_schema import State
from organized_agent.agent_helper_toolbox import get_text_response
import traceback

def analyze_bug_node(state: State):
    """Use model reasoning to identify the cause of failure and suggest improvements."""

    print("Analyzing bug...")

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

        If the error type is TypeError, review the function’s parameter list and operations to ensure they match expected input types.
        Possible causes: wrong parameter count, incompatible operations (e.g., int + str), "
        or incorrect return type.


        Rules:
        - Do NOT return any Python code.
        - Be concise and technical.
        - Use the feedback above to guide your reasoning.
        """

    reasoning = get_text_response(prompt)
    state["reasoning"] = reasoning
    print("Reasoning:\n", reasoning)
    return state