import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Clock, Trash2, FileText, Search } from 'lucide-react';
import api from '../api/axios';

export default function History() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    api.get('/api/v1/history').then(r => setRecords(r.data.predictions || []))
      .catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/v1/history/${id}`);
      setRecords(prev => prev.filter(r => r._id !== id));
    } catch {}
  };

  const filtered = records.filter(r =>
    r.module?.toLowerCase().includes(search.toLowerCase()) ||
    r.predicted_class?.toLowerCase().includes(search.toLowerCase()) ||
    r.filename?.toLowerCase().includes(search.toLowerCase())
  );

  const moduleColors = {
    lung_colon: '#dc143c', breast_cancer: '#e91e63', brain_tumor: '#9c27b0',
    skin_cancer: '#ff5722', chest_xray: '#2196f3', diabetic_retinopathy: '#4caf50',
  };

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> Prediction Archive</div>
        <h1>Scan <span className="accent">History</span></h1>
        <p>Browse and manage your diagnostic prediction history</p>
      </div>

      <div style={{ marginBottom: '2rem', position: 'relative' }}>
        <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--gray2)' }} />
        <input
          type="text" placeholder="Search by module, class, or filename..."
          value={search} onChange={(e) => setSearch(e.target.value)}
          style={{
            width: '100%', padding: '.8rem 1rem .8rem 2.8rem',
            background: 'rgba(255,255,255,.05)', border: '1px solid var(--border2)',
            borderRadius: '12px', color: 'var(--white)', fontSize: '.95rem',
            fontFamily: 'var(--font)', outline: 'none',
          }}
        />
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>
          <div className="spinner"></div>
          <p style={{ marginTop: '1rem' }}>Loading history...</p>
        </div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <Clock size={48} style={{ color: 'var(--gray3)', marginBottom: '1rem' }} />
          <p style={{ color: 'var(--gray)' }}>No predictions found. Start a scan to see results here.</p>
          <Link to="/" className="btn-primary" style={{ marginTop: '1.5rem', display: 'inline-flex' }}>
            <span>Go to Dashboard</span>
          </Link>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filtered.map((r) => (
            <div key={r._id} className="result-card" style={{ animation: 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{
                    width: '42px', height: '42px', borderRadius: '12px',
                    background: `${moduleColors[r.module] || 'var(--crimson)'}20`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    color: moduleColors[r.module] || 'var(--crimson)', fontSize: '1.1rem',
                  }}>
                    <FileText size={20} />
                  </div>
                  <div>
                    <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--white)', marginBottom: '.2rem' }}>
                      {r.module?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
                    </h4>
                    <p style={{ fontSize: '.85rem', color: 'var(--gray)' }}>{r.filename || 'Unknown file'}</p>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                  <div style={{ textAlign: 'right' }}>
                    <p style={{ fontSize: '.9rem', fontWeight: 500, color: 'var(--white)' }}>{r.predicted_class}</p>
                    <p style={{ fontSize: '.8rem', color: 'var(--gray2)' }}>
                      {r.confidence ? `${(parseFloat(r.confidence) * 100).toFixed(1)}%` : '—'}
                    </p>
                  </div>
                  <span className={`status-badge ${r.cancer_status?.toLowerCase().includes('malignant') || r.cancer_status?.toLowerCase().includes('positive') ? 'positive' : 'negative'}`}>
                    {r.cancer_status || 'N/A'}
                  </span>
                  <button onClick={() => handleDelete(r._id)} style={{
                    background: 'rgba(231,76,60,.1)', border: '1px solid rgba(231,76,60,.2)',
                    borderRadius: '8px', padding: '.4rem', cursor: 'pointer', color: '#ff7675',
                  }}>
                    <Trash2 size={16} />
                  </button>
                </div>
              </div>
              {r.timestamp && (
                <p style={{ fontSize: '.75rem', color: 'var(--gray3)', marginTop: '.8rem' }}>
                  <Clock size={12} style={{ marginRight: '.3rem', verticalAlign: 'middle' }} />
                  {new Date(r.timestamp).toLocaleString()}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
