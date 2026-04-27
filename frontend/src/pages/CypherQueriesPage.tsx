export default function CypherQueriesPage() {
  const cypherSamples = [
    {
      name: "Türkiye Root Entity",
      hop: "1-hop",
      query: `MATCH (e:Entity)
WHERE toLower(e.name) CONTAINS 'turkey'
   OR toLower(e.name) CONTAINS 'türkiye'
RETURN e.entityId AS id, e.name AS name
LIMIT 5`,
    },
    {
      name: "Turkish Cities Detection",
      hop: "2-hop",
      query: `MATCH (city:Entity)-[:RELATION {relation_name:'country'}]->(t:Entity {entityId:'Q43'})
RETURN city.entityId, city.name
LIMIT 20`,
    },
    {
      name: "Football Player -> Club",
      hop: "2-hop",
      query: `MATCH (player:Entity)-[:RELATION {relation_name:'member of sports team'}]->(club:Entity)
RETURN player.name, club.name
LIMIT 20`,
    },
    {
      name: "Film -> Director -> Birth Place",
      hop: "2-hop",
      query: `MATCH (film:Entity)-[:RELATION {relation_name:'director'}]->(d:Entity)-[:RELATION {relation_name:'place of birth'}]->(birth:Entity)
RETURN film.name, d.name, birth.name
LIMIT 20`,
    },
    {
      name: "Club -> Stadium -> City",
      hop: "3-hop",
      query: `MATCH (club:Entity)-[:RELATION {relation_name:'home venue'}]->(stadium:Entity)-[:RELATION]->(city:Entity)
RETURN club.name, stadium.name, city.name
LIMIT 20`,
    },
  ];

  return (
    <section className="two-col-page">
      <div className="left-column">
        <div className="card query-library-card">
          <div className="section-title">Query Library</div>
          <div className="library-list">
            {cypherSamples.map((item, idx) => (
              <div className="library-item" key={idx}>
                <div>
                  <div className="library-name">{item.name}</div>
                  <div className="library-hop">{item.hop}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="right-column">
        {cypherSamples.map((item, idx) => (
          <div className="card cypher-card" key={idx}>
            <div className="cypher-top">
              <div className="section-title no-margin">{item.name}</div>
              <span className="mini-tag">{item.hop}</span>
            </div>
            <pre className="code-block">{item.query}</pre>
          </div>
        ))}
      </div>
    </section>
  );
}