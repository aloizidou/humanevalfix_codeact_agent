## Agent Logic Flow

This repository implements an LLM-based agent that fixes buggy Python code and evaluates its performance on the Python subset of HumanEvalFix.  
The goal is to test how a small open-source model can reason about, edit, and validate code through an automated process.

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
  <img src="reports/flow_graphs/agent_logic_graph.png" alt="Agent Logic Flow" width="300">
</p>
