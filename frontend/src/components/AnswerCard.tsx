import type { GraphAnswer } from "../types";

function SourceBadge({ source }: { source?: string }) {
  if (!source) return null;

  const className =
    source === "graph_verified"
      ? "source-badge graph"
      : "source-badge fallback";

  const label =
    source === "graph_verified" ? "Graph Verified" : " ";

  return <span className={className}>{label}</span>;
}

type Props = {
  title: string;
  answer: GraphAnswer;
};

export default function AnswerCard({ title, answer }: Props) {
  if (!answer) return null;

  return (
    <div className="card answer-card">
      <div className="answer-top">
        <div className="section-title no-margin">{title}</div>
        <SourceBadge source={answer.source} />
      </div>
      <div className="final-answer">{answer.answer}</div>
      <div className="answer-reasoning">{answer.reasoning_summary}</div>
    </div>
  );
}