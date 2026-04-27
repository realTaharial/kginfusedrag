from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests

API_URL = "http://127.0.0.1:8000/ask"
QUESTION_BANK_PATH = Path("data/processed/verified_question_bank.json")
OUTPUT_PATH = Path("data/processed/evaluation_results_current_system.json")

# İstersen deneme için limit koy
MAX_QUESTIONS = None  # örn: 50
SLEEP_SECONDS = 0.05


def normalize_text(text: str) -> str:
    text = (text or "").strip().lower()
    text = text.replace("ı", "i").replace("İ", "i")
    text = text.replace("ç", "c").replace("ğ", "g").replace("ö", "o").replace("ş", "s").replace("ü", "u")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str) -> list[str]:
    return normalize_text(text).split()


def exact_match(pred: str, gold: str) -> int:
    return int(normalize_text(pred) == normalize_text(gold))


def token_f1(pred: str, gold: str) -> float:
    pred_tokens = tokenize(pred)
    gold_tokens = tokenize(gold)

    if not pred_tokens and not gold_tokens:
        return 1.0
    if not pred_tokens or not gold_tokens:
        return 0.0

    pred_counts = defaultdict(int)
    gold_counts = defaultdict(int)

    for t in pred_tokens:
        pred_counts[t] += 1
    for t in gold_tokens:
        gold_counts[t] += 1

    common = 0
    for t in pred_counts:
        common += min(pred_counts[t], gold_counts[t])

    if common == 0:
        return 0.0

    precision = common / len(pred_tokens)
    recall = common / len(gold_tokens)

    return 2 * precision * recall / (precision + recall)


def recall_like(pred: str, gold: str) -> float:
    pred_norm = normalize_text(pred)
    gold_norm = normalize_text(gold)

    if not pred_norm or not gold_norm:
        return 0.0

    return 1.0 if gold_norm in pred_norm else 0.0


def extract_best_answer(data: dict[str, Any]) -> str:
    # Önce graph answer, sonra llm answer, en son boş string
    graph_answer = data.get("graph_answer")
    if isinstance(graph_answer, dict) and graph_answer.get("answer"):
        return str(graph_answer["answer"])

    llm_answer = data.get("llm_answer")
    if isinstance(llm_answer, dict) and llm_answer.get("answer"):
        return str(llm_answer["answer"])

    # comparison branch için
    if data.get("source") == "graph_comparison" and data.get("answer"):
        return str(data["answer"])

    return ""


def build_entity_hint(question_item: dict[str, Any]) -> str:
    # Comparison sorularında entity_hint gerekmiyor
    if str(question_item.get("question_type", "")).startswith("compare_"):
        return ""

    reasoning_path = question_item.get("reasoning_path", [])
    if reasoning_path and isinstance(reasoning_path, list):
        first_entity = reasoning_path[0]
        if isinstance(first_entity, str):
            return first_entity.lower()

    return ""


def ask_backend(question: str, entity_hint: str) -> dict[str, Any]:
    params = {"question": question}
    if entity_hint:
        params["entity_hint"] = entity_hint

    response = requests.get(API_URL, params=params, timeout=120)
    response.raise_for_status()
    return response.json()


def summarize_group(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    if total == 0:
        return {
            "count": 0,
            "accuracy": 0.0,
            "em": 0.0,
            "f1": 0.0,
            "recall": 0.0,
        }

    accuracy = sum(r["correct"] for r in rows) / total
    em = sum(r["em"] for r in rows) / total
    f1 = sum(r["f1"] for r in rows) / total
    recall = sum(r["recall"] for r in rows) / total

    return {
        "count": total,
        "accuracy": round(accuracy, 4),
        "em": round(em, 4),
        "f1": round(f1, 4),
        "recall": round(recall, 4),
    }


def main() -> None:
    if not QUESTION_BANK_PATH.exists():
        raise FileNotFoundError(f"Question bank not found: {QUESTION_BANK_PATH}")

    with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if MAX_QUESTIONS is not None:
        questions = questions[:MAX_QUESTIONS]

    all_results: list[dict[str, Any]] = []

    by_difficulty: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_question_type: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for idx, item in enumerate(questions, start=1):
        question = item["question_text"]
        gold = str(item["gold_answer"])
        difficulty = str(item.get("difficulty", "unknown"))
        question_type = str(item.get("question_type", "unknown"))
        domain = str(item.get("domain", "unknown"))
        entity_hint = build_entity_hint(item)

        try:
            response_json = ask_backend(question, entity_hint)
            pred = extract_best_answer(response_json)

            em_score = exact_match(pred, gold)
            f1_score = token_f1(pred, gold)
            recall_score = recall_like(pred, gold)
            correct = em_score

            row = {
                "index": idx,
                "question_id": item.get("question_id"),
                "question": question,
                "gold_answer": gold,
                "predicted_answer": pred,
                "difficulty": difficulty,
                "question_type": question_type,
                "domain": domain,
                "correct": correct,
                "em": em_score,
                "f1": round(f1_score, 4),
                "recall": round(recall_score, 4),
            }

        except Exception as e:
            row = {
                "index": idx,
                "question_id": item.get("question_id"),
                "question": question,
                "gold_answer": gold,
                "predicted_answer": "",
                "difficulty": difficulty,
                "question_type": question_type,
                "domain": domain,
                "correct": 0,
                "em": 0,
                "f1": 0.0,
                "recall": 0.0,
                "error": str(e),
            }

        all_results.append(row)
        by_difficulty[difficulty].append(row)
        by_question_type[question_type].append(row)
        by_domain[domain].append(row)

        print(f"[{idx}/{len(questions)}] {question_type} | EM={row['em']} | Pred={row['predicted_answer']} | Gold={gold}")
        time.sleep(SLEEP_SECONDS)

    summary = {
        "overall": summarize_group(all_results),
        "by_difficulty": {k: summarize_group(v) for k, v in by_difficulty.items()},
        "by_question_type": {k: summarize_group(v) for k, v in by_question_type.items()},
        "by_domain": {k: summarize_group(v) for k, v in by_domain.items()},
        "results": all_results,
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("\nSaved evaluation results to:")
    print(OUTPUT_PATH)
    print("\nOverall:")
    print(summary["overall"])


if __name__ == "__main__":
    main()