from pathlib import Path
import csv
from neo4j import GraphDatabase

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "12345678"
DATABASE = "neo4j"

SUBSET = Path("data/subset")
ENTITY_FILE = SUBSET / "turkiye_general_entities.csv"
TRIPLE_FILE = SUBSET / "turkiye_general_triples.csv"

BATCH_SIZE = 1000

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def clear_graph(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def create_indexes(tx):
    tx.run("CREATE INDEX entity_id_index IF NOT EXISTS FOR (e:Entity) ON (e.entityId)")
    tx.run("CREATE INDEX entity_name_index IF NOT EXISTS FOR (e:Entity) ON (e.name)")

def insert_entities(tx, rows):
    tx.run("""
    UNWIND $rows AS row
    MERGE (e:Entity {entityId: row.entity_id})
    SET e.name = row.name,
        e.description = row.description
    """, rows=rows)

def insert_relations(tx, rows):
    tx.run("""
    UNWIND $rows AS row
    MATCH (s:Entity {entityId: row.subject_id})
    MATCH (o:Entity {entityId: row.object_id})
    MERGE (s)-[r:RELATION {
        relation_id: row.relation_id,
        relation_name: row.relation_name,
        subject_id: row.subject_id,
        object_id: row.object_id
    }]->(o)
    """, rows=rows)

def load_entities():
    rows = []
    total = 0
    with driver.session(database=DATABASE) as session:
        with open(ENTITY_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "entity_id": row["entity_id"],
                    "name": row["name"],
                    "description": row["description"],
                })
                if len(rows) >= BATCH_SIZE:
                    session.execute_write(insert_entities, rows)
                    total += len(rows)
                    print(f"Inserted entities: {total}")
                    rows = []
            if rows:
                session.execute_write(insert_entities, rows)
                total += len(rows)
                print(f"Inserted entities: {total}")

def load_relations():
    rows = []
    total = 0
    with driver.session(database=DATABASE) as session:
        with open(TRIPLE_FILE, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "subject_id": row["subject_id"],
                    "relation_id": row["relation_id"],
                    "relation_name": row["relation_name"],
                    "object_id": row["object_id"]
                })
                if len(rows) >= BATCH_SIZE:
                    session.execute_write(insert_relations, rows)
                    total += len(rows)
                    print(f"Inserted relations: {total}")
                    rows = []
            if rows:
                session.execute_write(insert_relations, rows)
                total += len(rows)
                print(f"Inserted relations: {total}")

def main():
    with driver.session(database=DATABASE) as session:
        print("Clearing graph...")
        session.execute_write(clear_graph)

        print("Creating indexes...")
        session.execute_write(create_indexes)

    print("Loading entities...")
    load_entities()

    print("Loading relations...")
    load_relations()

    print("Done.")

if __name__ == "__main__":
    main()
    driver.close()