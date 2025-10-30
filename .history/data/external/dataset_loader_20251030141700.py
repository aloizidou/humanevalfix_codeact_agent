from datasets import load_dataset

def load_humanevalfix_subset(n: int = 1):
    """
    Loads the HumanEvalFix dataset from Hugging Face.
    Returns a small subset (default: 1 sample) for development.
    """
    dataset = load_dataset("bigcode/humanevalfix", split="test")
    subset = dataset.select(range(n))

    problems = []
    for item in subset:
        problems.append({
            "task_id": item["task_id"],
            "prompt": item["prompt"],
            "canonical_solution": item["canonical_solution"],
            "buggy_solution": item["buggy_solution"],
            "test": item["test"],
        })
    
    return problems
