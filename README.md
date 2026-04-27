# KG-Infused RAG — Turkey-Focused Question Answering System

This repository implements a Knowledge Graph (KG) supported Retrieval-Augmented Generation (RAG) system for a Turkey-focused subset of Wikidata5M. The main goal is to improve question-answering performance using multi-hop entity and relation paths and to generate a verified QA dataset.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Repository Structure](#repository-structure)
- [Frontend Overview](#frontend-overview)
- [Case Studies](#case-studies)
- [Setup & Run](#setup--run)
- [Backend Configuration](#backend-configuration)
- [Key Data Files](#key-data-files)
- [Important Scripts](#important-scripts)
- [Use Case](#use-case)
- [Notes](#notes)

## 🚀 Project Overview

- **Focus:** Turkey-related entities, especially Turkish football, film, and organization data
- **Data source:** Turkey-focused subset of Wikidata5M
- **Outputs:** multi-hop QA questions, comparison questions, verified question bank
- **Technology:** FastAPI, Neo4j, OLLAMA/OpenAI, React + Vite

## 📁 Repository Structure

- `backend/` — FastAPI API, KG retrieval, and answer generation logic
- `frontend/` — React-based user interface
- `data/` — raw data, processed results, and output files
- `scripts/` — data preparation, subset creation, and question generation workflows
- `notebooks/` — exploratory analysis and experimental reporting

## 🧠 Frontend Overview

The frontend provides the following main tabs:

- **Knowledge Graph:** graph-based query interface, demo questions, and answer details
- **Cypher Queries:** Neo4j query templates and query results
- **Case Studies:** analysis of successful and failed examples
- **Project Status:** project progress and metrics

These tabs are defined in `frontend/src/App.tsx`. The `CaseStudiesPage.tsx` page shows detailed case study examples.

### Key Frontend Files

- `frontend/src/App.tsx` — main app shell and tab management
- `frontend/src/pages/KnowledgeGraphPage.tsx` — knowledge graph query page
- `frontend/src/pages/CypherQueriesPage.tsx` — Cypher query page
- `frontend/src/pages/CaseStudiesPage.tsx` — case studies page
- `frontend/src/pages/ProjectStatusPage.tsx` — project status page

## 📚 Case Studies

The project includes real case studies in the frontend. The `frontend/src/pages/CaseStudiesPage.tsx` page demonstrates examples such as:

- successful 2-hop and 3-hop questions
- comparison questions
- KG data deficiency failures
- entity linking failures
- Turkish-English entity matching issues
- retrieval guidance failures
- LLM surface realization issues

Each case study includes:

- question text
- expected answer
- system answer
- pipeline analysis
- error analysis
- recommended improvements

## 🛠️ Setup & Run

### 1. Python environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Backend dependencies

The backend generally requires these packages:

- `fastapi`
- `uvicorn`
- `python-dotenv`
- `neo4j`
- `openai`
- `requests`

Install example:

```powershell
pip install fastapi uvicorn python-dotenv neo4j openai requests
```

> Note: If there is no `requirements.txt` file in the repository root, install dependencies manually.

### 3. Frontend setup

```powershell
cd frontend
npm install
```

### 4. Run the application

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

## 🔧 Backend Configuration

Default settings in `backend/app.py`:

- Neo4j URI: `neo4j://127.0.0.1:7687`
- Neo4j username: `neo4j`
- Neo4j password: `12345678`
- OLLAMA URL: `http://localhost:11434/api/generate`
- OLLAMA model: `qwen2.5:3b`

### Environment variables

Add the following to a `.env` file if needed:

```env
OPENAI_API_KEY=your_openai_api_key
```

## 📌 Key Data Files

- `data/processed/verified_question_bank.json` — verified question bank
- `data/processed/relation_frequency_turkiye_subset.csv` — allowed relation list
- `backend/app.py` — graph retrieval and LLM answer logic
- `scripts/generate_verified_question_bank.py` — question bank generation pipeline

## 🧩 Important Scripts

- `scripts/load_basic_maps.py` — loads entity and relation maps
- `scripts/find_turkey` — discovers Turkey-focused entities
- `scripts/build_turkiye_general_subset.py` — builds the Turkey subset
- `scripts/generate_verified_question_bank.py` — generates verified QA pairs
- `scripts/evaluate_current_system.py` — evaluates system performance

## 💡 Use Case

1. Extract the Turkey subset from Wikidata5M.
2. Generate QA data from the subset.
3. Load the data into Neo4j.
4. Start the FastAPI backend.
5. Explore results and case studies in the frontend.

## 📝 Notes

- The frontend pages are defined under `frontend/src/pages`.
- `CaseStudiesPage` presents both successful and failed examples.
- The system is designed to support multi-hop reasoning over Turkey-related football, film, and organization data.

---

## 🎯 Goal

This repository presents a Turkey-focused KG-Infused RAG system. It covers both data preparation and QA inference workflows in separate sections.


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