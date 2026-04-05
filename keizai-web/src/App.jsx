import React, { useState, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import reportsData from './data/reports.json';
import Landing from './Landing';

const App = () => {
  const [view, setView] = useState('landing');
  const [selectedDate, setSelectedDate] = useState(reportsData.dates[0]);
  const [selectedReport, setSelectedReport] = useState(null);
  const [markdownContent, setMarkdownContent] = useState('');

  const filteredReports = reportsData.reports.filter(r => r.date === selectedDate);

  useEffect(() => {
    if (selectedReport) {
      // Fetch the summary markdown
      const path = selectedReport.summary_file ? 
        `/reports/${selectedDate}/Rank${selectedReport.rank}_Summary_Briefing.md` : 
        `/reports/${selectedDate}/${selectedReport.source_file.split('/').pop()}`;
      
      fetch(path)
        .then(res => res.text())
        .then(text => setMarkdownContent(text))
        .catch(err => setMarkdownContent("Failed to load content."));
    }
  }, [selectedReport, selectedDate]);

  if (view === 'landing') {
    return <Landing onEnter={() => setView('dashboard')} />;
  }

  return (
    <div className="dashboard-container">
      {/* Sidebar: Archive Stack */}
      <aside className="archive-sidebar">
        <div className="subtitle">アーカイブ</div>
        <h2 style={{ marginBottom: '1.5rem', fontFamily: 'var(--font-serif)', color: 'var(--accent-gold)' }}>タイムライン</h2>
        {reportsData.dates.map(date => (
          <div 
            key={date} 
            className={`date-stack-item ${selectedDate === date ? 'active' : ''}`}
            onClick={() => setSelectedDate(date)}
            style={{
              padding: '1rem',
              marginBottom: '0.5rem',
              borderRadius: '8px',
              background: selectedDate === date ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
              cursor: 'pointer',
              border: selectedDate === date ? '1px solid var(--accent-orange)' : '1px solid transparent',
              transition: 'all 0.2s ease'
            }}
          >
            {date.substring(0,4)} / {date.substring(4,6)} / {date.substring(6,8)}
          </div>
        ))}
      </aside>

      {/* Main Content: Report Grid */}
      <main className="main-content">
        <header>
          <div className="subtitle">経済インテリジェンス</div>
          <h1>{selectedDate.substring(0,4)}.{selectedDate.substring(4,6)}.{selectedDate.substring(6,8)} レポート</h1>
        </header>

        <div className="report-grid">
          {filteredReports.map(report => (
            <div 
              key={`${report.date}-${report.rank}`} 
              className="report-card"
              onClick={() => setSelectedReport(report)}
            >
              <div className="rank-badge">ランク {report.rank}</div>
              <h3 className="report-title">{report.title}</h3>
              <div className="report-footer">
                <span className="status-tag" style={{ color: report.status === 'completed' ? '#00ffa3' : '#ff9d00' }}>
                  ● {report.status === 'completed' ? '完了' : '処理中'}
                </span>
                <span>{report.date}</span>
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Detail Overlay: Glassmorphism Modal */}
      {selectedReport && (
        <div 
          className="detail-overlay"
          onClick={() => setSelectedReport(null)}
          style={{
            position: 'fixed',
            top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.85)',
            backdropFilter: 'blur(10px)',
            zIndex: 1000,
            display: 'flex',
            justifyContent: 'center',
            padding: '2rem',
            overflowY: 'auto'
          }}
        >
          <div 
            className="detail-panel"
            onClick={e => e.stopPropagation()}
            style={{
              background: 'var(--bg-surface)',
              border: '1px solid var(--glass-border)',
              borderRadius: '16px',
              padding: '3rem',
              maxWidth: '900px',
              width: '100%',
              height: 'fit-content',
              boxShadow: 'var(--glass-shadow)',
              position: 'relative'
            }}
          >
            <button 
              onClick={() => setSelectedReport(null)}
              style={{
                position: 'absolute', top: '1.5rem', right: '1.5rem',
                background: 'transparent', border: 'none', color: 'var(--text-secondary)',
                fontSize: '1.5rem', cursor: 'pointer'
              }}
            >✕</button>
            
            <div className="rank-badge">ランク {selectedReport.rank} • {selectedReport.status === 'completed' ? 'AI 要約' : '原文コンテンツ'}</div>
            <h2 className="report-title" style={{ fontSize: '2.5rem', marginBottom: '2rem' }}>{selectedReport.title}</h2>
            
            <div className="markdown-body">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {markdownContent}
              </ReactMarkdown>
            </div>

            <div style={{ marginTop: '3rem', borderTop: '1px solid var(--glass-border)', paddingTop: '2rem' }}>
              <a 
                href={selectedReport.source_url} 
                target="_blank" 
                rel="noreferrer"
                style={{ color: 'var(--accent-orange)', textDecoration: 'none', fontWeight: 'bold' }}
              >
                ソースを表示 →
              </a>
              
              <button 
                className="close-button-bottom"
                onClick={() => setSelectedReport(null)}
              >
                ダッシュボードに戻る
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
