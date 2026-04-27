#.\.venv\Scripts\python.exe -m uvicorn backend.app:app --reload
from email.mime import text
import os
import csv
import unicodedata
import json
import requests
from pathlib import Path
from collections import deque

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from neo4j import GraphDatabase
from numpy import record
from openai import OpenAI
EVAL_RESULTS_PATH = Path("data/processed/evaluation_results_current_system.json")
load_dotenv()

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"
app = FastAPI(title="KG-Infused RAG - Türkiye Domain API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

URI = "neo4j://127.0.0.1:7687"
USERNAME = "neo4j"
PASSWORD = "12345678"
DATABASE = "neo4j"

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

MAX_ROUNDS = 3
MAX_NEIGHBORS_PER_NODE = 40

QUESTION_BANK_PATH = Path("data/processed/verified_question_bank.json")

def load_question_bank():
    if not QUESTION_BANK_PATH.exists():
        return []
    with open(QUESTION_BANK_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

QUESTION_BANK = load_question_bank()

def load_allowed_relations():
    path = Path("data/processed/relation_frequency_turkiye_subset.csv")
    allowed = set()

    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            import csv
            reader = csv.DictReader(f)
            for row in reader:
                rel = row["relation_name"].strip()
                if rel:
                    allowed.add(rel)

    return allowed

ALLOWED_RELATIONS = load_allowed_relations()
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def ollama_graph_grounded_answer(question: str, graph_answer: dict | None, kg_summary: str = ""):
    if not graph_answer:
        return {
            "answer": "Graph üzerinde yeterli cevap bulunamadı.",
            "source": "ollama_fallback"
        }

    short_answer = graph_answer.get("answer", "").strip()
    reasoning_summary = graph_answer.get("reasoning_summary", "").strip()

    prompt = f"""
Senin görevin sadece verilen graph cevabını düzgün Türkçe cümleye çevirmek.

Kurallar:
- Sadece verilen cevabı kullan.
- Yeni bilgi ekleme.
- Tahmin yapma.
- soruyu cevabın içinde kullan.
- Tek cümle yaz.
- türkçe dil yapısına uyarak yaz.
- Cevap kesin değilse bunu söyleme, sadece verilen graph cevabını cümleleştir.

Soru:
{question}

Graph cevabı:
{short_answer}

Reasoning özeti:
{reasoning_summary}

İstenen çıktı:
Sadece kısa ve düzgün bir Türkçe cevap cümlesi.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "top_p": 0.3,
                    "num_predict": 80
                }
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("response", "").strip()

        if not text:
            return {
                "answer": f"Sorunun graph üzerinde bulunan cevabı: {short_answer}",
                "source": "ollama_fallback"
            }

        return {
            "answer": text,
            "source": f"ollama:{OLLAMA_MODEL}",
        }

    except Exception as e:
        print("OLLAMA ERROR:", e)
        return {
            "answer": f"Sorunun graph üzerinde bulunan cevabı: {short_answer}",
            "source": "ollama_fallback",
        }

def ollama_comparison_answer(question: str, comparison_result: dict | None):
    if not comparison_result:
        return {
            "answer": "Comparison sonucu üretilemedi.",
            "source": "ollama_fallback"
        }

    answer = comparison_result.get("answer", "")
    entities = comparison_result.get("entities", [])
    left_value = comparison_result.get("left_value", "")
    right_value = comparison_result.get("right_value", "")
    pattern = comparison_result.get("pattern", "")

    prompt = f"""
Senin görevin graph comparison sonucunu düzgün Türkçe cümleye çevirmek.

Kurallar:
- Sadece verilen bilgileri kullan.
- Yeni bilgi ekleme.
- Tahmin yapma.
- soruyu cevabın içinde kullan.
- Tek veya en fazla iki kısa cümle yaz.
- Cevabı net yaz.

Soru:
{question}

Pattern:
{pattern}

Entities:
{entities}

Left value:
{left_value}

Right value:
{right_value}

Comparison answer:
{answer}

Sadece kısa ve düzgün Türkçe cevap döndür.
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0,
                    "top_p": 0.3,
                    "num_predict": 80
                }
            },
            timeout=60,
        )
        response.raise_for_status()
        data = response.json()

        text = data.get("response", "").strip()
        llm_answer = ollama_comparison_answer(question, {
        "pattern": pattern,
        "entities": [entity1, entity2],
        "left_value": value1,
        "right_value": value2,
        "answer": answer,
    })
        if not text:
            return {
                "answer": f"Comparison sonucu: {llm_answer}",
                "source": "ollama_fallback"
            }

        return {
        "source": "graph_comparison",
        "question": question,
        "pattern": pattern,
        "entities": [entity1, entity2],
        "left_retrieval": retrieval1,
        "right_retrieval": retrieval2,
        "left_path": path1,
        "right_path": path2,
        "left_value": value1,
        "right_value": value2,
        "answer": answer,
        "llm_answer": llm_answer,
    }

    except Exception as e:
        print("OLLAMA COMPARISON ERROR:", e)
        return {
            "answer": f"Comparison sonucu: {llm_answer}",
            "source": "ollama_fallback"
        }

def question_relation_weights(question: str):
    q = question.lower()
    weights = {}

    def add(rel, val):
        if rel in ALLOWED_RELATIONS:
            weights[rel] = weights.get(rel, 0) + val

    # -----------------------------
    # Sports / team / stadium
    # -----------------------------
    if (
        "team" in q
        or "club" in q
        or "footballer" in q
        or "player" in q
        or "played for" in q
        or "plays for" in q
        or "oynadığı takım" in q
        or "futbolcu" in q
        or "oyuncu" in q
    ):
        add("member of sports team", 6)

    if (
        "stadium" in q
        or "stadyum" in q
        or "venue" in q
        or "arena" in q
        or "home stadium" in q
        or "home ground" in q
    ):
        add("home venue", 7)

    if (
        "architectural style" in q
        or "architecture" in q
        or "architectural design" in q
        or "mimari tarz" in q
        or "mimari stil" in q
        or "mimari üslup" in q
    ):
        add("architectural style", 9)
        add("home venue", 4)

    if "league" in q or "lig" in q:
        add("league", 5)

    if "position" in q or "pozisyon" in q:
        add("position played on team / speciality", 6)

    if "coach" in q or "teknik direktör" in q or "manager" in q:
        add("head coach", 8)

    # -----------------------------
    # Birth / city / location
    # -----------------------------
    if (
        "where" in q
        or "nerede" in q
        or "city" in q
        or "şehir" in q
        or "location" in q
        or "which city" in q
        or "in which city" in q
    ):
        add("location", 4)
        add("headquarters location", 4)
        add("located in the administrative territorial entity", 5)
        add("place of birth", 7)

    if (
        "born" in q
        or "birth" in q
        or "doğ" in q
        or "birthplace" in q
        or "place of birth" in q
        or "where was" in q
    ):
        add("place of birth", 9)

    if "country" in q or "ülke" in q or "nereli" in q:
        add("country", 5)
        add("country of citizenship", 6)
        add("country for sport", 4)
        add("country of origin", 4)

    if "citizenship" in q or "vatandaş" in q:
        add("country of citizenship", 7)

    # -----------------------------
    # Film / music / company / education
    # -----------------------------
    if "director" in q or "yönetmen" in q:
        add("director", 7)

    if "award" in q or "ödül" in q:
        add("award received", 7)

    if "actor" in q or "cast" in q or "oyuncu" in q:
        add("cast member", 6)

    if "plak şirketi" in q or "record label" in q or "label" in q:
        add("record label", 7)

    if "aynı ülke" in q:
        add("country", 8)

    if "aynı lig" in q:
        add("league", 8)

    if "aynı yerde doğ" in q:
        add("place of birth", 8)

    if "bölge" in q or "region" in q:
        add("located in the administrative territorial entity", 7)

    if "ortak ülke" in q:
        add("country", 9)

    if "educated" in q or "okudu" in q or "üniversite" in q or "university" in q:
        add("educated at", 7)

    if "academic" in q or "degree" in q or "derece" in q:
        add("academic degree", 6)

    if "company" in q or "şirket" in q:
        add("headquarters location", 5)
        add("industry", 5)
        add("employer", 4)

    if "industry" in q or "sektör" in q:
        add("industry", 6)

    if "occupation" in q or "meslek" in q:
        add("occupation", 6)

    if "genre" in q or "tür" in q:
        add("genre", 6)

    return weights

