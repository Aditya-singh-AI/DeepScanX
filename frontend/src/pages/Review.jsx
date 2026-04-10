import { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { FileText, CheckCircle } from 'lucide-react';
import api from '../api/axios';

export default function Review() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [opinion, setOpinion] = useState('');
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    api.get(`/opinions/api/review/${token}`).then(r => setData(r.data))
      .catch(() => {}).finally(() => setLoading(false));
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.post(`/opinions/api/review/${token}`, { opinion });
      setSubmitted(true);
    } catch {}
  };

  if (loading) return <div className="content" style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Loading review...</div>;
  if (!data) return <div className="content" style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Review not found or expired.</div>;

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> Peer Review</div>
        <h1>Second Opinion <span className="accent">Review</span></h1>
        <p>Review the diagnostic prediction and provide your expert opinion</p>
      </div>

      <div className="result-card">
        <div className="result-header">
          <h2><FileText size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> {data.prediction?.filename || 'Diagnostic Result'}</h2>
          <span className={`status-badge ${data.prediction?.cancer_status?.toLowerCase().includes('malignant') ? 'positive' : 'negative'}`}>
            {data.prediction?.cancer_status || 'N/A'}
          </span>
        </div>
        <div style={{ background: 'rgba(255,255,255,.03)', border: '1px solid var(--border2)', borderRadius: '12px', padding: '1.2rem', margin: '1rem 0' }}>
          <p style={{ color: 'var(--gray)', fontSize: '.9rem' }}>
            <strong>Module:</strong> {data.prediction?.module?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
          </p>
          <p style={{ color: 'var(--gray)', fontSize: '.9rem' }}>
            <strong>Predicted Class:</strong> {data.prediction?.predicted_class}
          </p>
          <p style={{ color: 'var(--gray)', fontSize: '.9rem' }}>
            <strong>Confidence:</strong> {data.prediction?.confidence ? `${(parseFloat(data.prediction.confidence) * 100).toFixed(1)}%` : 'N/A'}
          </p>
        </div>
        {data.message && (
          <div className="explanation-box">
            <h4>Message from Requesting Physician</h4>
            <p>{data.message}</p>
          </div>
        )}
      </div>

      {submitted ? (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <CheckCircle size={48} style={{ color: '#55efc4', marginBottom: '1rem' }} />
          <h3 style={{ color: 'var(--white)', marginBottom: '.5rem' }}>Opinion Submitted</h3>
          <p style={{ color: 'var(--gray)' }}>Thank you for your expert review. The requesting physician has been notified.</p>
        </div>
      ) : (
        <div className="upload-card" style={{ marginTop: '2rem' }}>
          <h3>Your Expert Opinion</h3>
          <form onSubmit={handleSubmit}>
            <div className="notes-section">
              <textarea value={opinion} onChange={e => setOpinion(e.target.value)} rows={6}
                placeholder="Provide your clinical assessment, agreement/disagreement with the AI prediction, and any recommendations..." required />
            </div>
            <button className="btn-analyze" type="submit">
              <CheckCircle size={18} /> Submit Opinion
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
