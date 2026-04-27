import csv
from pathlib import Path

INPUT_FILES = [
    Path("data/processed/generated_questions_pattern_a.csv"),
    Path("data/processed/generated_questions_pattern_b_strict.csv"),
    Path("data/processed/generated_questions_pattern_c.csv"),
    Path("data/processed/generated_questions_pattern_d_clean.csv"),
    Path("data/processed/generated_questions_pattern_e.csv"),
]

OUT_FILE = Path("data/processed/final_questions_combined.csv")

all_rows = []
seen = set()

for file_path in INPUT_FILES:
    if not file_path.exists():
        print("Skipping missing file:", file_path)
        continue

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = row.get("question", "").strip()
            answer = row.get("answer", "").strip()
            qtype = row.get("question_type", "").strip()

            if not question or not answer:
                continue

            key = (question.lower(), answer.lower(), qtype.lower())
            if key in seen:
                continue
            seen.add(key)

            all_rows.append({
                "question_type": qtype,
                "question": question,
                "answer": answer,
                "reasoning_path": row.get("reasoning_path", "")
            })

with open(OUT_FILE, "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "question_type",
        "question",
        "answer",
        "reasoning_path"
    ])
    writer.writeheader()
    writer.writerows(all_rows)

print("Final combined question count:", len(all_rows))
print("Saved to:", OUT_FILE)

print("\nFirst 30 final questions:")
for row in all_rows[:30]:
    print("-" * 80)
    print("Type:", row["question_type"])
    print("Q:", row["question"])
    print("A:", row["answer"])
    print("Path:", row["reasoning_path"])