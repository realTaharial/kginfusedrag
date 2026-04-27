import { useEffect, useMemo, useState } from "react";
import "./App.css";

import TopBar from "./components/TopBar";
import TabNav from "./components/TabNav";
import StatGrid from "./components/statGrid";

import KnowledgeGraphPage from "./pages/KnowledgeGraphPage";
import CypherQueriesPage from "./pages/CypherQueriesPage";
import EvaluationPage from "./pages/EvaluationPage";
import CaseStudiesPage from "./pages/CaseStudiesPage";
import ProjectStatusPage from "./pages/ProjectStatusPage";

import type {
  AskResponse,
  DemoQuestion,
  StatsResponse,
  TabKey,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

type MethodMetric = {
  method: string;
  acc: number;
  f1: number;
  em: number;
  recall: number;
};

export default function App() {
  const [stats, setStats] = useState<StatsResponse | null>(null);
  const [demoQuestions, setDemoQuestions] = useState<DemoQuestion[]>([]);
  const [askResult, setAskResult] = useState<AskResponse | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>("knowledge");
  const [loadingPage, setLoadingPage] = useState(true);
  const [loadingQuery, setLoadingQuery] = useState(false);
  const [error, setError] = useState("");

  const [question, setQuestion] = useState(
    "Orhan Ovacıklı'ın oynadığı takımın ülkesi neresidir?"
  );
  const [entityHint, setEntityHint] = useState("orhan ovacıklı");

  useEffect(() => {
    async function loadInitial() {
      try {
        setLoadingPage(true);
        setError("");

        const [statsRes, demoRes] = await Promise.all([
          fetch(`${API_BASE}/stats`),
          fetch(`${API_BASE}/demo-questions`),
        ]);

        if (!statsRes.ok) throw new Error("Stats endpoint failed");
        if (!demoRes.ok) throw new Error("Demo endpoint failed");

        const statsJson: StatsResponse = await statsRes.json();
        const demoJson: { questions: DemoQuestion[] } = await demoRes.json();


        setStats(statsJson);
        setDemoQuestions(demoJson.questions || []);
      } catch (err) {
        console.error(err);
        setError("Backend data could not be loaded. Check FastAPI and Neo4j.");
      } finally {
        setLoadingPage(false);
      }
    }

    loadInitial();
  }, []);

  function looksLikeComparisonQuestion(text: string) {
    const q = text.toLowerCase();

    return (
      q.includes(" ve ") &&
      (
        q.includes("aynı") ||
        q.includes("hangi ortak") ||
        q.includes("same") ||
        q.includes("common") ||
        q.includes("compare")
      )
    );
  }

  async function runAsk() {
    try {
      setLoadingQuery(true);
      setError("");

      const isComparisonQuestion = looksLikeComparisonQuestion(question);

      const url = isComparisonQuestion
        ? `${API_BASE}/ask?question=${encodeURIComponent(question)}`
        : `${API_BASE}/ask?question=${encodeURIComponent(question)}&entity_hint=${encodeURIComponent(entityHint)}`;

      const res = await fetch(url);
      if (!res.ok) throw new Error("Ask endpoint failed");

      const json: AskResponse = await res.json();
      setAskResult(json);
    } catch (err) {
      console.error(err);
      setError("Query failed. Check backend logs.");
    } finally {
      setLoadingQuery(false);
    }
  }

  const relationChartData = useMemo(() => {
    return stats?.relation_distribution || [];
  }, [stats]);

  const difficultyStats = useMemo(() => {
    const counts = {
      "1-hop": 0,
      "2-hop": 0,
      "3-hop": 0,
      comparison: 0,
    };

    for (const q of demoQuestions) {
      if (q.difficulty === "2-hop") counts["2-hop"] += 1;
      else if (q.difficulty === "3-hop") counts["3-hop"] += 1;
      else if (q.difficulty === "comparison") counts["comparison"] += 1;
      else counts["1-hop"] += 1;
    }

    return counts;
  }, [demoQuestions]);

  const domainStats = useMemo(() => {
    const counts: Record<string, number> = {};

    for (const q of demoQuestions) {
      counts[q.domain] = (counts[q.domain] || 0) + 1;
    }

    return Object.entries(counts).map(([domain, count]) => ({
      domain,
      count,
    }));
  }, [demoQuestions]);

  function handleUseDemo(item: DemoQuestion) {
    setQuestion(item.question_text);

    const isComparison =
      item.difficulty === "comparison" ||
      item.question_type?.startsWith("compare_") ||
      looksLikeComparisonQuestion(item.question_text);

    if (isComparison) {
      setEntityHint("");
    } else {
      const firstEntity = item.reasoning_path[0] || "";
      setEntityHint(firstEntity.toLowerCase());
    }

    setActiveTab("knowledge");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <div className="app-shell">
      <div className="background-glow glow-1" />
      <div className="background-glow glow-2" />

      <TopBar />
      <TabNav activeTab={activeTab} setActiveTab={setActiveTab} />

      {error ? <div className="error-banner">{error}</div> : null}

      <StatGrid
        totalEntities={loadingPage ? "..." : stats?.total_entities ?? 0}
        totalRelations={loadingPage ? "..." : stats?.total_relations ?? 0}
        totalQuestions={loadingPage ? "..." : demoQuestions.length}
        topPaths={askResult?.retrieval?.paths?.length ?? 0}
      />

      {activeTab === "knowledge" && (
        <KnowledgeGraphPage
          relationChartData={relationChartData}
          askResult={askResult}
          question={question}
          setQuestion={setQuestion}
          entityHint={entityHint}
          setEntityHint={setEntityHint}
          runAsk={runAsk}
          loadingQuery={loadingQuery}
          demoQuestions={demoQuestions}
          onUseDemo={handleUseDemo}
          difficultyStats={difficultyStats}
        />
      )}

      {activeTab === "cypher" && <CypherQueriesPage />}


      {activeTab === "case_study" && <CaseStudiesPage />}

      {activeTab === "status" && <ProjectStatusPage />}
    </div>
  );
}