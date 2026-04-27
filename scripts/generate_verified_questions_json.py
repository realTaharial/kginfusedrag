from neo4j import GraphDatabase
from pathlib import Path
import json

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "12345678"
DATABASE = "neo4j"

OUT_FILE = Path("data/processed/turkiye_verified_questions.json")
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

# Türkiye-related başlangıç mantığı:
# kişi/kurum/film/oyuncu Türkiye ile bağlantılı olacak,
# ama answer zorla Türkiye olmayacak.

PATTERNS = [
    # 2-hop SPORTS: Turkish-related player -> team -> country
    {
        "domain": "sports",
        "difficulty": "2-hop",
        "query": """
        MATCH (player:Entity)-[rt:RELATION]->(turkiye:Entity),
              (player)-[r1:RELATION]->(club:Entity)-[r2:RELATION]->(country:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'country for sport']
          AND r1.relation_name = 'member of sports team'
          AND r2.relation_name = 'country'
        RETURN DISTINCT player.name AS a, club.name AS b, country.name AS c
        LIMIT 20
        """,
        "qfn": lambda a, b, c: f"{a}'ın oynadığı takımın ülkesi neresidir?",
        "pathfn": lambda a, b, c: [a, "member of sports team", b, "country", c],
    },

    # 2-hop SPORTS: Turkish-related player -> team -> home venue
    {
        "domain": "sports",
        "difficulty": "2-hop",
        "query": """
        MATCH (player:Entity)-[rt:RELATION]->(turkiye:Entity),
              (player)-[r1:RELATION]->(club:Entity)-[r2:RELATION]->(venue:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'country for sport']
          AND r1.relation_name = 'member of sports team'
          AND r2.relation_name = 'home venue'
        RETURN DISTINCT player.name AS a, club.name AS b, venue.name AS c
        LIMIT 20
        """,
        "qfn": lambda a, b, c: f"{a}'ın oynadığı takımın stadyumu nedir?",
        "pathfn": lambda a, b, c: [a, "member of sports team", b, "home venue", c],
    },

    # 2-hop SPORTS: Turkish-related player -> place of birth -> city
    {
        "domain": "sports",
        "difficulty": "2-hop",
        "query": """
        MATCH (player:Entity)-[rt:RELATION]->(turkiye:Entity),
              (player)-[r1:RELATION]->(birth:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'country for sport']
          AND r1.relation_name = 'place of birth'
        RETURN DISTINCT player.name AS a, birth.name AS b
        LIMIT 20
        """,
        "qfn": lambda a, b: f"{a} nerede doğmuştur?",
        "pathfn": lambda a, b: [a, "place of birth", b],
    },

    # 2-hop SPORTS: Turkish-related player -> citizenship -> country
    {
        "domain": "sports",
        "difficulty": "2-hop",
        "query": """
        MATCH (player:Entity)-[r1:RELATION]->(country:Entity)
        WHERE r1.relation_name = 'country of citizenship'
          AND EXISTS {
              MATCH (player)-[:RELATION {relation_name:'sport'}]->(sport:Entity)
              WHERE toLower(sport.name) CONTAINS 'fut'
          }
        RETURN DISTINCT player.name AS a, country.name AS b
        LIMIT 20
        """,
        "qfn": lambda a, b: f"{a}'ın vatandaşlığı nedir?",
        "pathfn": lambda a, b: [a, "country of citizenship", b],
    },

    # 2-hop BUSINESS: Turkish-related company -> HQ city -> country
    {
        "domain": "business",
        "difficulty": "2-hop",
        "query": """
        MATCH (company:Entity)-[r1:RELATION]->(city:Entity)-[r2:RELATION]->(country:Entity)
        WHERE r1.relation_name = 'headquarters location'
          AND r2.relation_name = 'country'
          AND EXISTS {
              MATCH (company)-[:RELATION {relation_name:'headquarters location'}]->(:Entity)-[:RELATION {relation_name:'country'}]->(t:Entity {entityId:'Q43'})
          }
        RETURN DISTINCT company.name AS a, city.name AS b, country.name AS c
        LIMIT 20
        """,
        "qfn": lambda a, b, c: f"{a} şirketinin merkezinin bulunduğu ülke neresidir?",
        "pathfn": lambda a, b, c: [a, "headquarters location", b, "country", c],
    },

    # 2-hop ACADEMIA: Turkish-related person -> educated at -> university
    {
        "domain": "academia",
        "difficulty": "2-hop",
        "query": """
        MATCH (person:Entity)-[rt:RELATION]->(turkiye:Entity),
              (person)-[r1:RELATION]->(uni:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'place of birth']
          AND r1.relation_name = 'educated at'
        RETURN DISTINCT person.name AS a, uni.name AS b
        LIMIT 20
        """,
        "qfn": lambda a, b: f"{a} hangi üniversitede eğitim almıştır?",
        "pathfn": lambda a, b: [a, "educated at", b],
    },

    # 2-hop CINEMA: Turkish-related film -> director -> birth place
    {
        "domain": "cinema",
        "difficulty": "2-hop",
        "query": """
        MATCH (film:Entity)-[r1:RELATION]->(director:Entity)-[r2:RELATION]->(birth:Entity)
        WHERE r1.relation_name = 'director'
          AND r2.relation_name = 'place of birth'
          AND EXISTS {
              MATCH (director)-[:RELATION {relation_name:'country of citizenship'}]->(t:Entity {entityId:'Q43'})
          }
        RETURN DISTINCT film.name AS a, director.name AS b, birth.name AS c
        LIMIT 20
        """,
        "qfn": lambda a, b, c: f"{a} filminin yönetmeninin doğum yeri neresidir?",
        "pathfn": lambda a, b, c: [a, "director", b, "place of birth", c],
    },

    # 3-hop SPORTS: Turkish-related player -> team -> stadium -> city
    {
        "domain": "sports",
        "difficulty": "3-hop",
        "query": """
        MATCH (player:Entity)-[rt:RELATION]->(turkiye:Entity),
              (player)-[r1:RELATION]->(club:Entity)-[r2:RELATION]->(stadium:Entity)-[r3:RELATION]->(city:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'country for sport']
          AND r1.relation_name = 'member of sports team'
          AND r2.relation_name = 'home venue'
          AND r3.relation_name IN ['location', 'located in the administrative territorial entity']
        RETURN DISTINCT player.name AS a, club.name AS b, stadium.name AS c, city.name AS d
        LIMIT 15
        """,
        "qfn": lambda a, b, c, d: f"{a}'ın oynadığı takımın stadyumunun bulunduğu şehir neresidir?",
        "pathfn": lambda a, b, c, d: [a, "member of sports team", b, "home venue", c, "location", d],
    },

    # 3-hop SPORTS: Turkish-related player -> team -> country -> ? (same path but 3-hop style narrative)
    {
        "domain": "sports",
        "difficulty": "3-hop",
        "query": """
        MATCH (player:Entity)-[rt:RELATION]->(turkiye:Entity),
              (player)-[r1:RELATION]->(club:Entity)-[r2:RELATION]->(country:Entity)
        WHERE turkiye.entityId = 'Q43'
          AND rt.relation_name IN ['country of citizenship', 'country for sport']
          AND r1.relation_name = 'member of sports team'
          AND r2.relation_name = 'country'
        RETURN DISTINCT player.name AS a, club.name AS b, country.name AS c
        LIMIT 15
        """,
        "qfn": lambda a, b, c: f"{a}'ın oynadığı kulübün bulunduğu ülke neresidir?",
        "pathfn": lambda a, b, c: [a, "member of sports team", b, "country", c],
    },

    # comparison SPORTS
    {
        "domain": "sports",
        "difficulty": "comparison",
        "query": """
        MATCH (p1:Entity)-[r1:RELATION]->(b1:Entity),
              (p2:Entity)-[r2:RELATION]->(b2:Entity)
        WHERE r1.relation_name = 'place of birth'
          AND r2.relation_name = 'place of birth'
          AND EXISTS {
              MATCH (p1)-[:RELATION {relation_name:'country of citizenship'}]->(t:Entity {entityId:'Q43'})
          }
          AND EXISTS {
              MATCH (p2)-[:RELATION {relation_name:'country of citizenship'}]->(t:Entity {entityId:'Q43'})
          }
          AND p1.name <> p2.name
        RETURN DISTINCT p1.name AS a, b1.name AS b, p2.name AS c, b2.name AS d
        LIMIT 5
        """,
        "qfn": lambda a, b, c, d: f"{a} ile {c} aynı yerde mi doğmuştur?",
        "pathfn": lambda a, b, c, d: [a, "place of birth", b, c, "place of birth", d],
    },
]

