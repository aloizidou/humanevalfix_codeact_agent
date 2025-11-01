from openai import OpenAI
import os
import json
from datetime import datetime

# --- File paths ---
PROCESSED_DIR = os.path.join("data", "processed")
RESULTS_FILE = os.path.join(PROCESSED_DIR, "results_log.jsonl")

os.makedirs(PROCESSED_DIR, exist_ok=True)


client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

MODEL = "gemma3:4b"
TEMPERATURE = 0.6  

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
        "timestamp": datetime.now().isoformat(),
        "task_id": state.get("problem_id"),
        "result": state.get("result"),
        "bug_type": state.get("bug_type"),
        "entry_point": state.get("entry_point"),
        "reasoning": state.get("reasoning"),
        "fixed_code": state.get("fixed_code"),
        "test_output": state.get("test_output"),
        "error": state.get("error"),
    }

    with open(RESULTS_FILE, "a") as f:
        json.dump(record, f)
        f.write("\n")

    print(f"Logged result for {record['task_id']} to {RESULTS_FILE}")


def load_all_results():
    """
    Load all saved records from the JSONL file.
    Returns a list of dictionaries.
    """
    if not os.path.exists(RESULTS_FILE):
        print("No results found yet.")
        return []

    with open(RESULTS_FILE, "r") as f:
        return [json.loads(line) for line in f]

import re

def extract_error_hint(test_output: str) -> str:
    """
    Analyze test output or traceback text and return a short human-readable hint.
    """
    if not test_output:
        return "No error detected."

    error_patterns = {
        "IndexError": "IndexError: The code likely uses an invalid index. Ensure loop bounds and list accesses are safe.",
        "AssertionError": "AssertionError: The output does not match expected results. Recheck logic or return values.",
        "TypeError": "TypeError: Check for invalid operations or mismatched data types (e.g., int + str).",
        "ValueError": "ValueError: Ensure inputs are valid and conversions (like int() or float()) are handled safely.",
        "KeyError": "KeyError: Dictionary key might be missing. Use dict.get() or check keys before access.",
        "NameError": "NameError: Some variable or function is undefined. Make sure all identifiers are declared.",
        "SyntaxError": "SyntaxError: Generated code may have invalid Python syntax. Recheck indentation or missing colons.",
        "ZeroDivisionError": "ZeroDivisionError: Avoid dividing by zero — add a conditional guard.",
        "RecursionError": "RecursionError: Infinite recursion detected — add base conditions or iterative logic."
    }

    # Find first matching known error
    for error_type, hint in error_patterns.items():
        if re.search(error_type, test_output):
            return hint

    # Default fallback if unknown error
    return "Unknown error encountered. Review test output for clues."
