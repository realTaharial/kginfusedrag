from pathlib import Path
import csv
from collections import Counter

RAW = Path("data/raw")
OUT = Path("data/processed")
SUBSET = Path("data/subset")
OUT.mkdir(parents=True, exist_ok=True)
SUBSET.mkdir(parents=True, exist_ok=True)

TRIPLET_FILE = RAW / "wikidata5m_all_triplet.txt"
ENTITY_FILE = RAW / "wikidata5m_entity.txt"
RELATION_FILE = RAW / "wikidata5m_relation.txt"
TEXT_FILE = RAW / "wikidata5m_text.txt"

TURKIYE_ID = "Q43"

# Burada artık relation’ları çok dar elle seçmiyoruz.
# Sadece tamamen aşırı gürültülü birkaç taneyi blacklist edeceğiz.
BLACKLIST_RELATIONS = {
    "given name",
    "family name",
    "follows",
    "followed by",
    "taxon rank",
    "parent taxon",
}

print("Loading entities...")
entities = {}
with open(ENTITY_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            entities[parts[0]] = parts[1]

print("Loading descriptions...")
descriptions = {}
with open(TEXT_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            descriptions[parts[0]] = parts[1]

print("Loading relations...")
relations = {}
with open(RELATION_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            relations[parts[0]] = parts[1]

# 1) Türkiye'ye doğrudan bağlı triplelar
print("Scanning direct Türkiye-connected triples...")
direct_rows = []
direct_entities = {TURKIYE_ID}

with open(TRIPLET_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        s, r, o = parts
        rname = relations.get(r, r).strip().lower()

        if rname in BLACKLIST_RELATIONS:
            continue

        if s == TURKIYE_ID or o == TURKIYE_ID:
            direct_rows.append((s, r, o))
            direct_entities.add(s)
            direct_entities.add(o)

print("Direct triples:", len(direct_rows))
print("Direct entities:", len(direct_entities))

# 2) 1-hop genişleme
print("Collecting 1-hop expansion...")
expanded_rows = list(direct_rows)
expanded_entities = set(direct_entities)

with open(TRIPLET_FILE, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) != 3:
            continue
        s, r, o = parts
        rname = relations.get(r, r).strip().lower()

        if rname in BLACKLIST_RELATIONS:
            continue

        if s in direct_entities:
            expanded_rows.append((s, r, o))
            expanded_entities.add(s)
            expanded_entities.add(o)

expanded_rows = list(dict.fromkeys(expanded_rows))

print("Expanded triples:", len(expanded_rows))
print("Expanded entities:", len(expanded_entities))

# 3) relation frequency
counter = Counter()
for s, r, o in expanded_rows:
    counter[relations.get(r, r)] += 1

freq_out = OUT / "turkiye_relation_frequency.csv"
with open(freq_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["relation_name", "count"])
    for rel_name, cnt in counter.most_common():
        writer.writerow([rel_name, cnt])

# 4) entity csv
entity_out = SUBSET / "turkiye_general_entities.csv"
with open(entity_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["entity_id", "name", "description"])
    for eid in sorted(expanded_entities):
        writer.writerow([
            eid,
            entities.get(eid, eid),
            descriptions.get(eid, "")
        ])

# 5) triple csv
triple_out = SUBSET / "turkiye_general_triples.csv"
with open(triple_out, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "subject_id", "subject_name",
        "relation_id", "relation_name",
        "object_id", "object_name"
    ])
    for s, r, o in expanded_rows:
        writer.writerow([
            s, entities.get(s, s),
            r, relations.get(r, r),
            o, entities.get(o, o)
        ])

print("Saved entity file:", entity_out)
print("Saved triple file:", triple_out)
print("Saved relation frequency:", freq_out)

print("\nTop 30 relations:")
for rel_name, cnt in counter.most_common(30):
    print(rel_name, ":", cnt)