import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";

import QueryPanel from "../components/QueryPanel";
import AnswerCard from "../components/AnswerCard";
import PathCard from "../components/PatchCard";
import DemoQuestionCard from "../components/DemoQuestionCard";

import type {
  AskResponse,
  DemoQuestion,
  RelationItem,
} from "../types";

type Props = {
  relationChartData: RelationItem[];
  askResult: AskResponse | null;
  question: string;
  setQuestion: (v: string) => void;
  entityHint: string;
  setEntityHint: (v: string) => void;
  runAsk: () => void;
  loadingQuery: boolean;
  demoQuestions: DemoQuestion[];
  onUseDemo: (item: DemoQuestion) => void;
  difficultyStats: {
    "1-hop": number;
    "2-hop": number;
    "3-hop": number;
    comparison: number;
  };
};

export default function KnowledgeGraphPage({
  relationChartData,
  askResult,
  question,
  setQuestion,
  entityHint,
  setEntityHint,
  runAsk,
  loadingQuery,
  demoQuestions,
  onUseDemo,
  difficultyStats,
}: Props) {
  const isComparison = (askResult as any)?.source === "graph_comparison";

  return (
    <>
      <section className="summary-strip">
        <div className="card mini-summary-card">
          <div className="mini-title">1-Hop Questions</div>
          <div className="mini-value">{difficultyStats["1-hop"]}</div>
        </div>
        <div className="card mini-summary-card">
          <div className="mini-title">2-Hop Questions</div>
          <div className="mini-value">{difficultyStats["2-hop"]}</div>
        </div>
        <div className="card mini-summary-card">
          <div className="mini-title">3-Hop Questions</div>
          <div className="mini-value">{difficultyStats["3-hop"]}</div>
        </div>
        <div className="card mini-summary-card">
          <div className="mini-title">Comparison</div>
          <div className="mini-value">{difficultyStats["comparison"]}</div>
        </div>
      </section>

      <section className="main-grid">
        <div className="left-column">
          <QueryPanel
            question={question}
            setQuestion={setQuestion}
            entityHint={entityHint}
            setEntityHint={setEntityHint}
            runAsk={runAsk}
            loadingQuery={loadingQuery}
            usedSeed={askResult?.retrieval?.used_seed}
          />

          {!isComparison ? (
            <>
              <AnswerCard title="Graph Answer" answer={askResult?.graph_answer ?? null} />
              <AnswerCard title="LLM Answer" answer={askResult?.llm_answer ?? null} />
            </>
          ) : (
            <div className="card summary-card">
    <div className="section-title">Comparison Result</div>

    {(askResult as any)?.llm_answer?.answer ? (
      <div className="summary-text" style={{ marginBottom: "10px" }}>
        <strong>LLM Response:</strong> {(askResult as any).llm_answer.answer}
      </div>
    ) : null}

    <div className="summary-text">
      {(askResult as any)?.answer || "No comparison answer found."}
    </div>

    <div className="summary-text" style={{ marginTop: "10px" }}>
      <strong>Left Value:</strong> {(askResult as any)?.left_value || "-"}
    </div>
    <div className="summary-text">
      <strong>Right Value:</strong> {(askResult as any)?.right_value || "-"}
    </div>
  </div>
          )}

          <div className="card summary-card">
            <div className="section-title">Expanded Query</div>
            <div className="summary-text">
              {askResult?.query_expansion?.expanded_query || "Run a query to generate expanded query."}
            </div>
          </div>

          <div className="card summary-card">
            <div className="section-title">KG Summary</div>
            <div className="summary-text">
              {askResult?.retrieval?.kg_summary || "Run a query to generate KG summary."}
            </div>
          </div>

          <div className="card chart-card">
            <div className="section-title">Relation Distribution</div>
            <div className="chart-container">
              <ResponsiveContainer width="100%" height={320}>
                <BarChart data={relationChartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#23304f" />
                  <XAxis dataKey="relation" tick={{ fill: "#c7d2fe", fontSize: 11 }} />
                  <YAxis tick={{ fill: "#c7d2fe", fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="freq" fill="#60a5fa" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="right-column">
          <div className="card results-card">
            <div className="section-title">Reasoning Paths</div>

            {!askResult ? (
              <div className="placeholder-text">
                Run a query to see spreading activation and top reasoning paths.
              </div>
            ) : isComparison ? (
              <div className="paths-list">
                {(askResult as any)?.left_path ? (
                  <PathCard path={(askResult as any).left_path} index={0} />
                ) : null}

                {(askResult as any)?.right_path ? (
                  <PathCard path={(askResult as any).right_path} index={1} />
                ) : null}

                {!((askResult as any)?.left_path || (askResult as any)?.right_path) ? (
                  <div className="placeholder-text">No comparison paths found.</div>
                ) : null}
              </div>
            ) : askResult?.retrieval?.paths?.length ? (
              <div className="paths-list">
                {askResult.retrieval.paths.map((path, idx) => (
                  <PathCard key={idx} path={path} index={idx} />
                ))}
              </div>
            ) : (
              <div className="placeholder-text">No paths found.</div>
            )}
          </div>
        </div>
      </section>

      <section className="card demo-section">
        <div className="section-title">Verified Demo Questions</div>
        <div className="demo-grid">
          {demoQuestions.map((item, idx) => (
            <DemoQuestionCard key={idx} item={item} onUse={onUseDemo} />
          ))}
        </div>
      </section>
    </>
  );
}