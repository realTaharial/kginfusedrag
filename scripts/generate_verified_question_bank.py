from pathlib import Path
import csv
import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "12345678"   # kendi şifreni yaz
DATABASE = "neo4j"

OUT = Path("data/processed")
OUT.mkdir(parents=True, exist_ok=True)

driver = GraphDatabase.driver(URI, auth=(USER, PASSWORD))


QUESTION_TEMPLATES = [
    {
        "question_type": "team_country",
        "difficulty": "2-hop",
        "domain": "sports",
        "cypher": """
        MATCH (a:Entity)-[r1:RELATION {relation_name:'member of sports team'}]->(b:Entity)
              -[r2:RELATION {relation_name:'country'}]->(c:Entity)
        RETURN a.entityId AS a_id, a.name AS a_name,
               b.entityId AS b_id, b.name AS b_name,
               c.entityId AS c_id, c.name AS c_name
        LIMIT 200
        """,
        "question_fn": lambda a, b, c: f"{a}'ın oynadığı takımın ülkesi neresidir?",
        "path_fn": lambda a, b, c: [a, "member of sports team", b, "country", c],
        "answer_fn": lambda a, b, c: c,
    },
    {
    "question_type": "team_league",
    "difficulty": "2-hop",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'member of sports team'}]->(b:Entity)
          -[:RELATION {relation_name:'league'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a}'ın oynadığı takım hangi ligdedir?",
    "path_fn": lambda a, b, c: [a, "member of sports team", b, "league", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "team_venue",
    "difficulty": "2-hop",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'member of sports team'}]->(b:Entity)
          -[:RELATION {relation_name:'home venue'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a}'ın oynadığı takımın stadyumu nedir?",
    "path_fn": lambda a, b, c: [a, "member of sports team", b, "home venue", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "team_headquarters",
    "difficulty": "2-hop",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'member of sports team'}]->(b:Entity)
          -[:RELATION {relation_name:'headquarters location'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a}'ın oynadığı takımın merkezi nerededir?",
    "path_fn": lambda a, b, c: [a, "member of sports team", b, "headquarters location", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "director_award",
    "difficulty": "2-hop",
    "domain": "cinema",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'director'}]->(b:Entity)
          -[:RELATION {relation_name:'award received'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a} filminin yönetmeninin kazandığı ödül nedir?",
    "path_fn": lambda a, b, c: [a, "director", b, "award received", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "company_hq_country",
    "difficulty": "2-hop",
    "domain": "company",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'headquarters location'}]->(b:Entity)
          -[:RELATION {relation_name:'country'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a} şirketinin merkezinin bulunduğu ülke neresidir?",
    "path_fn": lambda a, b, c: [a, "headquarters location", b, "country", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "educated_at_country",
    "difficulty": "2-hop",
    "domain": "academia",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'educated at'}]->(b:Entity)
          -[:RELATION {relation_name:'country'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a}'ın mezun olduğu üniversitenin ülkesi neresidir?",
    "path_fn": lambda a, b, c: [a, "educated at", b, "country", c],
    "answer_fn": lambda a, b, c: c,
},{
    "question_type": "record_label_country",
    "difficulty": "2-hop",
    "domain": "music",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'record label'}]->(b:Entity)
          -[:RELATION {relation_name:'country'}]->(c:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c: f"{a}'ın bağlı olduğu plak şirketinin ülkesi neresidir?",
    "path_fn": lambda a, b, c: [a, "record label", b, "country", c],
    "answer_fn": lambda a, b, c: c,
},
    {
        "question_type": "coach_birth",
        "difficulty": "2-hop",
        "domain": "sports",
        "cypher": """
        MATCH (a:Entity)-[r1:RELATION {relation_name:'head coach'}]->(b:Entity)
              -[r2:RELATION {relation_name:'place of birth'}]->(c:Entity)
        RETURN a.entityId AS a_id, a.name AS a_name,
               b.entityId AS b_id, b.name AS b_name,
               c.entityId AS c_id, c.name AS c_name
        LIMIT 200
        """,
        "question_fn": lambda a, b, c: f"{a}'ın teknik direktörünün doğum yeri neresidir?",
        "path_fn": lambda a, b, c: [a, "head coach", b, "place of birth", c],
        "answer_fn": lambda a, b, c: c,
    },
    {
        "question_type": "director_birth",
        "difficulty": "2-hop",
        "domain": "cinema",
        "cypher": """
        MATCH (a:Entity)-[r1:RELATION {relation_name:'director'}]->(b:Entity)
              -[r2:RELATION {relation_name:'place of birth'}]->(c:Entity)
        RETURN a.entityId AS a_id, a.name AS a_name,
               b.entityId AS b_id, b.name AS b_name,
               c.entityId AS c_id, c.name AS c_name
        LIMIT 200
        """,
        "question_fn": lambda a, b, c: f"{a} filminin yönetmeninin doğum yeri neresidir?",
        "path_fn": lambda a, b, c: [a, "director", b, "place of birth", c],
        "answer_fn": lambda a, b, c: c,
    },
    {
        "question_type": "university_country",
        "difficulty": "2-hop",
        "domain": "academia",
        "cypher": """
        MATCH (a:Entity)-[r1:RELATION {relation_name:'educated at'}]->(b:Entity)
              -[r2:RELATION {relation_name:'country'}]->(c:Entity)
        RETURN a.entityId AS a_id, a.name AS a_name,
               b.entityId AS b_id, b.name AS b_name,
               c.entityId AS c_id, c.name AS c_name
        LIMIT 200
        """,
        "question_fn": lambda a, b, c: f"{a}'ın okuduğu üniversitenin ülkesi neresidir?",
        "path_fn": lambda a, b, c: [a, "educated at", b, "country", c],
        "answer_fn": lambda a, b, c: c,
    },
{
    "question_type": "director_birth_region",
    "difficulty": "3-hop",
    "domain": "cinema",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'director'}]->(b:Entity)
          -[:RELATION {relation_name:'place of birth'}]->(c:Entity)
          -[:RELATION {relation_name:'located in the administrative territorial entity'}]->(d:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name,
           d.entityId AS d_id, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a} filminin yönetmeninin doğduğu yerin bağlı olduğu bölge neresidir?",
    "path_fn": lambda a, b, c, d: [a, "director", b, "place of birth", c, "located in the administrative territorial entity", d],
    "answer_fn": lambda a, b, c, d: d,
},{
    "question_type": "company_hq_city_country",
    "difficulty": "3-hop",
    "domain": "company",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'headquarters location'}]->(b:Entity)
          -[:RELATION {relation_name:'location'}]->(c:Entity)
          -[:RELATION {relation_name:'country'}]->(d:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name,
           d.entityId AS d_id, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a} şirketinin merkezinin bulunduğu şehrin ülkesi neresidir?",
    "path_fn": lambda a, b, c, d: [a, "headquarters location", b, "location", c, "country", d],
    "answer_fn": lambda a, b, c, d: d,
},
{
    "question_type": "educated_at_city_country",
    "difficulty": "3-hop",
    "domain": "academia",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'educated at'}]->(b:Entity)
          -[:RELATION {relation_name:'location'}]->(c:Entity)
          -[:RELATION {relation_name:'country'}]->(d:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name,
           d.entityId AS d_id, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a}'ın mezun olduğu üniversitenin bulunduğu şehrin ülkesi neresidir?",
    "path_fn": lambda a, b, c, d: [a, "educated at", b, "location", c, "country", d],
    "answer_fn": lambda a, b, c, d: d,
},
{
    "question_type": "compare_birthday",
    "difficulty": "comparison",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'birthday'}]->(b:Entity),
          (c:Entity)-[:RELATION {relation_name:'birthday'}]->(d:Entity)
    WHERE a.entityId <> c.entityId
    RETURN a.entityId AS a_id, a.name AS a_name, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a} mi yoksa {c} mi daha önce doğmuştur?",
    "path_fn": lambda a, b, c, d: [a, "birthday", b, c, "birthday", d],
    "answer_fn": lambda a, b, c, d: "compare_dates",
},
{
    "question_type": "compare_team_country_same",
    "difficulty": "comparison",
    "domain": "sports",
    "cypher": """
    MATCH (p1:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t1:Entity)
          -[:RELATION {relation_name:'country'}]->(c1:Entity),
          (p2:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t2:Entity)
          -[:RELATION {relation_name:'country'}]->(c2:Entity)
    WHERE p1.entityId < p2.entityId
    RETURN p1.entityId AS a_id, p1.name AS a_name, t1.name AS b_name, c1.name AS c_name,
           p2.entityId AS d_id, p2.name AS d_name, t2.name AS e_name, c2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} aynı ülkedeki takımlarda mı oynuyor?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "member of sports team", b, "country", c,
        d, "member of sports team", e, "country", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_team_league_same",
    "difficulty": "comparison",
    "domain": "sports",
    "cypher": """
    MATCH (p1:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t1:Entity)
          -[:RELATION {relation_name:'league'}]->(l1:Entity),
          (p2:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t2:Entity)
          -[:RELATION {relation_name:'league'}]->(l2:Entity)
    WHERE p1.entityId < p2.entityId
    RETURN p1.entityId AS a_id, p1.name AS a_name, t1.name AS b_name, l1.name AS c_name,
           p2.entityId AS d_id, p2.name AS d_name, t2.name AS e_name, l2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} aynı ligde oynayan takımlarda mı bulunuyor?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "member of sports team", b, "league", c,
        d, "member of sports team", e, "league", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_company_hq_country_same",
    "difficulty": "comparison",
    "domain": "company",
    "cypher": """
    MATCH (x:Entity)-[:RELATION {relation_name:'headquarters location'}]->(h1:Entity)
          -[:RELATION {relation_name:'country'}]->(c1:Entity),
          (y:Entity)-[:RELATION {relation_name:'headquarters location'}]->(h2:Entity)
          -[:RELATION {relation_name:'country'}]->(c2:Entity)
    WHERE x.entityId < y.entityId
    RETURN x.entityId AS a_id, x.name AS a_name, h1.name AS b_name, c1.name AS c_name,
           y.entityId AS d_id, y.name AS d_name, h2.name AS e_name, c2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} şirketlerinin merkezleri aynı ülkede mi?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "headquarters location", b, "country", c,
        d, "headquarters location", e, "country", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_educated_country_same",
    "difficulty": "comparison",
    "domain": "academia",
    "cypher": """
    MATCH (x:Entity)-[:RELATION {relation_name:'educated at'}]->(u1:Entity)
          -[:RELATION {relation_name:'country'}]->(c1:Entity),
          (y:Entity)-[:RELATION {relation_name:'educated at'}]->(u2:Entity)
          -[:RELATION {relation_name:'country'}]->(c2:Entity)
    WHERE x.entityId < y.entityId
    RETURN x.entityId AS a_id, x.name AS a_name, u1.name AS b_name, c1.name AS c_name,
           y.entityId AS d_id, y.name AS d_name, u2.name AS e_name, c2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} aynı ülkedeki üniversitelerde mi okudu?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "educated at", b, "country", c,
        d, "educated at", e, "country", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_record_label_country_same",
    "difficulty": "comparison",
    "domain": "music",
    "cypher": """
    MATCH (x:Entity)-[:RELATION {relation_name:'record label'}]->(r1:Entity)
          -[:RELATION {relation_name:'country'}]->(c1:Entity),
          (y:Entity)-[:RELATION {relation_name:'record label'}]->(r2:Entity)
          -[:RELATION {relation_name:'country'}]->(c2:Entity)
    WHERE x.entityId < y.entityId
    RETURN x.entityId AS a_id, x.name AS a_name, r1.name AS b_name, c1.name AS c_name,
           y.entityId AS d_id, y.name AS d_name, r2.name AS e_name, c2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} aynı ülkedeki plak şirketlerine mi bağlı?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "record label", b, "country", c,
        d, "record label", e, "country", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_director_birth_place_same",
    "difficulty": "comparison",
    "domain": "cinema",
    "cypher": """
    MATCH (m1:Entity)-[:RELATION {relation_name:'director'}]->(d1:Entity)
          -[:RELATION {relation_name:'place of birth'}]->(p1:Entity),
          (m2:Entity)-[:RELATION {relation_name:'director'}]->(d2:Entity)
          -[:RELATION {relation_name:'place of birth'}]->(p2:Entity)
    WHERE m1.entityId < m2.entityId
    RETURN m1.entityId AS a_id, m1.name AS a_name, d1.name AS b_name, p1.name AS c_name,
           m2.entityId AS d_id, m2.name AS d_name, d2.name AS e_name, p2.name AS f_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e, f: f"{a} ve {d} filmlerinin yönetmenleri aynı yerde mi doğmuştur?",
    "path_fn": lambda a, b, c, d, e, f: [
        a, "director", b, "place of birth", c,
        d, "director", e, "place of birth", f
    ],
    "answer_fn": lambda a, b, c, d, e, f: "Evet" if c == f else "Hayır",
},
{
    "question_type": "compare_team_country_which",
    "difficulty": "comparison",
    "domain": "sports",
    "cypher": """
    MATCH (p1:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t1:Entity)
          -[:RELATION {relation_name:'country'}]->(c:Entity),
          (p2:Entity)-[:RELATION {relation_name:'member of sports team'}]->(t2:Entity)
          -[:RELATION {relation_name:'country'}]->(c:Entity)
    WHERE p1.entityId < p2.entityId
    RETURN p1.entityId AS a_id, p1.name AS a_name, t1.name AS b_name, c.name AS c_name,
           p2.entityId AS d_id, p2.name AS d_name, t2.name AS e_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d, e: f"{a} ve {d} hangi ortak ülkeye ait takımlarda oynuyor?",
    "path_fn": lambda a, b, c, d, e: [
        a, "member of sports team", b, "country", c,
        d, "member of sports team", e, "country", c
    ],
    "answer_fn": lambda a, b, c, d, e: c,
},
    {
    "question_type": "team_venue_city",
    "difficulty": "3-hop",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'member of sports team'}]->(b:Entity)
          -[:RELATION {relation_name:'home venue'}]->(c:Entity)
          -[:RELATION {relation_name:'located in the administrative territorial entity'}]->(d:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name,
           d.entityId AS d_id, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a}'ın oynadığı takımın stadyumunun bulunduğu şehir neresidir?",
    "path_fn": lambda a, b, c, d: [
        a, "member of sports team", b,
        "home venue", c,
        "located in the administrative territorial entity", d
    ],
    "answer_fn": lambda a, b, c, d: d,
    },
    {
    "question_type": "team_venue_country",
    "difficulty": "3-hop",
    "domain": "sports",
    "cypher": """
    MATCH (a:Entity)-[:RELATION {relation_name:'member of sports team'}]->(b:Entity)
          -[:RELATION {relation_name:'home venue'}]->(c:Entity)
          -[:RELATION {relation_name:'country'}]->(d:Entity)
    RETURN a.entityId AS a_id, a.name AS a_name,
           b.entityId AS b_id, b.name AS b_name,
           c.entityId AS c_id, c.name AS c_name,
           d.entityId AS d_id, d.name AS d_name
    LIMIT 200
    """,
    "question_fn": lambda a, b, c, d: f"{a}'ın oynadığı takımın stadyumunun bulunduğu ülke neresidir?",
    "path_fn": lambda a, b, c, d: [
        a, "member of sports team", b,
        "home venue", c,
        "country", d
    ],
    "answer_fn": lambda a, b, c, d: d,
    },
    {
        "question_type": "director_birth_country",
        "difficulty": "3-hop",
        "domain": "cinema",
        "cypher": """
        MATCH (a:Entity)-[:RELATION {relation_name:'director'}]->(b:Entity)
              -[:RELATION {relation_name:'place of birth'}]->(c:Entity)
              -[:RELATION {relation_name:'country'}]->(d:Entity)
        RETURN a.entityId AS a_id, a.name AS a_name,
               b.entityId AS b_id, b.name AS b_name,
               c.entityId AS c_id, c.name AS c_name,
               d.entityId AS d_id, d.name AS d_name
        LIMIT 200
        """,
        "question_fn": lambda a, b, c, d: f"{a} filminin yönetmeninin doğduğu yerin ülkesi neresidir?",
        "path_fn": lambda a, b, c, d: [a, "director", b, "place of birth", c, "country", d],
        "answer_fn": lambda a, b, c, d: d,
    },
]
def normalize_date(text: str):
    if text is None:
        return None
    t = str(text).strip()
    digits = "".join(ch for ch in t if ch.isdigit() or ch == "-")
    return digits if digits else None


def compare_dates(v1: str, v2: str):
    d1 = normalize_date(v1)
    d2 = normalize_date(v2)

    if not d1 or not d2:
        return None

    if d1 < d2:
        return "first"
    elif d2 < d1:
        return "second"
    return "equal"
def infer_difficulty_from_path(reasoning_path, question_type):
    if question_type.startswith("compare_"):
        return "comparison"

    # path örn:
    # [entity, relation, entity, relation, entity]
    # relation sayısı = (len(path)-1)//2
    hops = (len(reasoning_path) - 1) // 2

    return f"{hops}-hop"

def run_template(template):
    with driver.session(database=DATABASE) as session:
        result = session.run(template["cypher"])
        rows = [r.data() for r in result]

    verified_questions = []

    for idx, row in enumerate(rows, start=1):
        values = [v for k, v in row.items() if k.endswith("_name")]

        question_text = template["question_fn"](*values)
        reasoning_path = template["path_fn"](*values)
        gold_answer = template["answer_fn"](*values)

        if template["question_type"] == "compare_birthday":
            cmp_result = compare_dates(row["b_name"], row["d_name"])
            if cmp_result is None or cmp_result == "equal":
                continue
            gold_answer = row["a_name"] if cmp_result == "first" else row["c_name"]
        else:
            gold_answer = template["answer_fn"](*values)

        actual_difficulty = infer_difficulty_from_path(reasoning_path, template["question_type"])

        verified_questions.append({
        "question_id": f"{actual_difficulty.upper()}_{template['question_type'].upper()}_{idx:03d}",
        "question_text": question_text,
        "reasoning_path": reasoning_path,
        "gold_answer": gold_answer,
        "difficulty": actual_difficulty,
        "domain": template["domain"],
        "question_type": template["question_type"],
    })

    return verified_questions


def main():
    all_questions = []
    
    for template in QUESTION_TEMPLATES:
        qs = run_template(template)
        all_questions.extend(qs)
        print(f"{template['question_type']} -> {len(qs)} verified questions")

    json_out = OUT / "verified_question_bank.json"
    csv_out = OUT / "verified_question_bank.csv"

    with open(json_out, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    with open(csv_out, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "question_id",
            "question_text",
            "reasoning_path",
            "gold_answer",
            "difficulty",
            "domain",
            "question_type",
        ])
        for q in all_questions:
            writer.writerow([
                q["question_id"],
                q["question_text"],
                " -> ".join(q["reasoning_path"]),
                q["gold_answer"],
                q["difficulty"],
                q["domain"],
                q["question_type"],
            ])

    print("\nSaved:")
    print(json_out)
    print(csv_out)


if __name__ == "__main__":
    main()