def detect_question_pattern(question: str):
    q = question.lower()

    # -----------------------------
    # 1) Comparison patterns
    # -----------------------------
    if (
        "aynı ülkedeki takımlarda mı" in q
        or "aynı ülkedeki takimlarda mi" in q
        or "are they in teams from the same country" in q
        or "same country teams" in q
    ):
        return "compare_team_country_same"

    if (
        "both play for" in q
        or "both played for" in q
        or "ikisi de" in q and "oynadi mi" in q
        or "ikisi de" in q and "oynadı mı" in q
    ):
        return "compare_same_team_membership"

    if "aynı ligde" in q or "same league" in q:
        return "compare_team_league_same"

    if (
        "şirketlerinin merkezleri aynı ülkede mi" in q
        or "sirketlerinin merkezleri ayni ulkede mi" in q
        or "are the headquarters in the same country" in q
        or "same headquarters country" in q
    ):
        return "compare_company_hq_country_same"

    if (
        "aynı ülkedeki üniversitelerde mi okudu" in q
        or "ayni ulkedeki universitelerde mi okudu" in q
        or "did they study in universities in the same country" in q
        or "same university country" in q
    ):
        return "compare_educated_country_same"

    if (
        "aynı ülkedeki plak şirketlerine mi bağlı" in q
        or "ayni ulkedeki plak sirketlerine mi bagli" in q
        or "are they signed to record labels from the same country" in q
        or "same record label country" in q
    ):
        return "compare_record_label_country_same"

    if (
        "yönetmenleri aynı yerde mi doğmuştur" in q
        or "yonetmenleri ayni yerde mi dogmustur" in q
        or "were the directors born in the same place" in q
        or "same director birth place" in q
    ):
        return "compare_director_birth_place_same"

    if (
        "hangi ortak ülkeye ait takımlarda oynuyor" in q
        or "hangi ortak ulkeye ait takimlarda oynuyor" in q
        or "which common country do their teams belong to" in q
        or "shared team country" in q
    ):
        return "compare_team_country_which"

    if (
        "daha önce doğmuştur" in q
        or "daha once dogmustur" in q
        or "who was born earlier" in q
        or "who was born first" in q
    ):
        return "compare_birthday"

    # -----------------------------
    # 2) Architecture / stadium special patterns
    # -----------------------------
    if (
        "architectural style of galatasaray's home stadium" in q
        or "architectural style of beşiktaş's home stadium" in q
        or "architectural style of besiktas's home stadium" in q
        or "architectural style of the home stadium" in q
        or "mimari tarzı nedir" in q and "stadyum" in q
    ):
        return "team_venue_architecture"

    if (
        "architectural style of the stadium of the team" in q
        or "oynadığı takımın stadyumunun mimari tarzı" in q
        or "home stadium architectural style" in q
    ):
        return "player_team_venue_architecture"

    if (
        "country of the city where the stadium of the team the player played for is located" in q
        or "oynadığı takımın stadyumunun bulunduğu şehrin ülkesi" in q
    ):
        return "player_team_venue_city_country"

    # -----------------------------
    # 3) Specific long / multi-hop patterns
    # -----------------------------
    if (
        "stadyumunun bulunduğu şehrin ülkesi" in q
        or "stadyumunun bulundugu sehrin ulkesi" in q
        or "country of the city where the stadium is located" in q
    ):
        return "team_venue_city_country"

    if (
        "şirketinin merkezinin bulunduğu şehrin ülkesi" in q
        or "sirketinin merkezinin bulundugu sehrin ulkesi" in q
        or "country of the city where the company's headquarters is located" in q
    ):
        return "company_hq_city_country"

    if (
        "üniversitenin bulunduğu şehrin ülkesi" in q
        or "universitenin bulundugu sehrin ulkesi" in q
        or "country of the city where the university is located" in q
    ):
        return "educated_at_city_country"

    if (
        "stadyumunun bulunduğu şehir" in q
        or "stadyumunun bulundugu sehir" in q
        or "which city is the stadium in" in q
        or "stadium city" in q
    ):
        return "team_venue_city"

    if (
        "stadyumunun bulunduğu ülke" in q
        or "stadyumunun bulundugu ulke" in q
        or "which country is the stadium in" in q
        or "stadium country" in q
    ):
        return "team_venue_country"

    if (
        "yönetmeninin doğduğu yerin bağlı olduğu bölge" in q
        or "yonetmeninin dogdugu yerin bagli oldugu bolge" in q
        or "region of the director's birthplace" in q
    ):
        return "director_birth_region"

    if (
        "yönetmeninin doğduğu yerin ülkesi" in q
        or "yonetmeninin dogdugu yerin ulkesi" in q
        or "country of the director's birthplace" in q
    ):
        return "director_birth_country"

    if (
        "teknik direktörünün doğum yeri" in q
        or "teknik direktorunun dogum yeri" in q
        or "head coach's place of birth" in q
        or "birthplace of the head coach" in q
        or "where was the head coach born" in q
    ):
        return "coach_birth"

    if (
        "filminin yönetmeninin doğum yeri" in q
        or "yönetmeninin doğum yeri" in q
        or "director's place of birth" in q
        or "birthplace of the director" in q
        or "where was the director born" in q
    ):
        return "director_birth"

    if (
        "yönetmeninin kazandığı ödül" in q
        or "yonetmeninin kazandigi odul" in q
        or "award won by the director" in q
        or "director's award" in q
    ):
        return "director_award"

    if (
        "oynadığı takımın ülkesi" in q
        or "oynadigi takimin ulkesi" in q
        or "country of the team" in q
        or "which country is the team in" in q
    ):
        return "team_country"

    if (
        "oynadığı takım hangi ligdedir" in q
        or "oynadigi takim hangi ligdedir" in q
        or "which league is the team in" in q
        or "team league" in q
    ):
        return "team_league"

    if (
        "oynadığı takımın stadyumu nedir" in q
        or "oynadigi takimin stadyumu nedir" in q
        or "what is the team's stadium" in q
        or "home venue of the team" in q
    ):
        return "team_venue"

    if (
        "oynadığı takımın merkezi nerededir" in q
        or "oynadigi takimin merkezi nerededir" in q
        or "where is the team's headquarters" in q
        or "team headquarters" in q
    ):
        return "team_headquarters"

    if (
        "şirketinin merkezinin bulunduğu ülke" in q
        or "sirketinin merkezinin bulundugu ulke" in q
        or "which country is the company's headquarters in" in q
        or "company headquarters country" in q
    ):
        return "company_hq_country"

    if (
        "mezun olduğu üniversitenin ülkesi" in q
        or "mezun oldugu universitenin ulkesi" in q
        or "country of the university they graduated from" in q
    ):
        return "educated_at_country"

    if (
        "bağlı olduğu plak şirketinin ülkesi" in q
        or "bagli oldugu plak sirketinin ulkesi" in q
        or "country of the record label" in q
    ):
        return "record_label_country"

    if (
        "okuduğu üniversitenin ülkesi" in q
        or "okudugu universitenin ulkesi" in q
        or "country of the university studied at" in q
    ):
        return "university_country"

    # -----------------------------
    # 3) Single-hop but still specific
    # -----------------------------
    if "vatandaş" in q or "citizenship" in q or "country of citizenship" in q:
        return "citizenship"

    if (
        "teknik direktör" in q
        or "teknik direktor" in q
        or "head coach" in q
        or "coach" in q
        or "manager" in q
    ):
        return "head_coach"

    if "hangi lig" in q or "league" in q or "lig" in q:
        return "league"

    if "yönetmen" in q or "director" in q:
        return "director"

    if "üniversite" in q or "educated" in q or "studied at" in q or "okudu" in q:
        return "educated_at"

    if (
        "architectural style" in q
        or "mimari tarz" in q
        or "mimari stil" in q
    ):
        return "stadium_architecture"

    if (
        "stadyum" in q
        or "stadium" in q
        or "venue" in q
        or "arena" in q
    ):
        return "venue"

    # -----------------------------
    # 4) Most generic patterns at the end
    # -----------------------------
    if (
        "nereli" in q
        or "nerede doğ" in q
        or "hangi şehirde doğ" in q
        or "doğum yeri" in q
        or "birthplace" in q
        or "place of birth" in q
        or ("where was" in q and "born" in q)
        or ("in which city" in q and "born" in q)
        or "birth" in q
    ):
        return "direct_birth"

    if "ülkesi" in q or "hangi ülkede" in q or "country" in q:
        return "country"

    return "generic"


