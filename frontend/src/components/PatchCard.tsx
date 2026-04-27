import type { PathItem } from "../types";

type Props = {
  path: PathItem;
  index: number;
};

export default function PathCard({ path, index }: Props) {
  return (
    <div className="card path-card">
      <div className="path-header">
        <span className="path-rank">Path #{index + 1}</span>
        <span className="path-score">Score: {path.score.toFixed(2)}</span>
      </div>

      <div className="triples-wrapper">
        {path.triples.map((triple, i) => (
          <div className="triple-row" key={i}>
            <div className="entity-pill subject">{triple.subject_name}</div>
            <div className="relation-pill">{triple.relation}</div>
            <div className="entity-pill object">{triple.object_name}</div>
          </div>
        ))}
      </div>
    </div>
  );
}