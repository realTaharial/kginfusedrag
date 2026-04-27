# KG-Infused RAG — Türkiye Odaklı Soru-Cevap Sistemi

Bu proje, Türkiye odaklı bir Wikidata5M alt kümesi üzerinde çalışan bir Knowledge Graph (KG) destekli Retrieval-Augmented Generation (RAG) sistemini hedefler. Amaç, çok adımlı bağlantılar ve ilişki yolları kullanarak Türkçe soru-cevap performansını geliştirmek ve doğrulanmış bir QA veri seti oluşturmaktır.

---

## 🚀 Proje Özeti

- **Odak:** Türkiye ilişkili varlıklar ve özellikle Türk futbolu üzerine bilgi grafiği sorguları
- **Veri kaynağı:** Wikidata5M'in Türkiye içeriğine indirgenmiş subset'i
- **Çıktılar:** Çok adımlı (multi-hop) QA soruları, karşılaştırma soruları ve KG destekli yanıt üretimi
- **Teknoloji yığını:** FastAPI, Neo4j, OLLAMA/OpenAI, React + Vite

## 📁 Repository Yapısı

- `backend/` — FastAPI tabanlı API ve KG tabanlı cevap üretim mantığı
- `frontend/` — React + Vite kullanıcı arayüzü
- `data/` — ham veri, işlenmiş veri ve üretim sonuçları
- `scripts/` — Türkiye odaklı subset oluşturma, grafik hazırlama, soru üretilmesi ve değerlendirme işlemleri
- `notebooks/` — analiz, keşif ve deneysel çalışmalar

## ⭐ Ana Özellikler

- Türkiye odaklı bilgi grafiği analizi
- Futbol, şehir, şirket, üniversite ve film gibi alanlarda çok adımlı ilişkisel QA
- Doğrulanmış soru bankası üretimi ve değerlendirmesi
- Görev bazlı graph-grounded yanıt üretimi
- OLLAMA/OpenAI kullanarak Türkçe ifade dönüşümü

## 🛠️ Kurulum

### 1. Python ortamı

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Backend bağımlılıkları

Aşağıdaki paketlere ihtiyaç vardır:

- `fastapi`
- `uvicorn`
- `python-dotenv`
- `neo4j`
- `openai`
- `requests`

Kurulum için örnek:

```powershell
pip install fastapi uvicorn python-dotenv neo4j openai requests
```

### 3. Frontend kurulumu

```powershell
cd frontend
npm install
```

### 4. Çalıştırma

Backend:

```powershell
cd ..
uvicorn backend.app:app --reload
```

Frontend:

```powershell
cd frontend
npm run dev
```

## ⚙️ Çalışma Koşulları

### `backend/app.py` tarafından kullanılan varsayılan ayarlar

- Neo4j URI: `neo4j://127.0.0.1:7687`
- Neo4j kullanıcı adı: `neo4j`
- Neo4j parola: `12345678`
- OLLAMA URL: `http://localhost:11434/api/generate`
- OLLAMA model: `qwen2.5:3b`

### Ortam değişkenleri

Aşağıdaki değişken `.env` dosyasına eklenebilir:

```env
OPENAI_API_KEY=your_openai_api_key
```

## 📌 Önemli Veri Dosyaları

- `data/processed/verified_question_bank.json` — doğrulanmış soru bankası
- `data/processed/relation_frequency_turkiye_subset.csv` — izin verilen ilişki seti
- `backend/app.py` — grafik tabanlı sorgu ve LLM destekli cevap üretimi

## 🧩 Önemli Scriptler

- `scripts/load_basic_maps.py` — temel varlık ve ilişki haritalarını yükleme
- `scripts/find_turkey` — Türkiye ile ilgili varlıkları keşfetme
- `scripts/build_turkiye_general_subset.py` — Türkiye odaklı alt küme oluşturma
- `scripts/generate_verified_question_bank.py` — doğrulanmış soru bankası üretme
- `scripts/evaluate_current_system.py` — sistem değerlendirmesi