def expected_hop_count(question: str):
    pattern = detect_question_pattern(question)

    mapping = {
        "direct_birth": 1,
        "citizenship": 1,
        "head_coach": 1,
        "league": 1,
        "venue": 1,
        "country": 1,
        "director": 1,
        "educated_at": 1,
        "stadium_architecture": 1,

        "team_country": 2,
        "team_league": 2,
        "team_venue": 2,
        "team_headquarters": 2,
        "director_award": 2,
        "company_hq_country": 2,
        "educated_at_country": 2,
        "record_label_country": 2,
        "coach_birth": 2,
        "director_birth": 2,
        "university_country": 2,
        "team_venue_architecture": 2,

        "director_birth_region": 3,
        "company_hq_city_country": 3,
        "educated_at_city_country": 3,
        "team_venue_city": 4,
        "team_venue_country": 4,
        "director_birth_country": 3,
        "player_team_venue_architecture": 3,

        "team_venue_city_country": 4,
        "player_team_venue_city_country": 4,

        "compare_same_team_membership": 1,
        "compare_birthday": 2,
        "compare_team_country_same": 2,
        "compare_team_league_same": 2,
        "compare_company_hq_country_same": 2,
        "compare_educated_country_same": 2,
        "compare_record_label_country_same": 2,
        "compare_director_birth_place_same": 2,
        "compare_team_country_which": 2,

        "generic": None,
    }

    return mapping.get(pattern, None)

def comparison_required_relations(pattern: str):
    mapping = {
        "compare_team_country_same": {"member of sports team", "country"},
        "compare_team_league_same": {"member of sports team", "league"},
        "compare_company_hq_country_same": {"headquarters location", "country"},
        "compare_educated_country_same": {"educated at", "country"},
        "compare_record_label_country_same": {"record label", "country"},
        "compare_director_birth_place_same": {"director", "place of birth"},
        "compare_team_country_which": {"member of sports team", "country"},
        "compare_same_team_membership": {"member of sports team"},
    }
    return mapping.get(pattern, set())

def extract_comparison_entities_and_target_team(question: str):
    q = question.strip().rstrip("?")

    lower_q = q.lower()

    separators = [" and ", " ve "]
    split_sep = None
    for sep in separators:
        if sep in lower_q:
            split_sep = sep
            break

    if not split_sep:
        return None, None, None

    # orijinal string üzerinde böl
    idx = lower_q.find(split_sep)
    left = q[:idx].strip()
    right = q[idx + len(split_sep):].strip()

    target_markers = [" both play for ", " both played for ", " ikisi de "]
    marker_used = None

    for marker in target_markers:
        if marker in right.lower():
            marker_used = marker
            break

    if marker_used:
        ridx = right.lower().find(marker_used)
        entity2 = right[:ridx].strip()
        target_team = right[ridx + len(marker_used):].strip()
        return left, entity2, target_team

    # İngilizce sık kullanılan yapı:
    # "X and Y both play for Z"
    if " both play for " in lower_q:
        after = q[lower_q.find(" both play for ") + len(" both play for "):].strip()
        entity2 = right[: right.lower().find(" both play for ")].strip()
        return left, entity2, after

    if " both played for " in lower_q:
        after = q[lower_q.find(" both played for ") + len(" both played for "):].strip()
        entity2 = right[: right.lower().find(" both played for ")].strip()
        return left, entity2, after

    return left, right, None

def normalize_team_name(text: str) -> str:
    return normalize_text(text).replace("-", " ").replace(".", " ")

def find_team_membership_path_by_target_id(paths, target_entity_id: str):
    if not paths or not target_entity_id:
        return None

    candidates = []

    for p in paths:
        triples = p.get("triples", [])
        if len(triples) != 1:
            continue

        tr = triples[0]
        if tr["relation"] != "member of sports team":
            continue

        if tr["object_id"] == target_entity_id:
            candidates.append(p)

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return candidates[0]

def path_matches_pattern(path_triples, pattern: str):
    relations = [tr["relation"] for tr in path_triples]

    if pattern == "direct_birth":
        return len(relations) == 1 and relations == ["place of birth"]

    if pattern == "citizenship":
        return len(relations) == 1 and relations == ["country of citizenship"]

    if pattern == "head_coach":
        return len(relations) == 1 and relations == ["head coach"]

    if pattern == "league":
        return len(relations) == 1 and relations == ["league"]

    if pattern == "venue":
        return len(relations) == 1 and relations == ["home venue"]

    if pattern == "stadium_architecture":
        return len(relations) == 1 and relations == ["architectural style"]

    if pattern == "country":
        return len(relations) == 1 and (
            relations == ["country"] or relations == ["country of citizenship"]
        )

    if pattern == "director":
        return len(relations) == 1 and relations == ["director"]

    if pattern == "educated_at":
        return len(relations) == 1 and relations == ["educated at"]

    if pattern == "team_country":
        return len(relations) == 2 and relations == ["member of sports team", "country"]

    if pattern == "team_league":
        return len(relations) == 2 and relations == ["member of sports team", "league"]

    if pattern == "team_venue":
        return len(relations) == 2 and relations == ["member of sports team", "home venue"]

    if pattern == "team_headquarters":
        return len(relations) == 2 and relations == ["member of sports team", "headquarters location"]

    if pattern == "director_award":
        return len(relations) == 2 and relations == ["director", "award received"]

    if pattern == "company_hq_country":
        return len(relations) == 2 and relations == ["headquarters location", "country"]

    if pattern == "educated_at_country":
        return len(relations) == 2 and relations == ["educated at", "country"]

    if pattern == "record_label_country":
        return len(relations) == 2 and relations == ["record label", "country"]

    if pattern == "coach_birth":
        return len(relations) == 2 and relations == ["head coach", "place of birth"]

    if pattern == "director_birth":
        return len(relations) == 2 and relations == ["director", "place of birth"]

    if pattern == "university_country":
        return len(relations) == 2 and relations == ["educated at", "country"]

    if pattern == "team_venue_architecture":
        return len(relations) == 2 and relations == ["home venue", "architectural style"]

    if pattern == "player_team_venue_architecture":
        return len(relations) == 3 and relations == [
            "member of sports team",
            "home venue",
            "architectural style",
        ]

    if pattern == "team_venue_city_country":
        return len(relations) == 4 and relations == [
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
            "country",
        ]

    if pattern == "player_team_venue_city_country":
        return len(relations) == 4 and relations == [
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
            "country",
        ]

    if pattern == "director_birth_region":
        return len(relations) == 3 and relations == [
            "director",
            "place of birth",
            "located in the administrative territorial entity",
        ]

    if pattern == "company_hq_city_country":
        return len(relations) == 3 and relations == [
            "headquarters location",
            "location",
            "country",
        ]

    if pattern == "educated_at_city_country":
        return len(relations) == 3 and relations == [
            "educated at",
            "location",
            "country",
        ]

    if pattern == "team_venue_city":
        return len(relations) == 3 and relations == [
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
        ]

    if pattern == "team_venue_country":
        return len(relations) == 3 and relations == [
            "member of sports team",
            "home venue",
            "country",
        ]

    if pattern == "director_birth_country":
        return len(relations) == 3 and relations == [
            "director",
            "place of birth",
            "country",
        ]

    if pattern == "compare_birthday":
        return "birthday" in relations or "place of birth" in relations

    if pattern == "compare_team_country_same":
        return len(relations) == 2 and relations == ["member of sports team", "country"]

    if pattern == "compare_team_league_same":
        return len(relations) == 2 and relations == ["member of sports team", "league"]

    if pattern == "compare_company_hq_country_same":
        return len(relations) == 2 and relations == ["headquarters location", "country"]

    if pattern == "compare_educated_country_same":
        return len(relations) == 2 and relations == ["educated at", "country"]

    if pattern == "compare_record_label_country_same":
        return len(relations) == 2 and relations == ["record label", "country"]

    if pattern == "compare_director_birth_place_same":
        return len(relations) == 2 and relations == ["director", "place of birth"]

    if pattern == "compare_team_country_which":
        return len(relations) == 2 and relations == ["member of sports team", "country"]

    return True

