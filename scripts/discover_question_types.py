from pathlib import Path
import csv
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"   # kendi şifren
DATABASE = "neo4j"

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


def get_2hop_patterns():
    cypher = """
    MATCH (a:Entity)-[r1:RELATION]->(b:Entity)-[r2:RELATION]->(c:Entity)
    RETURN r1.relation_name AS rel1,
           r2.relation_name AS rel2,
           count(*) AS freq
    ORDER BY freq DESC
    LIMIT 300
    """
    with driver.session(database=DATABASE) as session:
        rows = [r.data() for r in session.run(cypher)]
    return rows


def get_3hop_patterns():
    cypher = """
    MATCH (a:Entity)-[r1:RELATION]->(b:Entity)-[r2:RELATION]->(c:Entity)-[r3:RELATION]->(d:Entity)
    RETURN r1.relation_name AS rel1,
           r2.relation_name AS rel2,
           r3.relation_name AS rel3,
           count(*) AS freq
    ORDER BY freq DESC
    LIMIT 300
    """
    with driver.session(database=DATABASE) as session:
        rows = [r.data() for r in session.run(cypher)]
    return rows


def is_reasonable_pattern_2hop(rel1, rel2):
    bad = {
        "instance of", "different from", "has list", "is a list of", "part of"
    }
    if rel1 in bad or rel2 in bad:
        return False
    return True


def is_reasonable_pattern_3hop(rel1, rel2, rel3):
    bad = {
        "instance of", "different from", "has list", "is a list of", "part of"
    }
    if rel1 in bad or rel2 in bad or rel3 in bad:
        return False
    return True


def main():
    patterns_2 = get_2hop_patterns()
    patterns_3 = get_3hop_patterns()

    out2 = OUT / "question_type_candidates_2hop.csv"
    out3 = OUT / "question_type_candidates_3hop.csv"

    with open(out2, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rel1", "rel2", "freq", "usable"])
        for row in patterns_2:
            usable = is_reasonable_pattern_2hop(row["rel1"], row["rel2"])
            writer.writerow([row["rel1"], row["rel2"], row["freq"], usable])

    with open(out3, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rel1", "rel2", "rel3", "freq", "usable"])
        for row in patterns_3:
            usable = is_reasonable_pattern_3hop(row["rel1"], row["rel2"], row["rel3"])
            writer.writerow([row["rel1"], row["rel2"], row["rel3"], row["freq"], usable])

    print("Top usable 2-hop patterns:")
    count = 0
    for row in patterns_2:
        if is_reasonable_pattern_2hop(row["rel1"], row["rel2"]):
            print(f"{row['rel1']} -> {row['rel2']} : {row['freq']}")
            count += 1
            if count >= 20:
                break

    print("\nTop usable 3-hop patterns:")
    count = 0
    for row in patterns_3:
        if is_reasonable_pattern_3hop(row["rel1"], row["rel2"], row["rel3"]):
            print(f"{row['rel1']} -> {row['rel2']} -> {row['rel3']} : {row['freq']}")
            count += 1
            if count >= 20:
                break

    print("\nSaved:")
    print(out2)
    print(out3)


if __name__ == "__main__":
    main()