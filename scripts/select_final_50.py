from pathlib import Path
import json
from collections import defaultdict

IN_FILE = Path("data/processed/verified_question_bank.json")
OUT_FILE = Path("data/processed/final_50_questions.json")

TARGET_COUNTS = {
    "2-hop": 30,
    "3-hop": 15,
    "comparison": 5,
}

# Aynı question_type'tan çok soru yığılmasın diye üst sınır
MAX_PER_QUESTION_TYPE = {
    "2-hop": 4,
    "3-hop": 4,
    "comparison": 2,
}

# domain dengesi için yumuşak üst sınır
MAX_PER_DOMAIN = {
    "sports": 15,
    "cinema": 12,
    "academia": 12,
    "company": 12,
    "music": 10,
    "business": 10,
}


def load_questions():
    with open(IN_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def dedup_questions(questions):
    seen = set()
    clean = []

    for q in questions:
        key = (
            q.get("question_text", "").strip().lower(),
            tuple(q.get("reasoning_path", [])),
            q.get("gold_answer", "").strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            clean.append(q)

    return clean


def bucket_by_difficulty(questions):
    buckets = defaultdict(list)
    for q in questions:
        buckets[q["difficulty"]].append(q)
    return buckets


def score_question(q, difficulty, domain_counter, type_counter):
    domain = q.get("domain", "unknown")
    qtype = q.get("question_type", "unknown")

    # az kullanılan domain ve type daha yüksek puan alsın
    score = 0
    score += max(0, 10 - domain_counter[domain])
    score += max(0, 10 - type_counter[qtype])

    # reasoning path uzunluğu çeşitlilik için küçük bonus
    score += len(q.get("reasoning_path", [])) * 0.1

    return score


def select_diverse_subset(questions, difficulty, target_count):
    selected = []
    domain_counter = defaultdict(int)
    type_counter = defaultdict(int)

    # önce sort et: az kullanılan type/domain öne çıksın diye greedy tekrar hesaplayacağız
    pool = questions[:]

    while pool and len(selected) < target_count:
        # her turda yeniden skorla
        pool.sort(
            key=lambda q: score_question(q, difficulty, domain_counter, type_counter),
            reverse=True
        )

        picked = None
        for q in pool:
            domain = q.get("domain", "unknown")
            qtype = q.get("question_type", "unknown")

            if type_counter[qtype] >= MAX_PER_QUESTION_TYPE.get(difficulty, 4):
                continue

            if domain_counter[domain] >= MAX_PER_DOMAIN.get(domain, 10):
                continue

            picked = q
            break

        if picked is None:
            break

        selected.append(picked)
        pool.remove(picked)

        domain_counter[picked.get("domain", "unknown")] += 1
        type_counter[picked.get("question_type", "unknown")] += 1

    return selected


def main():
    questions = load_questions()
    questions = dedup_questions(questions)

    buckets = bucket_by_difficulty(questions)

    final_questions = []

    for difficulty, target in TARGET_COUNTS.items():
        subset = buckets.get(difficulty, [])
        chosen = select_diverse_subset(subset, difficulty, target)
        final_questions.extend(chosen)
        print(f"{difficulty}: selected {len(chosen)} / target {target}")

    # final sort
    final_questions.sort(key=lambda q: (q["difficulty"], q.get("domain", ""), q.get("question_type", "")))

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(final_questions, f, ensure_ascii=False, indent=2)

    print(f"\nSaved final set to: {OUT_FILE}")
    print(f"Total selected: {len(final_questions)}")

    # kısa özet
    diff_summary = defaultdict(int)
    domain_summary = defaultdict(int)
    type_summary = defaultdict(int)

    for q in final_questions:
        diff_summary[q["difficulty"]] += 1
        domain_summary[q.get("domain", "unknown")] += 1
        type_summary[q.get("question_type", "unknown")] += 1

    print("\nDifficulty summary:")
    for k, v in diff_summary.items():
        print(f"{k}: {v}")

    print("\nDomain summary:")
    for k, v in sorted(domain_summary.items()):
        print(f"{k}: {v}")

    print("\nQuestion type summary:")
    for k, v in sorted(type_summary.items()):
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()