## 💡 Kullanım Senaryosu

1. Türkiye odaklı Wikidata verileri üzerinden subset çıkarın.
2. Bu subset üzerinden çok adımlı soru üretin.
3. Neo4j üzerine veri yükleyin.
4. FastAPI backend ile soruları sorgulayın.
5. Frontend üzerinden sonuçları görüntüleyin.

## 📘 Notlar

- Proje, veri ve mantık açısından Türkiye futbolu ve geniş Türkiye ilişkileri üzerine inşa edilmiştir.
- Backend, grafik sonuçlarını Türkçe olarak daha doğal bir cümleye dönüştürmek için OLLAMA kullanır.
- React frontend, kullanıcı deneyimi için Vite ile hazırlandı.

---

## 🎯 Hedef

Bu repo, Türkiye odağındaki bilgi grafiği sorularını destekleyen bir RAG sistemi sunar. Hem veri hazırlama hem de soru-cevap aşamaları bu hedefe göre düzenlenmiştir.

Purpose

This phase contains the working implementation of the KG-Infused RAG pipeline.

The repository is organized in a modular way. Each major step of the pipeline is implemented in a separate script or module.

Repository Structure
kg_infused_rag_project/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── raw/
│   │   ├── wikidata5m_entity.txt
│   │   ├── wikidata5m_relation.txt
│   │   └── wikidata5m_text.txt
│   │
│   ├── processed/
│   │   ├── entity_map.json
│   │   ├── relation_map.json
│   │   └── generated_questions_pattern_b_filtered.csv
│   │
│   └── subset/
│       └── turkiye_related_subset.csv
│
├── scripts/
│   ├── load_basic_maps.py
│   ├── find_turkey.py
│   ├── confirm_turkey.py
│   ├── extract_football_candidates.py
│   ├── clean_turkish_football.py
│   ├── build_turkiye_general_subset.py
│   ├── generate_verified_question_bank.py
│   └── generate_comparison_questions.py
│
├── backend/
│   ├── graph_retriever.py
│   ├── entity_linker.py
│   ├── question_classifier.py
│   ├── comparison_handler.py
│   ├── llm_handler.py
│   └── answer_generator.py
│
├── artifacts/
│   ├── phase-1/
│   ├── phase-2/
│   ├── phase-3/
│   ├── phase-4/
│   ├── phase-5/
│   └── phase-6/
│
└── docs/
    ├── turkiye_entity_analysis_report.md
    ├── multi_hop_qa_dataset_report.md
    ├── experiment_results.md
    └── case_study_report.md
Main Components
Component	Purpose
load_basic_maps.py	Loads entity, relation, and text mappings
find_turkey.py	Searches for Türkiye-related entities
confirm_turkey.py	Confirms the Türkiye root entity
extract_football_candidates.py	Extracts football-related Türkiye entities
clean_turkish_football.py	Cleans and filters football seed entities
generate_verified_question_bank.py	Generates verified QA pairs from graph paths
graph_retriever.py	Retrieves graph paths from Neo4j
entity_linker.py	Finds the correct KG entity from user question
question_classifier.py	Detects question type and pattern
comparison_handler.py	Handles comparison questions
llm_handler.py	Connects local LLM for answer generation
answer_generator.py	Produces final graph-grounded answers
Running the Project

Install requirements:

pip install -r requirements.txt

Run the FastAPI backend:

python -m uvicorn app:app --reload

Generate verified questions:

python scripts/generate_verified_question_bank.py

Generate comparison questions:

python scripts/generate_comparison_questions.py
Requirements File

The project includes a requirements.txt file containing the necessary Python dependencies.

Example dependencies:

fastapi
uvicorn
neo4j
pandas
numpy
requests
python-dotenv
8.4 Experiment Results

Related Phase: Phase 5

Purpose

