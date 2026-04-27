import type { DemoQuestion } from "../types";

type Props = {
  item: DemoQuestion;
  onUse: (item: DemoQuestion) => void;
};

export default function DemoQuestionCard({ item, onUse }: Props) {
  return (
    <div className="card demo-card">
      <div className="demo-top">
        <div className="demo-id"></div>
        <div className="demo-tags">
          <span className="mini-tag">{item.domain}</span>
          <span className="mini-tag">{item.difficulty}</span>
        </div>
      </div>

      <div className="demo-question">{item.question_text}</div>
      <div className="demo-answer">Gold Answer: {item.gold_answer}</div>
      <div className="demo-path">{item.reasoning_path.join(" → ")}</div>

      <button className="neon-btn small-btn" onClick={() => onUse(item)}>
        Use This
      </button>
    </div>
  );
}