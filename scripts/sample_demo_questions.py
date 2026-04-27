import csv
from pathlib import Path
from collections import defaultdict

IN_FILE = Path("data/processed/final_questions_combined.csv")
OUT_FILE = Path("data/processed/final_questions_demo.csv")

grouped = defaultdict(list)

with open(IN_FILE, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        grouped[row["question_type"]].append(row)

demo_rows = []
for qtype, rows in grouped.items():
    demo_rows.extend(rows[:8])  # her pattern'den ilk 8 örnek

with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "question_type",
        "question",
        "answer",
        "reasoning_path"
    ])
    writer.writeheader()
    writer.writerows(demo_rows)

print("Demo question count:", len(demo_rows))
print("Saved to:", OUT_FILE)

for row in demo_rows[:20]:
    print("-" * 80)
    print(row["question_type"])
    print("Q:", row["question"])
    print("A:", row["answer"])