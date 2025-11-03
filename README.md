## Agent Logic Flow

This repository implements an LLM-based agent that fixes buggy Python code and evaluates its performance on the Python subset of HumanEvalFix.  
The goal is to test how a small open-source model can reason about, edit, and validate code through an automated process.

load_problem 
→ analyze_bug 
→ generate_fix 
→ run_tests 
→ evaluate_result 
     ↳ if pass → log_result
     ↳ if fail → analyze_bug (with test failure info added)


### Overview
The agent follows a ReAct-style workflow:
1. Load the problem from HumanEvalFix.
2. Analyze the bug.
3. Generate a fix using the language model.
4. Run tests in a sandboxed environment.
5. Evaluate the result using the pass@1 metric.
6. Log the outcome.

### Framework and Model
- Framework: LangGraph  
- Agent type: ReAct-style agent with a code interpreter tool  
- Model: qwen2.5vl:7b 

### Evaluation
- Benchmark: Python subset of HumanEvalFix   
- Metric: pass@1  
- Safe execution with sandboxing  
- Optionally run on a representative subset if needed  

### Flow Diagram
The diagram below shows the logic of the agent pipeline:

<p align="center">
  <img src="reports/flow_graphs/agent_logic_graph.png" alt="Agent Logic Flow" width="180">
</p>


 generate_fix → run_tests → evaluate_result 
    ↳ if fail → find_possible_hints_for_error → analyze_bug → generate_fix
    ↳ if pass → log_result


graph.add_conditional_edges(
    "evaluate_result",
    route_result,
    {
        "find_error_hints": "find_error_hints_node",
        "log_result": "log_result",
    },
)

graph.add_edge("find_error_hints_node", "analyze_bug")
graph.add_edge("analyze_bug", "generate_fix")

small-scale AI agent that:
1. Takes buggy Python code as input,
2. Automatically fixes it using an LLM,
3. Tests whether the fix works,
4. And reports the model’s performance using the Python subset of HumanEvalFix (a benchmark dataset of buggy Python functions and their expected fixes).

Instructions on how to run it and reproduce your evaluation results




>> Code Injection via exec() Without Assertions
Symptom: Some fixes “pass” instantly with no output, but are actually incorrect.
Root cause:
If the test_code in HumanEvalFix doesn’t raise an error explicitly, the agent thinks it “passed.”
→ Fix:
Ensure your test runner explicitly asserts results.
You can wrap execution like this:


assert namespace[entry_point],


🧭 Key Insights from Failures
1️⃣ Most common corruption fields
reasoning
error_hint
last_error
If any of these persist between problems, the next iteration starts with irrelevant context — producing broken or irrelevant fixes.
2️⃣ Most common missing data
last_error (should contain structured info: type, message, traceback, line).
error_hint often oversimplified.
Without them, your next reasoning round is like:
“The test failed, but I don’t know why”
→ LLM guesses incorrectly → repeated failure.
3️⃣ Most common structural issue
fixed_code not matching the required signature (def entry_point().
generate_fix_node prompt sometimes outputs Markdown or adds print statements that break the test suite.


Layer	Specific Fix
🧠 Prompt logic (generate_fix_node)	Strengthen your prompt to include exact signature enforcement. 
Example: 
text<br>The function must be named exactly: def has_close_elements(numbers, threshold):<br>It should determine whether any two numbers are within the threshold distance.<br>Do not change its name or parameter list.<br>
🔍 Error analysis (extract_error_hint)	Detect argument mismatch more precisely: 
python<br>if "positional argument" in test_output: return "Function signature mismatch — ensure correct parameter names and count."<br>
🧩 Test runner (run_tests_node)	Force-replace the function name and ensure parameter list matches before executing tests: 
python<br>fixed_code = re.sub(r"def\s+\w+\s*\(", f"def {entry_point}(", fixed_code)<br>
🪞Reasoning step (analyze_bug_node)	Feed last_error["message"] and error_hint explicitly to the reasoning LLM. It should see: 
\nLast error: TypeError: has_close_elements() takes 1 positional argument but 2 were given.\n
📜 State cleanup	Ensure error_hint and reasoning are cleared at the start of each new problem.
🧾 Optional validation	Compare parameter counts between expected_solution and fixed_code. If mismatch, auto-add missing parameters before testing.
