import json

file_path = "data/processed/results_log.jsonl"

total = 0
passed = 0

with open(file_path, "r") as f:
    for line in f:
        record = json.loads(line)
        result = record.get("result", "").strip().lower()
        total += 1
        if result == "pass":
            passed += 1

if total > 0:
    pass_at_1 = passed / total
    print(f"pass@1: {pass_at_1:.3f} ({passed}/{total})")
else:
    print("No entries found in the file.")
