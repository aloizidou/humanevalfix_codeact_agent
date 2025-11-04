from datasets import load_dataset
import json

print("Downloading HumanEvalPack")
dataset = load_dataset("bigcode/humanevalpack", "python")["test"]
dataset.to_json("data/raw/humanevalpack_python.jsonl")

print(f"Saved {len(dataset)} tasks to data/raw/humanevalpack_python.jsonl")

def load_humanevalpack_local(subsample: int = None):
    """Load HumanEvalPack locally if available, else download from Hugging Face."""
    local_path = "data/raw/humanevalpack_python.jsonl"
    try:
        with open(local_path) as f:
            data = [json.loads(line) for line in f]
        print(f"Loaded {len(data)} problems from local file.")
        if subsample:
            data = data[:subsample]
        return data
    except FileNotFoundError:
        print("Local file not found, downloading from Hugging Face")
        dataset = load_dataset("bigcode/humanevalpack", "python")["test"]
        dataset.to_json(local_path)
        print(f"Saved {len(dataset)} tasks to {local_path}")
        return dataset[:subsample] if subsample else dataset