The experiment phase evaluates the performance of the KG-Infused RAG system and compares graph-grounded retrieval with other answering strategies.

Compared Methods
Method	Description
Graph-only QA	Answers are extracted directly from Neo4j graph paths
LLM-only QA	The language model answers without graph grounding
KG-Infused RAG	Graph retrieval is used first, then the LLM generates a grounded answer
Fallback LLM	Used only when the graph retrieval cannot find a valid answer
Evaluation Criteria

The system was evaluated using the following criteria:

Metric	Description
Answer correctness	Whether the predicted answer matches the gold answer
Path correctness	Whether the retrieved reasoning path matches the expected graph path
Entity linking accuracy	Whether the correct entity was selected from the question
Pattern detection accuracy	Whether the correct question type was detected
Failure rate	How often the system could not produce an answer
Explanation quality	Whether the answer includes understandable reasoning
Observed Results

The graph-based approach performs well on structured factual questions where the entity and relation can be clearly detected.

Strong results were observed for patterns such as:

team_country
team_league
team_venue
team_headquarters
company_hq_country
educated_at_country
university_country
director_birth

The most difficult cases were comparison questions and ambiguous entity mentions.

For example, the system can detect that a question is a comparison question, but it may fail if it cannot extract the two compared entities correctly.

Example failure output:

{
  "source": "graph_comparison",
  "answer": null,
  "error": "Could not extract two entities from comparison question.",
  "entities": [
    null,
    null
  ]
}
Experiment Summary
Category	Result
Single-hop questions	Generally successful
Multi-hop questions	Successful when reasoning path exists clearly
Comparison questions	Partially successful, needs stronger entity extraction
Entity ambiguity	Main source of errors
LLM fallback	Useful when graph result is empty
Graph-grounded answers	More reliable than LLM-only answers
Performance Analysis

The KG-Infused RAG approach provides more explainable answers than a standard LLM-only pipeline because it retrieves explicit graph paths from Neo4j.

The main advantage is that each answer can be supported with a reasoning path.

The main limitation is entity linking. If the system selects the wrong entity or cannot extract the entities from the question, the final answer becomes incorrect or empty.

8.5 Case Study Report

Related Phase: Phase 6

Purpose

This phase analyzes successful and unsuccessful examples from the system.

Successful Case Study 1: Single-Hop Football Question

Question:

What is the home stadium of Galatasaray S.K.?

Expected reasoning path:

Galatasaray S.K.
→ home venue
→ Ali Sami Yen Stadium

This is a successful case because the question contains a clear team entity and a clear relation type.

The system can detect:

entity: Galatasaray S.K.
relation: home venue
answer type: stadium

Final answer:

The home stadium of Galatasaray S.K. is Ali Sami Yen Stadium.
Successful Case Study 2: Birth Place Question

Question:

In which German city was Beşiktaş footballer Cenk Tosun born?

Expected reasoning path:

Cenk Tosun
→ place of birth
→ Wetzlar

This question is answerable because the entity and relation are clear.

The system detects the player entity and searches the graph for the place of birth relation.

Successful Case Study 3: Multi-Hop Director Question

Question:

The director of the movie was born in which administrative region?

Expected reasoning path:

Movie
→ director
→ Director
→ place of birth
→ Birth Place
→ located in the administrative territorial entity
→ Region

This is a harder example because it requires multiple graph hops.

The graph-based retrieval is useful here because the answer cannot be found from a single direct relation.

Unsuccessful Case Study 1: Ambiguous Entity Name

Problem:

Some football club names are ambiguous in Wikidata5M.

Example:

Galatasaray

The system may retrieve:

Galatasaray athletics

instead of:

Galatasaray S.K.

Reason:

The entity linker may select the wrong candidate when multiple entities contain the same name.

Recommendation:

Add stronger seed mapping and aliases for important football clubs.

Example high-quality seeds:

