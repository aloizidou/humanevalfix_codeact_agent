from openai import OpenAI
import os
import json
from datetime import datetime
import re


client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MODEL = "gemma3:4b"
TEMPERATURE = 0.5 

PROCESSED_DIR = os.path.join("data", "processed")
RESULTS_FILE = os.path.join(PROCESSED_DIR, "results_log.jsonl")
os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_text_response(prompt: str) -> str:
    """Get text response from LLM which will help with our logical reasoning"""
    system_message = {
        "role": "system",
        "content": "You are an expert Python code analyst. Be concise and technical."
    }
    user_message = {"role": "user", "content": prompt}

    response = client.chat.completions.create(
        model=MODEL,
        messages=[system_message, user_message],
        temperature=TEMPERATURE,
    )
    return response.choices[0].message.content.strip()

def log_result_to_jsonl(state: dict):
    """
    Append the final state (or relevant info) to results_log.jsonl.
    Keeps one JSON object per line.
    """
    record = {
        "task_id": state.get("problem_id"),
        "result": state.get("result"),
        "retries": state.get("retries"),
        "failure_symptoms": state.get("failure_symptoms"),
        "bug_type": state.get("bug_type"),
        "error_type": state.get("error_type"),
        "error_hint": state.get("error_hint"),
        "reasoning": state.get("reasoning"),
        "fixed_code": state.get("fixed_code"),
        "test_output": state.get("test_output"),
        "entry_point": state.get("entry_point"),
        "timestamp": datetime.now().isoformat(),
    }

    with open(RESULTS_FILE, "a") as f:
        json.dump(record, f)
        f.write("\n")

    print(f"Logged result for {record['task_id']} to {RESULTS_FILE}")

def extract_error_hint(test_output: str, error_type: str = None) -> str:
    """
    Analyze test output or traceback text and return a short human-readable hint.
    Uses both the traceback string and the Python exception type if available.
    """

    if not test_output and not error_type:
        return "No error detected."

    error_patterns = {
        "IndexError": "IndexError: The code likely uses an invalid index. Ensure loop bounds and list accesses are safe.",
        "AssertionError": "AssertionError: The output does not match expected results. Recheck logic or return values. This means we run some tests and the code did not pass — make sure you include edge cases.",
        "TypeError": "TypeError: Check for invalid operations or mismatched data types (e.g., int + str).",
        "ValueError": "ValueError: Ensure inputs are valid and conversions (like int() or float()) are handled safely.",
        "KeyError": "KeyError: Dictionary key might be missing. Use dict.get() or check keys before access.",
        "NameError": "NameError: Some variable or function is NOT defined, or defined wrongly. Make sure all identifiers are declared.",
        "SyntaxError": "SyntaxError: Generated code may have invalid Python syntax. Recheck indentation, parentheses, or missing colons.",
        "ZeroDivisionError": "ZeroDivisionError: Avoid dividing by zero — add a conditional guard.",
        "RecursionError": "RecursionError: Infinite recursion detected — add base conditions or iterative logic."
    }

    # Step 1 — look for known error names in the traceback
    for error_key, hint in error_patterns.items():
        if re.search(error_key, test_output or ""):
            return hint

    # Step 2 — fallback to using the explicit error type
    if error_type and error_type in error_patterns:
        return error_patterns[error_type]

    # Step 3 — default fallback
    return "Unknown error encountered. Review traceback for details."

