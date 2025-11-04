from organized_agent.graph_definition import compile_graph, save_graph_visualization
from organized_agent.dataset_loader import load_humanevalpack_local 

def humanevalfix_batch_run():
    """Run the LangGraph agent on the HumanEvalFix dataset and report results."""
    DATASET = load_humanevalpack_local()
    app = compile_graph()
    save_graph_visualization(app)
    total = len(DATASET)

    counts = {"pass": 0, "fail": 0}

    for idx in range(total):
        try:
            state = {
                "current_index": idx,
                "retries": 0,
                "save_history": True,
                "history": [],
            }

            result = app.invoke(
                state,
                config={"configurable": {"thread_id": f"problem-{idx}"}}
            )
            print("\nFinal state:\n", result)
            outcome = result.get("result", "fail")
            counts[outcome] = counts.get(outcome, 0) + 1

            print(f"[{idx+1}/{total}] {result.get('problem_id')} → {outcome.upper()}")

        except Exception as e:
            print(f"Error on problem {idx}: {e}")
    
    # Compute pass@1 metric
    total_attempted = counts["pass"] + counts["fail"]
    pass_at_1 = (counts["pass"] / total_attempted) * 100 if total_attempted > 0 else 0.0

    print("\nBatch run completed.")
    print("Final counts:", counts)
    print(f"Pass@1: {pass_at_1:.2f}%")
    
humanevalfix_batch_run()