{
  "Besiktas": "Q172567",
  "Galatasaray": "Q43134",
  "Fenerbahce": "Q6601875"
}
Unsuccessful Case Study 2: Comparison Question Entity Extraction

Problem:

The system may understand that a question is a comparison question, but fail to extract the two compared entities.

Example output:

{
  "source": "graph_comparison",
  "answer": null,
  "error": "Could not extract two entities from comparison question.",
  "entities": [
    null,
    null
  ]
}

Reason:

Comparison questions usually contain two entities in a more complex sentence structure. If the parser cannot separate the two entities, the graph query cannot be executed.

Recommendation:

Implement pattern-specific extraction rules for comparison questions.

Example comparison templates:

Are Galatasaray and Beşiktaş in the same league?
Did Galatasaray and Fenerbahçe play in the same country?
Are Company A and Company B headquartered in the same country?
Error Categories
Error Type	Description	Recommendation
Entity linking error	Wrong entity selected from candidates	Add aliases and seed priority
Missing relation	Expected relation does not exist in graph	Expand subset or relation coverage
Missing entity	Entity is not included in selected subset	Improve candidate extraction
Comparison extraction error	Two entities cannot be extracted	Add comparison-specific parser
Ambiguous question	Question text is too general	Use question pattern detection
LLM hallucination risk	LLM may answer without graph evidence	Prefer graph-grounded answer generation
8.6 Final Project Report
Project Summary

This project implements a KG-Infused Retrieval-Augmented Generation system using a Türkiye-focused subset of Wikidata5M.

The system combines:

knowledge graph exploration
Türkiye-related entity extraction
verified multi-hop question generation
Neo4j graph traversal
entity linking
question pattern detection
graph-grounded answer generation
local LLM-based fallback and summarization

The final system is designed to answer structured multi-hop questions using explicit reasoning paths instead of relying only on language model knowledge.

Summary of All Phases
Phase	Description	Output
Phase 1	Türkiye entity exploration	Türkiye root entity and related matches
Phase 2	Domain selection and subset creation	Turkish football-focused entity set
Phase 3	Multi-hop QA generation	Verified question bank
Phase 4	KG-Infused RAG implementation	Working backend and modular code
Phase 5	Experiments	Result tables and performance analysis
Phase 6	Case studies	Success/failure analysis and recommendations
Findings

The most important findings are:

Türkiye-related data in Wikidata5M is large enough to support a focused QA system.
Turkish football is a suitable domain because it contains many connected entities.
Neo4j graph traversal is effective for answering structured factual questions.
Multi-hop questions can be generated automatically when verified graph paths exist.
KG-grounded answers are more explainable than LLM-only answers.
Entity linking is the most important challenge in the system.
Comparison questions require special handling because two entities must be extracted correctly.
Local LLM integration is useful for answer formatting, but graph evidence should remain the main source of truth.
Conclusions

The project successfully demonstrates how a knowledge graph can improve retrieval-augmented question answering.

Instead of generating answers only from a language model, the system retrieves entities and relations from Neo4j and uses those graph paths as evidence.

This makes the answers more reliable, explainable, and easier to debug.

The system performs best on direct factual and verified multi-hop questions. The main weakness is ambiguous entity detection and comparison question parsing.

Future Work

Future improvements can include:

improving entity linking with aliases and fuzzy matching
adding stronger seed entity mappings for important Turkish football clubs
supporting more relation types from Wikidata5M
improving comparison question parsing
adding frontend visualization for reasoning paths
expanding the dataset beyond football
evaluating the system with larger test sets
adding automatic error categorization
improving LLM prompt templates for graph-grounded answer generation
adding confidence scores for retrieved answers
Final Output

The final project includes:

Türkiye entity analysis report
selected domain justification
entity-relation map
verified multi-hop QA dataset
reasoning paths and gold answers in JSON format
working KG-Infused RAG backend
modular source code
README and usage documentation
requirements file
experiment result tables
performance analysis
case study report
final findings and future work recommendations