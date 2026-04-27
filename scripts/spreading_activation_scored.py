from neo4j import GraphDatabase
from collections import deque

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "12345678"
DATABASE = "neo4j"

MAX_ROUNDS = 2
MAX_NEIGHBORS_PER_NODE = 30

ALLOWED_RELATIONS = {
    "member of sports team",
    "country",
    "country of citizenship",
    "country of origin",
    "country for sport",
    "place of birth",
    "place of death",
    "headquarters location",
    "coach",
    "sport",
    "occupation",
    "league",
    "home venue",
    "instance of",
    "position played on team / speciality",
    "located in the administrative territorial entity",
    "location",
    "participant of"
}

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def find_seed_entity(tx, query_text):
    cypher = """
    MATCH (e:Entity)
    WHERE toLower(e.name) CONTAINS toLower($query_text)
    RETURN e.entityId AS entityId, e.name AS name
    LIMIT 10
    """
    return list(tx.run(cypher, query_text=query_text))

def get_neighbors(tx, entity_id):
    cypher = """
    MATCH (s:Entity {entityId:$entity_id})-[r:RELATION]->(o:Entity)
    RETURN s.entityId AS s_id, s.name AS s_name,
           r.relation_name AS relation,
           o.entityId AS o_id, o.name AS o_name
    LIMIT $limit
    """
    return list(tx.run(cypher, entity_id=entity_id, limit=MAX_NEIGHBORS_PER_NODE))

def question_relation_weights(question: str):
    q = question.lower()
    weights = {}

    def add(rel, val):
        weights[rel] = weights.get(rel, 0) + val

    if "team" in q or "club" in q or "oynadığı takım" in q:
        add("member of sports team", 5)

    if "country" in q or "ülke" in q:
        add("country", 5)
        add("country of citizenship", 3)
        add("country for sport", 3)

    if "birth" in q or "doğ" in q:
        add("place of birth", 5)

    if "coach" in q or "teknik direktör" in q:
        add("coach", 5)

    if "stadium" in q or "stadyum" in q or "venue" in q:
        add("home venue", 5)

    if "league" in q or "lig" in q:
        add("league", 4)

    if "where" in q or "nerede" in q or "location" in q:
        add("headquarters location", 3)
        add("location", 2)

    return weights

def score_path(path, relation_weights):
    score = 0
    for triple in path:
        rel = triple[2]
        score += relation_weights.get(rel, 1)
    score -= max(0, len(path) - 1) * 0.5
    return score

def spreading_activation_scored(seed_id, seed_name, question):
    visited_entities = set([seed_id])
    relation_weights = question_relation_weights(question)
    frontier = deque([(seed_id, seed_name, 0, [])])
    completed_paths = []

    while frontier:
        current_id, current_name, depth, path = frontier.popleft()

        if depth >= MAX_ROUNDS:
            if path:
                completed_paths.append(path)
            continue

        with driver.session(database=DATABASE) as session:
            neighbors = session.execute_read(get_neighbors, current_id)

        expanded = False

        for record in neighbors:
            relation = record["relation"]
            next_id = record["o_id"]
            next_name = record["o_name"]

            if relation not in ALLOWED_RELATIONS:
                continue

            triple = (
                record["s_id"],
                record["s_name"],
                relation,
                next_id,
                next_name
            )

            new_path = path + [triple]
            expanded = True

            if next_id not in visited_entities:
                visited_entities.add(next_id)
                frontier.append((next_id, next_name, depth + 1, new_path))
            else:
                completed_paths.append(new_path)

        if not expanded and path:
            completed_paths.append(path)

    scored = []
    for path in completed_paths:
        scored.append((score_path(path, relation_weights), path))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored

def print_best_paths(scored_paths, top_k=10):
    print(f"\nTop {top_k} reasoning paths:")
    for idx, (score, path) in enumerate(scored_paths[:top_k], start=1):
        print(f"\nPath {idx} | score={score:.2f}")
        for triple in path:
            print(f"{triple[1]} --[{triple[2]}]--> {triple[4]}")

def run_demo(question, entity_hint):
    with driver.session(database=DATABASE) as session:
        candidates = session.execute_read(find_seed_entity, entity_hint)

    if not candidates:
        print("No seed entity found.")
        return

    print("Seed candidates:")
    for c in candidates[:10]:
        print("-", c["entityId"], c["name"])

    seed = candidates[0]
    print("\nUsing seed:", seed["entityId"], seed["name"])
    print("Question:", question)

    scored_paths = spreading_activation_scored(seed["entityId"], seed["name"], question)
    print_best_paths(scored_paths, top_k=10)

if __name__ == "__main__":
    question = "Which country is the team of Ali Bilgin in?"
    entity_hint = "ali bilgin"

    run_demo(question, entity_hint)
    driver.close()