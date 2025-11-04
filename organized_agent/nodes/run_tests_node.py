from organized_agent.state_schema import State
from organized_agent.agent_helper_toolbox import extract_error_hint
import re
import io
import contextlib
import traceback

def run_tests_node(state: State):
    
    print(f"Running tests for {state.get('problem_id', 'unknown')}")

    state["test_output"] = ""
    state["last_error"] = {}
    state["error_type"] = ""
    state["error_message"] = ""

    fixed_code = state.get("fixed_code", "")
    test_code = state.get("test_code", "")
    entry_point = state.get("entry_point", "unknown_function")

    # correct the function name
    fixed_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", fixed_code)

    # syntax validation before running
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

    # combining corrected code + dataset tests
    full_code = f"{fixed_code}\n\n{test_code}"

    # execute in sandbox and capture output
    namespace = {}
    output_buffer = io.StringIO()

    try:
        with contextlib.redirect_stdout(output_buffer):
            exec(full_code, namespace)

        output_text = output_buffer.getvalue().strip()
        state["test_output"] = output_text or "SUCCESS: All tests executed successfully."
        state["result"] = "pass"

        # elear errors (in case of retry success)
        state["last_error"] = {}
        state["error_type"] = ""
        state["error_message"] = ""
        print(f"All tests passed for {entry_point}")

    except Exception as e:

        error_trace = traceback.format_exc()
        error_type = type(e).__name__
        error_message = str(e)

        # getting failed assertion line if no message exists
        if error_type == "AssertionError" and not error_message:
            tb_lines = error_trace.splitlines()
            failed_line = ""
            for line in reversed(tb_lines):
                if line.strip().startswith("assert "):
                    failed_line = line.strip()
                    break
            if failed_line:
                error_message = f"Failed assertion: {failed_line}"

        state["result"] = "fail"
        state["test_output"] = output_buffer.getvalue().strip() + "\n" + error_trace
        state["last_error"] = {
            "type": error_type,
            "message": error_message,
            "traceback": error_trace,
        }
        state["error_type"] = error_type
        state["error_message"] = error_message
        
        # generating hint
        error_hint = extract_error_hint(error_trace, error_type)
        if "positional argument" in error_message:
            error_hint = "Function signature mismatch — ensure correct parameters and name."
        state["error_hint"] = error_hint

        print(f"Failed: {entry_point} — {error_type}")
        print(f"Hint: {error_hint}\nTRACEBACK:\n{error_trace}")

    return state