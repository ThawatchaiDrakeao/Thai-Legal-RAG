import { StrictMode, useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

function formatPage(pageNumber) {
  return pageNumber == null ? "ไม่ระบุเลขหน้า" : `หน้า ${pageNumber}`;
}

function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function askQuestion(event) {
    event.preventDefault();
    const trimmedQuestion = question.trim();
    if (!trimmedQuestion || loading) return;

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const response = await fetch(`${API_URL}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmedQuestion }),
      });
      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "ระบบไม่สามารถตอบคำถามได้");
      }
      setResult(payload);
    } catch (requestError) {
      setError(requestError.message || "เชื่อมต่อ backend ไม่สำเร็จ");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="/" aria-label="Thai Legal RAG home">
          <span className="brand-mark">§</span>
          <span>
            <strong>Thai Legal RAG</strong>
            <small>Evidence-first legal research</small>
          </span>
        </a>
        <span className="status-pill"><span className="status-dot" /> Demo workspace</span>
      </header>

      <main className="main-content">
        <section className="hero">
          <div className="eyebrow">THAI LEGAL KNOWLEDGE BASE</div>
          <h1>ค้นหาคำตอบกฎหมาย<br /><em>จากเอกสารที่ตรวจสอบได้</em></h1>
          <p className="hero-copy">
            ถามคำถามเป็นภาษาไทย แล้วให้ระบบค้นหามาตราที่เกี่ยวข้องพร้อมแสดงแหล่งอ้างอิงอย่างโปร่งใส
          </p>
        </section>

        <section className="workspace-card" aria-label="Legal question workspace">
          <form onSubmit={askQuestion} className="ask-form">
            <label htmlFor="question">คำถามของคุณ</label>
            <div className="input-row">
              <textarea
                id="question"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                placeholder="เช่น มาตรา 1 กล่าวถึงอะไร"
                rows="3"
                maxLength="2000"
                disabled={loading}
              />
              <button type="submit" disabled={loading || !question.trim()}>
                {loading ? <span className="spinner" aria-label="กำลังค้นหา" /> : <span className="arrow">↗</span>}
                <span>{loading ? "กำลังค้นหา" : "ถามระบบ"}</span>
              </button>
            </div>
            <div className="form-meta"><span>รองรับคำถามภาษาไทย</span><span>{question.length}/2,000</span></div>
          </form>

          {error && <div className="alert error-alert" role="alert"><span>!</span>{error}</div>}

          {result && (
            <div className="result-area">
              {!result.found_context && (
                <div className="alert warning-alert" role="status">
                  <span>!</span>ไม่พบข้อมูลที่เกี่ยวข้องในเอกสาร
                </div>
              )}
              <section className="answer-section">
                <div className="section-heading"><span className="section-icon">✦</span><h2>คำตอบ</h2></div>
                <div className="answer-box">{result.answer}</div>
              </section>

              <section className="sources-section">
                <div className="section-heading">
                  <span className="section-icon source-icon">⌁</span>
                  <div><h2>แหล่งที่มา</h2><p>เอกสารที่ระบบใช้ประกอบคำตอบ</p></div>
                </div>
                <div className="sources-list">
                  {result.sources.length === 0 ? (
                    <div className="empty-sources">ไม่พบแหล่งอ้างอิง</div>
                  ) : result.sources.map((source, index) => (
                    <article className="source-card" key={`${source.source_file}-${source.page_number}-${index}`}>
                      <div className="source-index">{String(index + 1).padStart(2, "0")}</div>
                      <div className="source-body">
                        <div className="source-title"><strong>{source.source_file}</strong><span className="score">ความเกี่ยวข้อง {(source.score * 100).toFixed(1)}%</span></div>
                        <div className="source-meta"><span>{formatPage(source.page_number)}</span><span className="source-divider">•</span><span>คะแนน {source.score.toFixed(3)}</span></div>
                        <p>{source.text}</p>
                      </div>
                    </article>
                  ))}
                </div>
              </section>
            </div>
          )}

          {!result && !loading && !error && (
            <div className="empty-state"><div className="empty-icon">⌕</div><h2>เริ่มต้นค้นคว้า</h2><p>คำตอบจะปรากฏที่นี่ พร้อมเอกสารอ้างอิงที่เกี่ยวข้อง</p></div>
          )}
        </section>
      </main>

      <footer className="footer">ระบบต้นแบบเพื่อการศึกษา ไม่ใช่คำปรึกษากฎหมายจากทนายความ</footer>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<StrictMode><App /></StrictMode>);
