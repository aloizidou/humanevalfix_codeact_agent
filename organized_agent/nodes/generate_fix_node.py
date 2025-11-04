from organized_agent.state_schema import State
from organized_agent.agent_helper_toolbox import get_text_response
import re

def generate_fix_node(state: State):
    print("Generating candidate fix...")

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
    9. Ensure that variable types match the expected behavior (e.g., do not mix strings and numbers).
    10. Return values of the correct type as implied by the task description and tests.


    Make sure the function behaves correctly for typical and edge-case inputs implied by the description (e.g., positive, negative, zero, decimal values).
    ### Now output ONLY the corrected function below:

    """

    fixed_code = get_text_response(prompt)

    cleaned_code = (
        fixed_code.replace("```python", "")
        .replace("```", "")
        .strip()
    )

    #  ensuring correct function name for extra safety:
    import re
    if not cleaned_code.strip().startswith(f"def {entry_point}("):
        cleaned_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", cleaned_code)

    state["fixed_code"] = cleaned_code

    print("Generated Fix:\n", state["fixed_code"])
    return state