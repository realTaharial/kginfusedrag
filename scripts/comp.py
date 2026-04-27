import json
import random
import re
from pathlib import Path
from datetime import datetime
from itertools import combinations

INPUT_PATH = "verified_triples.jsonl"
OUTPUT_PATH = "comparison_questions.jsonl"
MAX_PER_RELATION = 200
SEED = 42

random.seed(SEED)


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def normalize_text(x: str) -> str:
    return re.sub(r"\s+", " ", str(x).strip())


def parse_date_safe(date_str: str):
    """
    Tries multiple date formats.
    Returns datetime or None.
    """
    if not date_str:
        return None

    date_str = normalize_text(date_str)

    formats = [
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%Y/%m/%d",
        "%d/%m/%Y",
        "%Y-%m",
        "%Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            pass

    return None


def load_jsonl(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def write_jsonl(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def pick_template(templates):
    return random.choice(templates)


# --------------------------------------------------
# Relation type detection
# --------------------------------------------------

DATE_RELATIONS = {
    "coach_birth",
    "director_birth",
    "person_birth",
    "birth_date",
}

SAME_VALUE_RELATIONS = {
    "team_country",
    "company_hq_country",
    "educated_at_country",
    "record_label_country",
    "university_country",
    "team_league",
    "team_venue",
    "team_headquarters",
}

# İstersen sonra buraya numeric relation da ekleyebilirsin
NUMERIC_RELATIONS = {
    # örnek: "director_award_count"
}


# --------------------------------------------------
# Templates
# --------------------------------------------------

DATE_COMPARE_TEMPLATES = [
    "Who was born earlier, {a} or {b}?",
    "Which one is older, {a} or {b}?",
    "Between {a} and {b}, who was born first?",
]

DATE_COMPARE_LATER_TEMPLATES = [
    "Who was born later, {a} or {b}?",
    "Which one is younger, {a} or {b}?",
    "Between {a} and {b}, who was born more recently?",
]

SAME_VALUE_TEMPLATES = [
    "Are {a} and {b} from the same {field}?",
    "Do {a} and {b} belong to the same {field}?",
    "Do {a} and {b} share the same {field}?",
]

DIFF_VALUE_TEMPLATES = [
    "Are {a} and {b} from different {field}s?",
    "Do {a} and {b} belong to different {field}s?",
]

VALUE_WHICH_TEMPLATES = [
    "Which {field} do both {a} and {b} share?",
    "{a} and {b} belong to the same {field}. What is it?",
]


# --------------------------------------------------
# Pretty field names
# --------------------------------------------------

def relation_to_field_name(relation: str) -> str:
    mapping = {
        "team_country": "country",
        "company_hq_country": "country",
        "educated_at_country": "country",
        "record_label_country": "country",
        "university_country": "country",
        "team_league": "league",
        "team_venue": "venue",
        "team_headquarters": "headquarters",
    }
    return mapping.get(relation, "category")


# --------------------------------------------------
# Core generators
# --------------------------------------------------

def generate_date_comparisons(rows, relation, max_count=200):
    """
    Expects rows like:
    {
      "subject": "Person A",
      "relation": "director_birth",
      "object": "1978-04-10"
    }
    """
    valid = []
    for r in rows:
        dt = parse_date_safe(r["object"])
        if dt is not None:
            valid.append({
                "subject": normalize_text(r["subject"]),
                "relation": relation,
                "object": normalize_text(r["object"]),
                "parsed_date": dt,
            })

    questions = []
    seen_questions = set()

    pairs = list(combinations(valid, 2))
    random.shuffle(pairs)

    for x, y in pairs:
        if len(questions) >= max_count:
            break

        # aynı tarihse atla
        if x["parsed_date"] == y["parsed_date"]:
            continue

        # earlier question
        if random.random() < 0.5:
            q = pick_template(DATE_COMPARE_TEMPLATES).format(a=x["subject"], b=y["subject"])
            answer = x["subject"] if x["parsed_date"] < y["parsed_date"] else y["subject"]
            comparator = "earlier"
        else:
            q = pick_template(DATE_COMPARE_LATER_TEMPLATES).format(a=x["subject"], b=y["subject"])
            answer = x["subject"] if x["parsed_date"] > y["parsed_date"] else y["subject"]
            comparator = "later"

        key = (q.lower(), answer.lower())
        if key in seen_questions:
            continue
        seen_questions.add(key)

        questions.append({
            "type": "comparison",
            "relation": relation,
            "question": q,
            "answer": answer,
            "meta": {
                "entity_a": x["subject"],
                "entity_b": y["subject"],
                "value_a": x["object"],
                "value_b": y["object"],
                "comparison_type": comparator,
            }
        })

    return questions


def generate_same_value_comparisons(rows, relation, max_count=200):
    """
    Produces:
    - same/different yes-no questions
    - shared-value questions when values are equal
    """
    field = relation_to_field_name(relation)

    items = []
    for r in rows:
        items.append({
            "subject": normalize_text(r["subject"]),
            "relation": relation,
            "object": normalize_text(r["object"]),
        })

    questions = []
    seen_questions = set()

    pairs = list(combinations(items, 2))
    random.shuffle(pairs)

    for x, y in pairs:
        if len(questions) >= max_count:
            break

        same = (x["object"].lower() == y["object"].lower())

        mode = random.choice(["same_diff_yesno", "shared_value"])

        if mode == "same_diff_yesno":
            # bazen same, bazen different sor
            ask_same = random.random() < 0.5

            if ask_same:
                q = pick_template(SAME_VALUE_TEMPLATES).format(
                    a=x["subject"], b=y["subject"], field=field
                )
                answer = "Yes" if same else "No"
                comp_type = "same_yesno"
            else:
                q = pick_template(DIFF_VALUE_TEMPLATES).format(
                    a=x["subject"], b=y["subject"], field=field
                )
                answer = "No" if same else "Yes"
                comp_type = "different_yesno"

        else:
            # shared value sorusu sadece gerçekten aynıysa anlamlı
            if not same:
                continue
            q = pick_template(VALUE_WHICH_TEMPLATES).format(
                a=x["subject"], b=y["subject"], field=field
            )
            answer = x["object"]
            comp_type = "shared_value"

        key = (q.lower(), answer.lower())
        if key in seen_questions:
            continue
        seen_questions.add(key)

        questions.append({
            "type": "comparison",
            "relation": relation,
            "question": q,
            "answer": answer,
            "meta": {
                "entity_a": x["subject"],
                "entity_b": y["subject"],
                "value_a": x["object"],
                "value_b": y["object"],
                "same_value": same,
                "comparison_type": comp_type,
            }
        })

    return questions


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    rows = load_jsonl(INPUT_PATH)

    # normalize expected keys
    cleaned = []
    for r in rows:
        # farklı key isimleri varsa burada uyarlayabilirsin
        subject = r.get("subject") or r.get("entity") or r.get("head")
        relation = r.get("relation") or r.get("predicate") or r.get("rel")
        obj = r.get("object") or r.get("tail") or r.get("answer")

        if not subject or not relation or obj is None:
            continue

        cleaned.append({
            "subject": normalize_text(subject),
            "relation": normalize_text(relation),
            "object": normalize_text(obj),
        })

    by_relation = {}
    for r in cleaned:
        by_relation.setdefault(r["relation"], []).append(r)

    all_questions = []

    for relation, rel_rows in by_relation.items():
        if relation in DATE_RELATIONS:
            qs = generate_date_comparisons(
                rel_rows,
                relation=relation,
                max_count=MAX_PER_RELATION
            )
            print(f"{relation} -> {len(qs)} comparison questions")
            all_questions.extend(qs)

        elif relation in SAME_VALUE_RELATIONS:
            qs = generate_same_value_comparisons(
                rel_rows,
                relation=relation,
                max_count=MAX_PER_RELATION
            )
            print(f"{relation} -> {len(qs)} comparison questions")
            all_questions.extend(qs)

        else:
            print(f"{relation} -> skipped (no comparison template defined)")

    write_jsonl(OUTPUT_PATH, all_questions)
    print(f"\nSaved to: {OUTPUT_PATH}")
    print(f"Total comparison questions: {len(all_questions)}")


if __name__ == "__main__":
    main()