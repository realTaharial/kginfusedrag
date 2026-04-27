from pathlib import Path
from collections import Counter

RAW = Path("data/raw")

triplet_file = RAW / "wikidata5m_all_triplet.txt"
relation_file = RAW / "wikidata5m_relation.txt"

target_id = "Q43"

relations = {}
with open(relation_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            relations[parts[0]] = parts[1]

counter = Counter()

with open(triplet_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 3:
            s, r, o = parts
            if o == target_id:
                counter[r] += 1

print("Top 30 relations pointing to Q43:")
for rel_id, cnt in counter.most_common(30):
    print(rel_id, "->", relations.get(rel_id, rel_id), ":", cnt)