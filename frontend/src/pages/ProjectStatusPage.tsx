export default function ProjectStatusPage() {
  return (
    <section className="status-page">
      <div className="card status-card">
        <div className="section-title">Project Deliverable Status</div>
        <ul className="status-list">
          <li>✅ Türkiye entity analysis</li>
          <li>✅ Relation frequency analysis</li>
          <li>✅ Neo4j graph loading</li>
          <li>✅ Verified QA dataset generation</li>
          <li>✅ Spreading activation retrieval</li>
          <li>✅ Graph answer + LLM fallback UI</li>
          <li>🟡 Query expansion polishing</li>
          <li>🟡 4-method evaluation table with real scores</li>
          <li>🟡 5 success + 5 failure case studies</li>
          <li>🟡 Final report and presentation visuals</li>
        </ul>
      </div>

      <div className="card status-card">
        <div className="section-title">Missing vs Project PDF</div>
        <ul className="status-list">
          <li>Gerçek No-Retrieval / Vanilla RAG / Vanilla QE sonuçları</li>
          <li>Case study sayısını tamamlamak</li>
          <li>Question quality cleanup (duplicate / noisy paths)</li>
          <li>Cypher result preview and query execution page</li>
          <li>Final report tables/charts</li>
        </ul>
      </div>
    </section>
  );
}