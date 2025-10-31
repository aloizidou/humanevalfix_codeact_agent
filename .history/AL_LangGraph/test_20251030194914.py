from datasets import load_dataset

ds = load_dataset("bigcode/humanevalpack", "python")["test"]
print(ds[0].keys())
print(ds[0])