questions = []
qid = 1

with driver.session(database=DATABASE) as session:
    for pattern in PATTERNS:
        results = session.run(pattern["query"])
        for row in results:
            values = list(row.values())
            questions.append({
                "question_id": f"TR_{qid:03d}",
                "question_text": pattern["qfn"](*values),
                "reasoning_path": pattern["pathfn"](*values),
                "gold_answer": values[-1],
                "difficulty": pattern["difficulty"],
                "domain": pattern["domain"]
            })
            qid += 1

with open(OUT_FILE, "w", encoding="utf-8") as f:
    json.dump(questions, f, ensure_ascii=False, indent=2)

print("Saved verified questions to:", OUT_FILE)
print("Total questions:", len(questions))

difficulty_counts = {}
domain_counts = {}

for q in questions:
    difficulty_counts[q["difficulty"]] = difficulty_counts.get(q["difficulty"], 0) + 1
    domain_counts[q["domain"]] = domain_counts.get(q["domain"], 0) + 1

print("\nDifficulty distribution:")
for k, v in difficulty_counts.items():
    print(k, ":", v)

print("\nDomain distribution:")
for k, v in domain_counts.items():
    print(k, ":", v)

print("\nFirst 10 questions:")
for q in questions[:10]:
    print("-" * 80)
    print(q["question_id"])
    print(q["question_text"])
    print(q["reasoning_path"])
    print("Answer:", q["gold_answer"])

driver.close()