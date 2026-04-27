from pathlib import Path
from collections import Counter
import csv

RAW = Path("data/raw")
SUBSET = Path("data/subset")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

RELATION_FILE = RAW / "wikidata5m_relation.txt"
TRIPLET_FILE = RAW / "wikidata5m_all_triplet.txt"
TURKIYE_TRIPLE_FILE = SUBSET / "turkiye_general_triples.csv"

relations = {}

print("Loading relation dictionary...")
with open(RELATION_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            rid, rname = parts[0], parts[1]
            relations[rid] = rname

# 1) Global raw relation frequency
print("Scanning global raw triplets...")
global_counter = Counter()

with open(TRIPLET_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        _, r, _ = parts
        global_counter[relations.get(r, r)] += 1

# 2) Türkiye subset relation frequency
subset_counter = Counter()

if TURKIYE_TRIPLE_FILE.exists():
    print("Scanning Türkiye subset triples...")
    with open(TURKIYE_TRIPLE_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            subset_counter[row["relation_name"]] += 1
else:
    print("WARNING: Türkiye subset triple file not found:", TURKIYE_TRIPLE_FILE)

# 3) Save results
global_out = OUT / "relation_frequency_global.csv"
subset_out = OUT / "relation_frequency_turkiye_subset.csv"

with open(global_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["relation_name", "count"])
    for rel, cnt in global_counter.most_common():
        writer.writerow([rel, cnt])

with open(subset_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["relation_name", "count"])
    for rel, cnt in subset_counter.most_common():
        writer.writerow([rel, cnt])

print("\nTop 30 global relations:")
for rel, cnt in global_counter.most_common(30):
    print(rel, ":", cnt)

print("\nTop 30 Türkiye-subset relations:")
for rel, cnt in subset_counter.most_common(30):
    print(rel, ":", cnt)

# 4) Domain-guided recommended relation set
recommended_keywords = [
    "country",
    "citizenship",
    "birth",
    "head",
    "coach",
    "manager",
    "venue",
    "league",
    "director",
    "educated",
    "award",
    "cast",
    "location",
    "sport",
    "occupation",
    "industry",
    "genre",
    "label",
]

recommended = []
for rel, cnt in subset_counter.most_common():
    low = rel.lower()
    if any(k in low for k in recommended_keywords):
        recommended.append((rel, cnt))

recommended_out = OUT / "relation_recommendations_for_backend.csv"
with open(recommended_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["relation_name", "count"])
    for rel, cnt in recommended:
        writer.writerow([rel, cnt])

print("\nRecommended relations for backend:")
for rel, cnt in recommended:
    print(rel, ":", cnt)

print("\nSaved files:")
print("-", global_out)
print("-", subset_out)
print("-", recommended_out)