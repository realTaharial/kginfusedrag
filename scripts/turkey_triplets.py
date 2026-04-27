from pathlib import Path
import csv

RAW = Path("data/raw")
OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

triplet_file = RAW / "wikidata5m_all_triplet.txt"
relation_file = RAW / "wikidata5m_relation.txt"
entity_file = RAW / "wikidata5m_entity.txt"

target_id = "Q43"

relations = {}
entities = {}

print("Loading relation names...")
with open(relation_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            relations[parts[0]] = parts[1]

print("Loading entity names...")
with open(entity_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            entities[parts[0]] = parts[1]

rows = []
count = 0

print("Scanning triples...")
with open(triplet_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) == 3:
            s, r, o = parts
            if s == target_id or o == target_id:
                rows.append([
                    s,
                    entities.get(s, s),
                    r,
                    relations.get(r, r),
                    o,
                    entities.get(o, o)
                ])
                count += 1

print("Matched triples:", count)

out_file = OUT / "q43_related_triples.csv"
with open(out_file, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "subject_id", "subject_name",
        "relation_id", "relation_name",
        "object_id", "object_name"
    ])
    writer.writerows(rows)

print("Saved to:", out_file)
print("First 20 rows:")
for row in rows[:20]:
    print(row)