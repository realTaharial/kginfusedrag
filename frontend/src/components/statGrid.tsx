type Props = {
  totalEntities: number | string;
  totalRelations: number | string;
  totalQuestions: number | string;
  topPaths: number | string;
};

function StatCard({
  title,
  value,
  subtitle,
}: {
  title: string;
  value: number | string;
  subtitle: string;
}) {
  return (
    <div className="card stat-card">
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-subtitle">{subtitle}</div>
    </div>
  );
}

export default function StatGrid({
  totalEntities,
  totalRelations,
  totalQuestions,
  topPaths,
}: Props) {
  return (
    <section className="stats-grid">
      <StatCard title="Entities" value={totalEntities} subtitle="Neo4j nodes" />
      <StatCard title="Relations" value={totalRelations} subtitle="Neo4j edges" />
      <StatCard title="Verified Questions" value={totalQuestions} subtitle="Loaded demo items" />
      <StatCard title="Top Paths" value={topPaths} subtitle="For current query" />
    </section>
  );
}