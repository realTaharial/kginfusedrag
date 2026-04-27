export type RelationItem = {
  relation: string;
  freq: number;
};

export type DemoQuestion = {
  question_id: string;
  question_text: string;
  reasoning_path: string[];
  gold_answer: string;
  difficulty: string;
  domain: string;
  question_type: string;
};

export type StatsResponse = {
  total_entities: number;
  total_relations: number;
  relation_distribution: RelationItem[];
};

export type TripleItem = {
  subject_id: string;
  subject_name: string;
  relation: string;
  object_id: string;
  object_name: string;
};

export type PathItem = {
  score: number;
  triples: TripleItem[];
};

export type QueryResult = {
  seed_candidates: { entityId: string; name: string; description?: string }[];
  used_seed: { entityId: string; name: string } | null;
  paths: PathItem[];
  kg_summary: string;
};

export type GraphAnswer = {
  answer: string;
  source: string;
  reasoning_summary: string;
} | null;

export type QueryExpansion = {
  expanded_query: string;
};

export type AskResponse = {
  question: string;
  entity_hint: string;
  retrieval: QueryResult;
  graph_answer: GraphAnswer;
  query_expansion: QueryExpansion;
  llm_answer: GraphAnswer;
};


export type TabKey =
  | "knowledge"
  | "cypher"
  | "evaluation"
  | "case_study"
  | "status";
