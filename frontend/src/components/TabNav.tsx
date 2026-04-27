import type { TabKey } from "../types";

type Props = {
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;
};

export default function TabNav({ activeTab, setActiveTab }: Props) {
  return (
    <div className="tabs-row">
      <button
        className={activeTab === "knowledge" ? "tab-btn active" : "tab-btn"}
        onClick={() => setActiveTab("knowledge")}
      >
        Knowledge Graph
      </button>

      <button
        className={activeTab === "cypher" ? "tab-btn active" : "tab-btn"}
        onClick={() => setActiveTab("cypher")}
      >
        Cypher Queries
      </button>

      <button
        className={activeTab === "evaluation" ? "tab-btn active" : "tab-btn"}
        onClick={() => setActiveTab("evaluation")}
      >
        Evaluation
      </button>

      <button
        className={activeTab === "case_study" ? "tab-btn active" : "tab-btn"}
        onClick={() => setActiveTab("case_study")}
      >
        Case Studies
      </button>

      <button
        className={activeTab === "status" ? "tab-btn active" : "tab-btn"}
        onClick={() => setActiveTab("status")}
      >
        Project Status
      </button>
    </div>
  );
}