def required_question_relations(question: str):
    pattern = detect_question_pattern(question)
    required = set()

    def add(rel):
        if rel in ALLOWED_RELATIONS:
            required.add(rel)

    pattern_mapping = {
        "direct_birth": {"place of birth"},
        "citizenship": {"country of citizenship"},
        "head_coach": {"head coach"},
        "league": {"league"},
        "venue": {"home venue"},
        "director": {"director"},
        "educated_at": {"educated at"},
        "stadium_architecture": {"architectural style"},

        "team_country": {"member of sports team", "country"},
        "team_league": {"member of sports team", "league"},
        "team_venue": {"member of sports team", "home venue"},
        "team_headquarters": {"member of sports team", "headquarters location"},
        "director_award": {"director", "award received"},
        "company_hq_country": {"headquarters location", "country"},
        "educated_at_country": {"educated at", "country"},
        "record_label_country": {"record label", "country"},
        "coach_birth": {"head coach", "place of birth"},
        "director_birth": {"director", "place of birth"},
        "university_country": {"educated at", "country"},
        "team_venue_architecture": {"home venue", "architectural style"},

        "player_team_venue_architecture": {
            "member of sports team",
            "home venue",
            "architectural style",
        },

        "team_venue_city_country": {
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
            "country",
        },

        "player_team_venue_city_country": {
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
            "country",
        },

        "director_birth_region": {
            "director",
            "place of birth",
            "located in the administrative territorial entity",
        },
        "company_hq_city_country": {
            "headquarters location",
            "location",
            "country",
        },
        "educated_at_city_country": {
            "educated at",
            "location",
            "country",
        },
        "team_venue_city": {
            "member of sports team",
            "home venue",
            "located in the administrative territorial entity",
        },
        "team_venue_country": {
            "member of sports team",
            "home venue",
            "country",
        },
        "director_birth_country": {
            "director",
            "place of birth",
            "country",
        },

        "compare_team_country_same": {"member of sports team", "country"},
        "compare_team_league_same": {"member of sports team", "league"},
        "compare_company_hq_country_same": {"headquarters location", "country"},
        "compare_educated_country_same": {"educated at", "country"},
        "compare_record_label_country_same": {"record label", "country"},
        "compare_director_birth_place_same": {"director", "place of birth"},
        "compare_team_country_which": {"member of sports team", "country"},
    }

    for rel in pattern_mapping.get(pattern, set()):
        add(rel)

    return required

def is_comparison_pattern(pattern: str):
    return pattern.startswith("compare_")

def extract_two_entities_from_comparison_question(question: str):
    q = question.strip().rstrip("?")

    if " ve " not in q:
        return None, None

    left, right = q.split(" ve ", 1)

    stop_phrases = [
        " aynı ülkedeki takımlarda mı oynuyor",
        " aynı ligde oynayan takımlarda mı bulunuyor",
        " aynı ülkedeki üniversitelerde mi okudu",
        " aynı ülkedeki plak şirketlerine mi bağlı",
        " filmlerinin yönetmenleri aynı yerde mi doğmuştur",
        " hangi ortak ülkeye ait takımlarda oynuyor",
        " şirketlerinin merkezleri aynı ülkede mi",
    ]

    entity1 = left.strip()
    entity2 = right.strip()

    for s in stop_phrases:
        if s in entity2:
            entity2 = entity2.split(s)[0].strip()

    return entity1, entity2

def extract_two_entities_from_comparison_question(question: str):
    q = question.strip().rstrip("?")
    q_lower = q.lower()

    # Yeni tip: X and Y both play(ed) for Z
    if " both play for " in q_lower or " both played for " in q_lower:
        marker = " both play for " if " both play for " in q_lower else " both played for "
        left_part, target_team = q.split(marker, 1)
        target_team = target_team.strip()

        if " and " in left_part:
            entity1, entity2 = left_part.split(" and ", 1)
        elif " ve " in left_part:
            entity1, entity2 = left_part.split(" ve ", 1)
        else:
            return None, None

        entity1 = entity1.replace("Did ", "").replace("did ", "").strip()
        entity2 = entity2.strip()

        return entity1, entity2, target_team
    
    def normalize_team_name(text: str) -> str:
        return normalize_text(text).replace("-", " ").replace(".", " ").strip()


def find_team_membership_path(paths, target_team: str):
    if not paths or not target_team:
        return None

    target_norm = normalize_team_name(target_team)
    candidates = []

    for p in paths:
        triples = p.get("triples", [])
        if len(triples) != 1:
            continue

        tr = triples[0]
        if tr["relation"] != "member of sports team":
            continue

        obj_norm = normalize_team_name(tr["object_name"])

        if (
            obj_norm == target_norm
            or target_norm in obj_norm
            or obj_norm in target_norm
        ):
            candidates.append(p)

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return candidates[0]

    # Eski Türkçe comparison tipi
    if " ve " in q:
        left, right = q.split(" ve ", 1)

        stop_phrases = [
            " aynı ülkedeki takımlarda mı oynuyor",
            " aynı ligde oynayan takımlarda mı bulunuyor",
            " aynı ülkedeki üniversitelerde mi okudu",
            " aynı ülkedeki plak şirketlerine mi bağlı",
            " filmlerinin yönetmenleri aynı yerde mi doğmuştur",
            " hangi ortak ülkeye ait takımlarda oynuyor",
            " şirketlerinin merkezleri aynı ülkede mi",
        ]

        entity1 = left.strip()
        entity2 = right.strip()

        for s in stop_phrases:
            if s in entity2:
                entity2 = entity2.split(s)[0].strip()

        return entity1, entity2, None

    # İngilizce generic and fallback
    if " and " in q:
        left, right = q.split(" and ", 1)
        return left.strip(), right.strip(), None

    return None, None, None

def comparison_required_relations(pattern: str):
    mapping = {
        "compare_team_country_same": {"member of sports team", "country"},
        "compare_team_league_same": {"member of sports team", "league"},
        "compare_company_hq_country_same": {"headquarters location", "country"},
        "compare_educated_country_same": {"educated at", "country"},
        "compare_record_label_country_same": {"record label", "country"},
        "compare_director_birth_place_same": {"director", "place of birth"},
        "compare_team_country_which": {"member of sports team", "country"},
    }
    return mapping.get(pattern, set())

