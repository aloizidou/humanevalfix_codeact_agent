from datasets import load_dataset

print("Downloading HumanEvalPack (Python subset)...")
dataset = load_dataset("bigcode/humanevalpack", "python")["test"]
dataset.to_json("data/raw/humanevalpack_python.jsonl")

print(f"Saved {len(dataset)} tasks to data/raw/humanevalpack_python.jsonl")
