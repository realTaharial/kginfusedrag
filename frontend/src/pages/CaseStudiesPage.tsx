export default function CaseStudiesPage() {
  const successfulCases = [
    {
      id: 1,
      title: "Successful 2-Hop",
      question: "Orhan Ovacıklı'ın oynadığı takımın ülkesi neresidir?",
      expected: "Türkiye",
      system: "Türkiye",
      pipeline:
        "Seed entity doğru şekilde Orhan Ovacıklı olarak bulundu. İlk roundda 'member of sports team' ilişkileri seçildi. İkinci roundda takım düğümünden 'country' ilişkisi izlenerek Türkiye cevabına ulaşıldı.",
      analysis:
        "Bu örnek kısa ve temiz bir 2-hop path içerdiği için retrieval stabil çalıştı. Entity linking güçlüydü ve path filtering doğru sonucu korudu.",
      recommendation:
        "Bu tip kısa, net path'ler baseline success örneği olarak sunulabilir.",
    },
    {
      id: 2,
      title: "Successful 2-Hop",
      question: "Av mevsimi filminin yönetmeninin doğum yeri neresidir?",
      expected: "Hakkâri",
      system: "Hakkâri",
      pipeline:
        "Seed entity film olarak bulundu. İlk hopta 'director', ikinci hopta 'place of birth' ilişkisi seçildi. Yönetmen düğümü üzerinden doğum yerine gidildi.",
      analysis:
        "Director tabanlı sorularda first-hop yönlendirmesi retrieval kalitesini artırdı. Yanlış kenarlara sapmadan doğru relation zinciri izlendi.",
      recommendation:
        "Film tabanlı sorularda first-hop relation guidance korunmalı.",
    },
    {
      id: 3,
      title: "Successful 3-Hop",
      question: "The Deathless Devil filminin yönetmeninin doğduğu yerin bağlı olduğu bölge neresidir?",
      expected: "Greater Istanbul",
      system: "Greater Istanbul",
      pipeline:
        "Film seed'i bulundu. 'director' -> 'place of birth' -> 'located in the administrative territorial entity' zinciri izlendi ve Greater Istanbul cevabı elde edildi.",
      analysis:
        "Bu örnek 3-hop reasoning'in Neo4j üzerinde doğru şekilde çalıştığını gösteriyor. Manuel Cypher doğrulaması ile sistem cevabı uyuştu.",
      recommendation:
        "3-hop sorular başarılı örnek olarak sunulmalı; özellikle region/country zincirleri case study için uygun.",
    },
    {
      id: 4,
      title: "Successful 3-Hop",
      question: "Kolpaçino: Bir Şehir Efsanesi filminin yönetmeninin doğduğu yerin ülkesi neresidir?",
      expected: "Türkiye",
      system: "Türkiye",
      pipeline:
        "Film seed'i bulundu. 'director' -> 'place of birth' -> 'country' path'i seçildi. Path ranking içinde doğru triple zinciri yüksek skor aldı.",
      analysis:
        "Başlangıçta film adındaki 'şehir' kelimesi relation filtering'i bozuyordu. Kural daraltıldıktan sonra sistem doğru relation set'i kullandı ve soru başarıyla çözüldü.",
      recommendation:
        "Question-text tabanlı relation çıkarımı yerine pattern tabanlı relation mapping tercih edilmeli.",
    },
    {
      id: 5,
      title: "Successful Comparison",
      question: "Serkan Gölge ve Türkan Akyol aynı ülkedeki üniversitelerde mi okudu?",
      expected: "Evet",
      system: "Evet",
      pipeline:
        "İki seed ayrı ayrı bulundu. Her iki tarafta da 'educated at' -> 'country' path'i çıkarıldı. Sol ve sağ son değerler 'Türkiye' olduğu için comparison sonucu 'Evet' üretildi.",
      analysis:
        "Comparison modülü iki ayrı retrieval sonucu karşılaştırarak doğru karar verdi. Sol ve sağ reasoning path'lerin ayrı tutulması hata ayıklamayı kolaylaştırdı.",
      recommendation:
        "Comparison sorularında left/right path ve final value mutlaka UI'da ayrı gösterilmeli.",
    },
  ];

  const failureCases = [
    {
      id: 6,
      title: "Failure — KG Data Deficiency",
      question: "Arda Güler'in current market value nedir?",
      expected: "KG'de yok",
      system: "No answer / fallback",
      pipeline:
        "Entity bulunabiliyor ancak Wikidata5M Türkiye subset'inde market value bilgisi bulunmuyor. Path tamamlanamadığı için graph answer üretilemedi.",
      analysis:
        "Bu doğrudan KG Data Deficiency örneği. Sistem doğru entity'yi bulsa bile gerekli relation graph içinde yer almıyor.",
      recommendation:
        "Eksik relation'lar raporlanmalı ve dış corpus fallback ile desteklenmeli.",
    },
    {
      id: 7,
      title: "Failure — Entity Linking Error",
      question: "The Deathless Devil ...",
      expected: "Film entity'si",
      system: "Başta yanlış entity / description match",
      pipeline:
        "İlk sürümde description tabanlı candidate matching nedeniyle alakasız entity adayları öne çıkabildi. Seed seçimi hatalı olunca doğru path oluşmadı.",
      analysis:
        "Bu durum entity linking precision problemini gösteriyor. Özellikle film isimlerinde description match gürültü üretti.",
      recommendation:
        "Name-first matching, stronger exact match scoring ve description ağırlığını düşürmek gerekli.",
    },
    {
      id: 8,
      title: "Failure — Turkish-English Mismatch",
      question: "Türkçe isimli bazı entity soruları",
      expected: "Doğru entity eşleşmesi",
      system: "Bazı örneklerde eşleşme yok / düşük skor",
      pipeline:
        "Türkçe soru metni ile KG'deki İngilizce veya farklı yazımlı entity adları her zaman birebir örtüşmedi. Alias kapsamı yetersiz olduğunda seed bulunamadı.",
      analysis:
        "Bu, Turkish-English mismatch kategorisine giriyor. Özellikle transliteration ve farklı adlandırmalar sorun çıkarıyor.",
      recommendation:
        "Alias dosyasını genişletmek, Türkçe-İngilizce eşanlamlı varyasyonları eklemek ve normalizasyonu güçlendirmek gerekir.",
    },
    {
      id: 9,
      title: "Failure — Retrieval Error",
      question: "Director tabanlı bazı 3-hop sorular",
      expected: "Director üzerinden path",
      system: "İlgisiz relation'lara sapma",
      pipeline:
        "İlk retrieval sürümünde sistem seed film düğümünden 'cast member', 'narrative location' gibi alakasız kenarlara gidebiliyordu. Doğru 'director' first-hop relation'ı her zaman önceliklenmiyordu.",
      analysis:
        "Bu açık bir retrieval error örneği. Doğru bilgi graph'ta bulunmasına rağmen traversal yanlış kenarları takip etti.",
      recommendation:
        "Pattern'e göre first-hop relation guidance uygulanmalı.",
    },
    {
      id: 10,
      title: "Failure — LLM Selection / Surface Realization Error",
      question: "Graph cevabı doğru, LLM cevabı bozuk",
      expected: "Kısa ve doğru doğal dil cevabı",
      system: "Anlamsız / bozulmuş Ollama çıktısı",
      pipeline:
        "Graph answer doğru şekilde çıkarıldı ancak küçük local model (1.5B) bazı prompt'larda graph bilgisini düzgün yüzeyselleştiremedi ve anlamsız cümle üretti.",
      analysis:
        "Bu doğrudan LLM surface-generation hatasıdır. Reasoning graph'te doğru olsa bile model son cevapta kalite düşürebilir.",
      recommendation:
        "Prompt daha dar tutulmalı, temperature düşürülmeli, gerekirse 3B model veya template-based fallback kullanılmalı.",
    },
  ];

  const allCases = [...successfulCases, ...failureCases];

  return (
    <section className="case-page">
      <div className="stats-grid">
        <div className="card stat-card">
          <div className="stat-title">Case Studies</div>
          <div className="stat-value">10</div>
          <div className="stat-subtitle">5 successful + 5 unsuccessful</div>
        </div>

        <div className="card stat-card">
          <div className="stat-title">Successful Cases</div>
          <div className="stat-value">5</div>
          <div className="stat-subtitle">Verified graph reasoning examples</div>
        </div>

        <div className="card stat-card">
          <div className="stat-title">Failure Categories</div>
          <div className="stat-value">5</div>
          <div className="stat-subtitle">KG gap, EL, mismatch, retrieval, LLM</div>
        </div>

        <div className="card stat-card">
          <div className="stat-title">Dominant Error</div>
          <div className="stat-value">Retrieval</div>
          <div className="stat-subtitle">Wrong edge expansion / missing guidance</div>
        </div>
      </div>

      {allCases.map((item) => {
        const success = item.id <= 5;

        return (
          <div key={item.id} className="card case-card">
            <div className="case-top">
              <div className="section-title no-margin">
                Case Study #{item.id} — {item.title}
              </div>
              <span className={`source-badge ${success ? "graph" : "fallback"}`}>
                {success ? "SUCCESS" : "FAILURE"}
              </span>
            </div>

            <div className="case-row">
              <strong>Question:</strong> {item.question}
            </div>

            <div className="case-row">
              <strong>Expected Answer:</strong> {item.expected}
            </div>

            <div className="case-row">
              <strong>System Answer:</strong> {item.system}
            </div>

            <div className="case-row">
              <strong>Pipeline Analysis:</strong> {item.pipeline}
            </div>

            <div className="case-row">
              <strong>Analysis:</strong> {item.analysis}
            </div>

            <div className="case-row">
              <strong>Recommendations:</strong> {item.recommendation}
            </div>
          </div>
        );
      })}
    </section>
  );
}