def find_best_path_by_relations(paths, required_relations: set):
    if not paths:
        return None

    candidates = []

    for p in paths:
        triples = p.get("triples", [])
        relation_set = {t["relation"] for t in triples}

        if required_relations.issubset(relation_set):
            candidates.append(p)

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return candidates[0]

def extract_final_value_from_path(path):
    if not path:
        return None

    triples = path.get("triples", [])
    if not triples:
        return None

    return triples[-1]["object_name"]

def compare_final_values(pattern, value1, value2):
    if value1 is None or value2 is None:
        return None

    if pattern in {
        "compare_team_country_same",
        "compare_team_league_same",
        "compare_company_hq_country_same",
        "compare_educated_country_same",
        "compare_record_label_country_same",
        "compare_director_birth_place_same",
    }:
        return "Evet" if value1 == value2 else "Hayır"

    if pattern == "compare_team_country_which":
        return value1 if value1 == value2 else f"{value1} / {value2}"

    return None

def preferred_first_hop_relations(question: str):
    pattern = detect_question_pattern(question)

    mapping = {
        "director_birth": {"director"},
        "director_birth_region": {"director"},
        "director_birth_country": {"director"},
        "director_award": {"director"},
        "coach_birth": {"head coach"},
        "team_country": {"member of sports team"},
        "team_league": {"member of sports team"},
        "team_venue": {"member of sports team"},
        "team_headquarters": {"member of sports team"},
        "team_venue_city": {"member of sports team"},
        "team_venue_country": {"member of sports team"},
        "team_venue_city_country": {"member of sports team"},
        "educated_at_country": {"educated at"},
        "university_country": {"educated at"},
        "record_label_country": {"record label"},
        "company_hq_country": {"headquarters location"},
    }

    return mapping.get(pattern, set())

def clean_entity_hint(entity_hint: str) -> str:
    if not entity_hint:
        return ""

    hint = normalize_text(entity_hint)

    banned = {
        "",
        "yazi",
        "yazisi",
        "soru",
        "sorusu",
        "question",
        "text",
        "metin",
        "yazi yazisi",
    }

    if hint in banned:
        return ""

    return entity_hint.strip()

import re

def extract_entity_hint_from_question(question: str) -> str:
    q = question.strip()

    # comparison ise seed çıkarma, zaten ayrı branch'e gidecek
    pattern = detect_question_pattern(q)
    if is_comparison_pattern(pattern):
        return ""

    # İngilizce doğum soruları
    patterns = [
        r"where was (.+?) born",
        r"in which city was (.+?) born",
        r"what is the architectural style of (.+?) home stadium",
        r"what is the architectural style of (.+?)'s home stadium",
        r"which country is the stadium of (.+?) in",
        r"which league is the team of (.+?) in",
    ]

    q_lower = q.lower()

    for pat in patterns:
        m = re.search(pat, q_lower)
        if m:
            raw = q[m.start(1):m.end(1)].strip(" ?,.\"'")
            return raw

    # Türkçe basit kalıplar
    tr_patterns = [
        r"(.+?) nerede doğ",
        r"(.+?) hangi şehirde doğ",
        r"(.+?) doğum yeri",
        r"(.+?) oynadığı takımın ülkesi",
        r"(.+?) oynadığı takım hangi ligdedir",
        r"(.+?) oynadığı takımın stadyumu nedir",
    ]

    for pat in tr_patterns:
        m = re.search(pat, normalize_text(q))
        if m:
            return m.group(1).strip(" ?,.\"'")

    return ""

def handle_comparison_question(question: str):
    pattern = detect_question_pattern(question)

    # Yeni tip: iki oyuncu aynı takımda mı oynadı?
    if pattern == "compare_same_team_membership":
        entity1, entity2, target_team = extract_two_entities_from_comparison_question(question)

        if not entity1 or not entity2 or not target_team:
            return {
                "source": "graph_comparison",
                "answer": None,
                "error": "Could not extract entities or target team.",
                "entities": [entity1, entity2],
                "target_team": target_team,
            }

        retrieval1 = run_spreading_activation(question, entity1)
        retrieval2 = run_spreading_activation(question, entity2)

        path1 = find_team_membership_path(retrieval1.get("paths", []), target_team)
        path2 = find_team_membership_path(retrieval2.get("paths", []), target_team)

        left_value = path1 is not None
        right_value = path2 is not None

        answer = "Evet" if (left_value and right_value) else "Hayır"

        return {
            "source": "graph_comparison",
            "question": question,
            "pattern": pattern,
            "entities": [entity1, entity2],
            "target_team": target_team,
            "left_retrieval": retrieval1,
            "right_retrieval": retrieval2,
            "left_path": path1,
            "right_path": path2,
            "left_value": left_value,
            "right_value": right_value,
            "answer": answer,
        }

    # Eski comparison akışı
    entity1, entity2, _ = extract_two_entities_from_comparison_question(question)
    if not entity1 or not entity2:
        return {
            "source": "graph_comparison",
            "answer": None,
            "error": "Could not extract two entities from comparison question.",
            "entities": [entity1, entity2],
        }

    required_relations = comparison_required_relations(pattern)
    if not required_relations:
        return {
            "source": "graph_comparison",
            "answer": None,
            "error": "Unsupported comparison pattern.",
            "entities": [entity1, entity2],
        }

    retrieval1 = run_spreading_activation(question, entity1)
    retrieval2 = run_spreading_activation(question, entity2)

    path1 = find_best_path_by_relations(retrieval1.get("paths", []), required_relations)
    path2 = find_best_path_by_relations(retrieval2.get("paths", []), required_relations)

    value1 = extract_final_value_from_path(path1)
    value2 = extract_final_value_from_path(path2)

    answer = compare_final_values(pattern, value1, value2)

    return {
        "source": "graph_comparison",
        "question": question,
        "pattern": pattern,
        "entities": [entity1, entity2],
        "left_retrieval": retrieval1,
        "right_retrieval": retrieval2,
        "left_path": path1,
        "right_path": path2,
        "left_value": value1,
        "right_value": value2,
        "answer": answer,
    }

def score_path(path, relation_weights):
    score = 0.0
    for triple in path:
        rel = triple[2]
        score += relation_weights.get(rel, 1)
    score -= max(0, len(path) - 1) * 0.4
    return score

def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("ı", "i").replace("ğ", "g").replace("ü", "u")
    text = text.replace("ş", "s").replace("ö", "o").replace("ç", "c")
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.split())

MANUAL_SEED_ID_MAP = {
    "gs": "Q43134",
    "galatasaray": "Q43134",
    "galatasaray sk": "Q43134",
    "galatasaray s k": "Q43134",
    "galatasaray s.k.": "Q43134",
    "galatasaray s. k.": "Q43134",

    "fb": "Q6601875",
    "fenerbahce": "Q6601875",
    "fenerbahçe": "Q6601875",
    "fenerbahce sk": "Q6601875",
    "fenerbahçe sk": "Q6601875",
    "fenerbahce s k": "Q6601875",
    "fenerbahçe s k": "Q6601875",
    "fenerbahce s.k.": "Q6601875",
    "fenerbahçe s.k.": "Q6601875",

    "bjk": "Q172567",
    "besiktas": "Q172567",
    "beşiktaş": "Q172567",
    "besiktas jk": "Q172567",
    "beşiktaş jk": "Q172567",
    "besiktas j k": "Q172567",
    "beşiktaş j k": "Q172567",
    "besiktas j.k.": "Q172567",
    "beşiktaş j.k.": "Q172567",
}


