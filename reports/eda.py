import pandas as pd

df = pd.read_json("data/processed/results_log1.jsonl", lines=True)

# counts by result
counts = df["result"].value_counts()
print("Counts by result:")
print(counts)
print()

# error_type counts
fail_df = df[df["result"] == "fail"]
error_type_counts = fail_df["error_type"].value_counts()
print("Error types when result == fail:")
print(error_type_counts)
print()

# for failures only: error_hint top counts
error_hint_counts = fail_df["error_hint"].value_counts()
print("Top error hints when result == fail:")
print(error_hint_counts)

# retry distribution
retry_counts = df["retries"].value_counts().sort_index()
print("Retry count distribution:")
print(retry_counts)

