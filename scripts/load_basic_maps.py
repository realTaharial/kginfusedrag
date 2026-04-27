from pathlib import Path

RAW = Path("data/raw")

entity_file = RAW / "wikidata5m_entity.txt"
relation_file = RAW / "wikidata5m_relation.txt"
text_file = RAW / "wikidata5m_text.txt"

entities = {}
relations = {}
texts = {}

print("Loading entities...")
with open(entity_file, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            entity_id = parts[0]
            name = parts[1]
            entities[entity_id] = name
        if i >= 50000:
            break

print("Loading relations...")
with open(relation_file, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            rel_id = parts[0]
            rel_name = parts[1]
            relations[rel_id] = rel_name

print("Loading texts...")
with open(text_file, "r", encoding="utf-8") as f:
    for i, line in enumerate(f):
        parts = line.rstrip("\n").split("\t")
        if len(parts) >= 2:
            entity_id = parts[0]
            description = parts[1]
            texts[entity_id] = description
        if i >= 50000:
            break

print(f"Loaded sample entities: {len(entities)}")
print(f"Loaded relations: {len(relations)}")
print(f"Loaded sample texts: {len(texts)}")

print("\nSample relations:")
for k in list(relations.keys())[:10]:
    print(k, "->", relations[k])