def find_seed_entity(tx, entity_hint, question=None):
    hint_norm = normalize_text(entity_hint)

    # -------------------------------------------------
    # 1) GS / FB / BJK gibi çok ambigu takımları direkt
    #    sabit entityId ile seedle
    # -------------------------------------------------
    if hint_norm in MANUAL_SEED_ID_MAP:
        entity_id = MANUAL_SEED_ID_MAP[hint_norm]

        exact_id_cypher = """
        MATCH (e:Entity {entityId: $entity_id})
        RETURN e.entityId AS entityId,
               e.name AS name,
               coalesce(e.description, "") AS description
        LIMIT 1
        """
        row = tx.run(exact_id_cypher, entity_id=entity_id).single()

        if row:
            return [{
                "entityId": row["entityId"],
                "name": row["name"],
                "description": row["description"],
                "score": 999999
            }]

    # -------------------------------------------------
    # 2) Normal entity search
    #    önce name üzerinden ara
    # -------------------------------------------------
    strong_cypher = """
    MATCH (e:Entity)
    WHERE toLower(e.name) = toLower($entity_hint)
       OR toLower(e.name) STARTS WITH toLower($entity_hint)
       OR toLower(e.name) CONTAINS toLower($entity_hint)
    RETURN e.entityId AS entityId,
           e.name AS name,
           coalesce(e.description, "") AS description
    LIMIT 50
    """
    raw_candidates = list(tx.run(strong_cypher, entity_hint=entity_hint))

    # -------------------------------------------------
    # 3) Name'den hiçbir şey gelmezse description fallback
    # -------------------------------------------------
    if not raw_candidates:
        weak_cypher = """
        MATCH (e:Entity)
        WHERE toLower(coalesce(e.description, "")) CONTAINS toLower($entity_hint)
        RETURN e.entityId AS entityId,
               e.name AS name,
               coalesce(e.description, "") AS description
        LIMIT 50
        """
        raw_candidates = list(tx.run(weak_cypher, entity_hint=entity_hint))

    q_norm = normalize_text(question or "")
    scored = []

    for c in raw_candidates:
        name = c["name"] or ""
        desc = c["description"] or ""

        name_norm = normalize_text(name)
        desc_norm = normalize_text(desc)
        low = f"{name_norm} {desc_norm}"

        score = 0

        # -------------------------------------------------
        # 4) Name similarity
        # -------------------------------------------------
        if name_norm == hint_norm:
            score += 1500
        elif name_norm.startswith(hint_norm):
            score += 900
        elif hint_norm in name_norm:
            score += 500

        if hint_norm in desc_norm:
            score += 40

        score -= abs(len(name_norm) - len(hint_norm))

        # -------------------------------------------------
        # 5) Generic junk penalties
        # -------------------------------------------------
        if "list of" in low:
            score -= 120
        if "season" in low:
            score -= 100
        if "lyceum" in low or "lisesi" in low:
            score -= 100
        if "university" in low or "universite" in low:
            score -= 80

        # -------------------------------------------------
        # 6) Question-aware boosts
        # -------------------------------------------------
        sports_context = any(x in q_norm for x in [
            "stadium", "home stadium", "venue", "arena",
            "football", "footballer", "player", "played for",
            "team", "club", "goalkeeper", "coach", "league"
        ])

        birth_context = any(x in q_norm for x in [
            "born", "birthplace", "place of birth",
            "where was", "in which city", "dogum", "doğum", "dogdu", "doğdu"
        ])

        architecture_context = any(x in q_norm for x in [
            "architectural style", "architecture", "mimari tarz", "mimari stil"
        ])

        if sports_context:
            if "football club" in low or "association football club" in low:
                score += 260
            if "sports club" in low:
                score += 140
            if "turkish football club" in low:
                score += 220
            if "athletics" in low:
                score -= 220

        if architecture_context:
            if "stadium" in low or "arena" in low:
                score += 180
            if "football club" in low or "sports club" in low:
                score += 120
            if "athletics" in low:
                score -= 120

        if birth_context:
            if any(x in low for x in [
                "footballer", "former footballer", "person", "human",
                "goalkeeper", "manager", "coach", "player"
            ]):
                score += 300

            if any(x in low for x in [
                "football club", "sports club", "athletics club", "team",
                "stadium", "arena"
            ]):
                score -= 180

        # description-only false positive cezası
        if hint_norm not in name_norm and hint_norm in desc_norm:
            score -= 220

        scored.append({
            "entityId": c["entityId"],
            "name": name,
            "description": desc,
            "score": score
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:10]


def get_neighbors(tx, entity_id, allowed_relations):
    cypher = """
    MATCH (s:Entity {entityId:$entity_id})-[r:RELATION]->(o:Entity)
    WHERE r.relation_name IN $allowed_relations
    RETURN s.entityId AS s_id,
           s.name AS s_name,
           r.relation_name AS relation,
           o.entityId AS o_id,
           o.name AS o_name
    """
    return list(tx.run(
        cypher,
        entity_id=entity_id,
        allowed_relations=list(allowed_relations)
    ))

def resolve_entity_id_from_hint(entity_hint: str, question: str = ""):
    with driver.session(database=DATABASE) as session:
        candidates = session.execute_read(find_seed_entity, entity_hint, question)

    if not candidates:
        return None

    return candidates[0]

def build_debug_info(question, pattern, expected_hops, required_rels, scored_paths, filtered_paths):
    debug_paths = []

    for p in scored_paths[:15]:
        triples = p["triples"]
        relations_in_path = [tr["relation"] for tr in triples]

        accepted = any(p is fp for fp in filtered_paths)

        debug_paths.append({
            "score": p["score"],
            "hop_count": len(triples),
            "relations": relations_in_path,
            "triples": triples,
            "accepted": accepted,
        })

    return {
        "question": question,
        "pattern": pattern,
        "expected_hops": expected_hops,
        "required_relations": list(required_rels),
        "candidate_paths_before_filter": len(scored_paths),
        "candidate_paths_after_filter": len(filtered_paths),
        "paths": debug_paths,
    }

def run_spreading_activation(question: str, entity_hint: str):
    entity_hint = clean_entity_hint(entity_hint)

    if not entity_hint:
        entity_hint = extract_entity_hint_from_question(question)

    if not entity_hint:
        return {
            "seed_candidates": [],
            "used_seed": None,
            "paths": [],
            "kg_summary": "",
            "debug": {
                "question": question,
                "pattern": detect_question_pattern(question),
                "expected_hops": expected_hop_count(question),
                "required_relations": list(required_question_relations(question)),
                "candidate_paths_before_filter": 0,
                "candidate_paths_after_filter": 0,
                "paths": [],
                "error": "No valid entity hint and no entity could be extracted from question."
            },
        }

    with driver.session(database=DATABASE) as session:
        candidates = session.execute_read(find_seed_entity, entity_hint, question)

    preferred_first_hops = preferred_first_hop_relations(question)

    for i, c in enumerate(candidates[:5], start=1):
        print(f"SEED_{i}:",
              c["entityId"],
              "|",
              c["name"],
              "| score:",
              c.get("score"))

    if not candidates:
        return {
            "seed_candidates": [],
            "used_seed": None,
            "paths": [],
            "kg_summary": "",
            "debug": {
                "question": question,
                "pattern": detect_question_pattern(question),
                "expected_hops": expected_hop_count(question),
                "required_relations": list(required_question_relations(question)),
                "candidate_paths_before_filter": 0,
                "candidate_paths_after_filter": 0,
                "paths": [],
            },
        }

    seed = candidates[0]
    relation_weights = question_relation_weights(question)

    visited_entities = {seed["entityId"]}
    frontier = deque([(seed["entityId"], seed["name"], 0, [])])
    completed_paths = []
    print("member of sports team" in ALLOWED_RELATIONS)
    print("home venue" in ALLOWED_RELATIONS)
    print("located in the administrative territorial entity" in ALLOWED_RELATIONS)
    print("country" in ALLOWED_RELATIONS)
    while frontier:
        current_id, current_name, depth, path = frontier.popleft()

        if depth >= MAX_ROUNDS:
            if path:
                completed_paths.append(path)
            continue

        with driver.session(database=DATABASE) as session:
            neighbors = session.execute_read(get_neighbors, current_id, ALLOWED_RELATIONS)

        expanded = False

        for record in neighbors:
            relation = record["relation"]
            next_id = record["o_id"]
            next_name = record["o_name"]

            if depth == 0 and preferred_first_hops:
                if relation not in preferred_first_hops:
                    continue
            
            #if relation not in ALLOWED_RELATIONS:
            #    continue

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

            completed_paths.append(new_path)

        if not expanded and path:
            completed_paths.append(path)

    scored_paths = [
        {
            "score": score_path(path, relation_weights),
            "triples": [
                {
                    "subject_id": t[0],
                    "subject_name": t[1],
                    "relation": t[2],
                    "object_id": t[3],
                    "object_name": t[4],
                }
                for t in path
            ]
        }
        for path in completed_paths if path
    ]
    print("\n--- SCORED PATHS (TOP 15) ---")
    for i, p in enumerate(scored_paths[:15], start=1):
        triples = p["triples"]
        relations_in_path = [tr["relation"] for tr in triples]
        print(f"PATH_{i}: score={p['score']}, hops={len(triples)}, relations={relations_in_path}")
        for tr in triples:
            print("   ", tr["subject_name"], "--[", tr["relation"], "]-->", tr["object_name"])

    # Önce genel skor sıralaması
    scored_paths.sort(key=lambda x: x["score"], reverse=True)

    required_rels = required_question_relations(question)
    pattern = detect_question_pattern(question)
    expected_hops = expected_hop_count(question)

    

    filtered_paths = []
    debug_paths = []

    print("PATTERN:", detect_question_pattern(question))
    print("EXPECTED_HOPS:", expected_hop_count(question))
    print("REQUIRED:", required_question_relations(question))

    for p in scored_paths:
        triples = p["triples"]
        relations_in_path = [tr["relation"] for tr in triples]
        relation_set = set(relations_in_path)

        accepted = True
        reject_reason = ""

        if required_rels and not required_rels.issubset(relation_set):
            accepted = False
            reject_reason = "missing_required_relations"

        if accepted and expected_hops is not None and len(triples) != expected_hops:
            accepted = False
            reject_reason = f"wrong_hop_count:{len(triples)}"

        if accepted and not path_matches_pattern(triples, pattern):
            accepted = False
            reject_reason = f"pattern_mismatch:{relations_in_path}"


        debug_paths.append({
            "score": p["score"],
            "hop_count": len(triples),
            "relations": relations_in_path,
            "triples": triples,
            "accepted": accepted,
            "reject_reason": reject_reason,
        })

        if accepted:
            filtered_paths.append(p)

    # Asıl sonuç sadece filtrelenmiş path'lerden gelsin
    filtered_paths.sort(key=lambda x: x["score"], reverse=True)
    top_paths = filtered_paths[:10]

    if not top_paths:
        return {
            "seed_candidates": [
                {
                    "entityId": c["entityId"],
                    "name": c["name"],
                    "description": c["description"][:200] if c.get("description") else ""
                }
                for c in candidates
            ],
            "used_seed": {
                "entityId": seed["entityId"],
                "name": seed["name"]
            },
            "paths": [],
            "kg_summary": "",
            "debug": {
                "question": question,
                "pattern": pattern,
                "expected_hops": expected_hops,
                "required_relations": list(required_rels),
                "candidate_paths_before_filter": len(scored_paths),
                "candidate_paths_after_filter": len(filtered_paths),
                "paths": debug_paths[:15],
            },
        }

    summary_lines = []
    for path in top_paths[:3]:
        for triple in path["triples"]:
            summary_lines.append(
                f"{triple['subject_name']} --[{triple['relation']}]--> {triple['object_name']}"
            )

    kg_summary = "\n".join(summary_lines)

    return {
        "seed_candidates": [
            {
                "entityId": c["entityId"],
                "name": c["name"],
                "description": c["description"][:200] if c.get("description") else ""
            }
            for c in candidates
        ],
        "used_seed": {
            "entityId": seed["entityId"],
            "name": seed["name"]
        },
        "paths": top_paths,
        "kg_summary": kg_summary,
        "debug": {
            "question": question,
            "pattern": pattern,
            "expected_hops": expected_hops,
            "required_relations": list(required_rels),
            "candidate_paths_before_filter": len(scored_paths),
            "candidate_paths_after_filter": len(filtered_paths),
            "paths": debug_paths[:15],
        },
    }

def find_exact_question_bank_answer(question: str):
    q_norm = normalize_text(question)

    for item in QUESTION_BANK:
        candidate = item.get("question_text", "")
        if normalize_text(candidate) == q_norm:
            return {
                "answer": item.get("gold_answer"),
                "source": "verified_question_bank",
                "reasoning_summary": "Exact match found in verified question bank.",
                "matched_question": item.get("question_text"),
                "question_type": item.get("question_type"),
                "difficulty": item.get("difficulty"),
            }

    return None
def is_comparison_pattern(pattern: str):
    return pattern.startswith("compare_")


def extract_two_entities_from_comparison_question(question: str):
    q = question.strip().rstrip("?")

    if " ve " not in q:
        return None, None

    left, right = q.split(" ve ", 1)

    stop_phrases = [
        " aynı ülkedeki takımlarda mı oynuyor",
        " aynı ligde oynayan takımlarda mı bulunuyor",
        " aynı ülkedeki üniversitelerde mi okudu",
        " aynı ülkedeki plak şirketlerine mi bağlı",
        " filmlerinin yönetmenleri aynı yerde mi doğmuştur",
        " hangi ortak ülkeye ait takımlarda oynuyor",
        " şirketlerinin merkezleri aynı ülkede mi",
    ]

    entity1 = left.strip()
    entity2 = right.strip()

    for s in stop_phrases:
        if s in entity2:
            entity2 = entity2.split(s)[0].strip()

    return entity1, entity2


def comparison_required_relations(pattern: str):
    mapping = {
        "compare_team_country_same": {"member of sports team", "country"},
        "compare_team_league_same": {"member of sports team", "league"},
        "compare_company_hq_country_same": {"headquarters location", "country"},
        "compare_educated_country_same": {"educated at", "country"},
        "compare_record_label_country_same": {"record label", "country"},
        "compare_director_birth_place_same": {"director", "place of birth"},
        "compare_team_country_which": {"member of sports team", "country"},
    }
    return mapping.get(pattern, set())


def find_best_path_by_relations(paths, required_relations: set):
    if not paths:
        return None

    candidates = []

    for p in paths:
        triples = p.get("triples", [])
        relation_set = {t["relation"] for t in triples}

        if required_relations.issubset(relation_set):
            candidates.append(p)

    if not candidates:
        return None

    candidates.sort(key=lambda x: x.get("score", 0), reverse=True)
    return candidates[0]


def extract_final_value_from_path(path):
    if not path:
        return None

    triples = path.get("triples", [])
    if not triples:
        return None

    return triples[-1]["object_name"]


def compare_final_values(pattern, value1, value2):
    if value1 is None or value2 is None:
        return None

    if pattern in {
        "compare_team_country_same",
        "compare_team_league_same",
        "compare_company_hq_country_same",
        "compare_educated_country_same",
        "compare_record_label_country_same",
        "compare_director_birth_place_same",
    }:
        return "Evet" if value1 == value2 else "Hayır"

    if pattern == "compare_team_country_which":
        return value1 if value1 == value2 else f"{value1} / {value2}"

    return None


def handle_comparison_question(question: str):
    pattern = detect_question_pattern(question)

    entity1, entity2 = extract_two_entities_from_comparison_question(question)
    if not entity1 or not entity2:
        return {
            "source": "graph_comparison",
            "answer": None,
            "error": "Could not extract two entities from comparison question.",
            "entities": [entity1, entity2],
        }

    required_relations = comparison_required_relations(pattern)
    if not required_relations:
        return {
            "source": "graph_comparison",
            "answer": None,
            "error": "Unsupported comparison pattern.",
            "entities": [entity1, entity2],
        }

    retrieval1 = run_spreading_activation(question, entity1)
    retrieval2 = run_spreading_activation(question, entity2)

    path1 = find_best_path_by_relations(retrieval1.get("paths", []), required_relations)
    path2 = find_best_path_by_relations(retrieval2.get("paths", []), required_relations)

    value1 = extract_final_value_from_path(path1)
    value2 = extract_final_value_from_path(path2)

    answer = compare_final_values(pattern, value1, value2)

    return {
        "source": "graph_comparison",
        "question": question,
        "pattern": pattern,
        "entities": [entity1, entity2],
        "left_retrieval": retrieval1,
        "right_retrieval": retrieval2,
        "left_path": path1,
        "right_path": path2,
        "left_value": value1,
        "right_value": value2,
        "answer": answer,
    }

def extract_graph_answer(paths):
    if not paths:
        return None

    best_path = paths[0]["triples"]
    if not best_path:
        return None

    return {
        "answer": best_path[-1]["object_name"],
        "source": "graph_verified",
        "reasoning_summary": " -> ".join(
            [best_path[0]["subject_name"]]
            + [t["relation"] for t in best_path]
            + [best_path[-1]["object_name"]]
        ),
    }


def graph_grounded_llm_answer(question: str, kg_summary: str):
    if not kg_summary.strip():
        return None

    if client is None:
        return {
            "answer": "OpenAI API key missing. Graph evidence exists, but LLM verbalization is unavailable.",
            "source": "graph_verified",
            "reasoning_summary": "Graph facts found, but OPENAI_API_KEY is not configured."
        }

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "Answer ONLY using the provided KG summary. "
                    "Do not use outside knowledge. "
                    "If insufficient, say exactly: Insufficient graph evidence."
                ),
            },
            {
                "role": "user",
                "content": f"Question:\n{question}\n\nKG Summary:\n{kg_summary}",
            },
        ],
    )

    return {
        "answer": response.output_text.strip(),
        "source": "graph_verified",
        "reasoning_summary": "Answer verbalized from KG summary."
    }


