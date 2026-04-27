type Props = {
  question: string;
  setQuestion: (value: string) => void;
  entityHint: string;
  setEntityHint: (value: string) => void;
  runAsk: () => void;
  loadingQuery: boolean;
  usedSeed?: { entityId: string; name: string } | null;
};

export default function QueryPanel({
  question,
  setQuestion,
  entityHint,
  setEntityHint,
  runAsk,
  loadingQuery,
  usedSeed,
}: Props) {
  return (
    <div className="card query-card">
      <div className="section-title">Ask a Question</div>

      <label className="input-label">Question</label>
      <textarea
        className="text-input textarea-input"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />

      <label className="input-label">Entity Hint</label>
      <input
        className="text-input"
        value={entityHint}
        onChange={(e) => setEntityHint(e.target.value)}
      />

      <button className="neon-btn" onClick={runAsk} disabled={loadingQuery}>
        {loadingQuery ? "Running..." : "Run KG-Infused Query"}
      </button>

      {usedSeed ? (
        <div className="seed-box">
          <div className="seed-title">Used Seed</div>
          <div className="seed-value">
            {usedSeed.name} ({usedSeed.entityId})
          </div>
        </div>
      ) : null}
    </div>
  );
}