import React from 'react';
import { useNavigate } from 'react-router-dom';
import heroImg from './assets/hero_bg.png';

const Landing = () => {
  const navigate = useNavigate();

  return (
    <div className="landing-wrapper">
      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-overlay"></div>
        <img src={heroImg} alt="経済データビジュアライゼーション" className="hero-bg-img" />
        
        <div className="hero-content">
          <div className="badge animate-fade-in">AI駆動型 経済インテリジェンス</div>
          <h1 className="hero-title animate-slide-up">
            <span style={{ display: 'block', whiteSpace: 'nowrap' }}>グローバルな経済の潮流を、</span>
            <span className="text-gradient" style={{ display: 'block', whiteSpace: 'nowrap' }}>一瞬で把握する</span>
          </h1>
          <p className="hero-description animate-slide-up">
            高度な自動クローリング、プロフェッショナル級のAI要約。
            戦略的な意思決定のための、即応可能な洞察を提供します。
          </p>
          <div className="hero-actions animate-slide-up">
            <button className="primary-btn" onClick={() => navigate('/')}>
              最新レポートを見る →
            </button>
            <button className="secondary-btn" onClick={() => window.scrollTo({ top: window.innerHeight, behavior: 'smooth' })}>
              プロセスの詳細
            </button>
          </div>
        </div>
      </section>

      {/* Process Section */}
      <section className="process-section" id="process">
        <div className="section-header">
          <div className="subtitle">ワークフロー</div>
          <h2>インテリジェンス・パイプライン</h2>
        </div>

        <div className="process-grid">
          <div className="process-card">
            <div className="process-number">01</div>
            <h3>高度なクローリング</h3>
            <p>世界中の経済レポート、ランキング、深層Webソースを毎日スキャンします。</p>
          </div>
          <div className="process-card highlight">
            <div className="process-number">02</div>
            <h3>AIによる統合・要約</h3>
            <p>断片的なPDFやデータを、Google NotebookLMを通じて文脈豊かなブリーフィング・ドキュメントに変換します。</p>
          </div>
          <div className="process-card">
            <div className="process-number">03</div>
            <h3>日々の洞察</h3>
            <p>優先順位付けされたインテリジェンスを、意思決定に直結するダッシュボードで提供します。</p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <div className="footer-content">
          <p>© 2026 Daily Keizai Intelligence. Powered by Advanced Agentic AI.</p>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