def llm_query_expansion(question: str, kg_summary: str):
    if client is None or not kg_summary.strip():
        return {
            "expanded_query": question
        }

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You expand the user's question using only the provided KG summary. "
                    "Return a single concise expanded query."
                ),
            },
            {
                "role": "user",
                "content": f"Original question:\n{question}\n\nKG Summary:\n{kg_summary}",
            },
        ],
    )

    return {
        "expanded_query": response.output_text.strip()
    }


def llm_fallback_answer(question: str):
    if client is None:
        return {
            "answer": "LLM fallback unavailable because OPENAI_API_KEY is missing.",
            "source": "llm_fallback",
            "reasoning_summary": "No API key configured."
        }

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": (
                    "You are answering when the local knowledge graph does not have enough evidence. "
                    "Be concise and explicitly note that this is an LLM fallback answer, not graph-verified."
                ),
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    return {
        "answer": response.output_text.strip(),
        "source": "llm_fallback",
        "reasoning_summary": "Answer generated from LLM fallback because graph evidence was insufficient."
    }


@app.get("/")
def root():
    return {"message": "KG-Infused RAG Türkiye API is running"}


@app.get("/stats")
def stats():
    with driver.session(database=DATABASE) as session:
        total_entities = session.run(
            "MATCH (n:Entity) RETURN count(n) AS c"
        ).single()["c"]

        total_relations = session.run(
            "MATCH ()-[r:RELATION]->() RETURN count(r) AS c"
        ).single()["c"]

        rel_rows = session.run("""
            MATCH ()-[r:RELATION]->()
            RETURN r.relation_name AS relation, count(*) AS freq
            ORDER BY freq DESC
            LIMIT 12
        """)

        relation_distribution = [
            {"relation": row["relation"], "freq": row["freq"]}
            for row in rel_rows
        ]

    return {
        "total_entities": total_entities,
        "total_relations": total_relations,
        "relation_distribution": relation_distribution
    }


@app.get("/demo-questions")
def demo_questions():
    import json
    import random
    from collections import defaultdict

    path = Path("data/processed/verified_question_bank.json")

    if not path.exists():
        return {"questions": [], "summary": {"error": "verified_question_bank.json not found"}}

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    random.shuffle(data)

    target_counts = {
        "1-hop": 10,
        "2-hop": 30,
        "3-hop": 15,
        "comparison": 5,
    }

    def diverse_pick(items, target_count):
        by_type = defaultdict(list)

        for item in items:
            qtype = item.get("question_type", "unknown")
            by_type[qtype].append(item)

        for qtype in by_type:
            random.shuffle(by_type[qtype])

        selected = []

        # önce her type'tan birer tane
        type_names = list(by_type.keys())
        random.shuffle(type_names)

        for qtype in type_names:
            if len(selected) >= target_count:
                break
            if by_type[qtype]:
                selected.append(by_type[qtype].pop(0))

        # sonra kalan boşluğu doldur
        leftovers = []
        for qtype in by_type:
            leftovers.extend(by_type[qtype])

        random.shuffle(leftovers)

        for item in leftovers:
            if len(selected) >= target_count:
                break
            selected.append(item)

        return selected

    by_difficulty = defaultdict(list)
    for item in data:
        diff = item.get("difficulty", "unknown")
        by_difficulty[diff].append(item)

    final_questions = []

    for difficulty, count in target_counts.items():
        picked = diverse_pick(by_difficulty.get(difficulty, []), count)
        final_questions.extend(picked)

    random.shuffle(final_questions)

    return {
        "questions": final_questions,
        "summary": {
            "total": len(final_questions),
            "counts": {
                "1-hop": sum(1 for q in final_questions if q.get("difficulty") == "1-hop"),
                "2-hop": sum(1 for q in final_questions if q.get("difficulty") == "2-hop"),
                "3-hop": sum(1 for q in final_questions if q.get("difficulty") == "3-hop"),
                "comparison": sum(1 for q in final_questions if q.get("difficulty") == "comparison"),
            }
        }
    }


def json_load_safe(file_obj):
    import json
    return json.load(file_obj)


@app.get("/run-query")
def run_query(question: str, entity_hint: str):
    return run_spreading_activation(question, entity_hint)


@app.get("/ask")
def ask(question: str, entity_hint: str = ""):
    pattern = detect_question_pattern(question)

    # Comparison soruları için ayrı branch
    if is_comparison_pattern(pattern):
        return handle_comparison_question(question)

    # Normal sorular için mevcut akış
    retrieval = run_spreading_activation(question, entity_hint)
    paths = retrieval.get("paths", [])
    kg_summary = retrieval.get("kg_summary", "")

    if paths:
        graph_answer = extract_graph_answer(paths)
        llm_answer = ollama_graph_grounded_answer(question, graph_answer, kg_summary )

        return {
            "question": question,
            "entity_hint": entity_hint,
            "retrieval": retrieval,
            "graph_answer": graph_answer,
            "query_expansion": llm_query_expansion(question, kg_summary),
            "llm_answer": llm_answer
        }

    return {
        "question": question,
        "entity_hint": entity_hint,
        "retrieval": retrieval,
        "graph_answer": None,
        "query_expansion": {"expanded_query": question},
        "llm_answer": llm_fallback_answer(question),
    }

