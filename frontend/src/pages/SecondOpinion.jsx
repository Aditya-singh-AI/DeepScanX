import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Send, Clock, CheckCircle, XCircle, ExternalLink } from 'lucide-react';
import api from '../api/axios';

export default function SecondOpinion() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ prediction_id: '', recipient_email: '', message: '' });
  const [sending, setSending] = useState(false);

  useEffect(() => {
    api.get('/opinions/api/requests').then(r => setRequests(r.data.requests || []))
      .catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleSend = async (e) => {
    e.preventDefault(); setSending(true);
    try {
      const res = await api.post('/opinions/api/request', form);
      setRequests(prev => [res.data.request, ...prev]);
      setShowForm(false);
      setForm({ prediction_id: '', recipient_email: '', message: '' });
    } catch {} finally { setSending(false); }
  };

  const statusIcon = (status) => {
    if (status === 'completed') return <CheckCircle size={16} style={{ color: '#55efc4' }} />;
    if (status === 'rejected') return <XCircle size={16} style={{ color: '#ff7675' }} />;
    return <Clock size={16} style={{ color: '#ffd32a' }} />;
  };

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> Collaboration Hub</div>
        <h1>Second <span className="accent">Opinions</span></h1>
        <p>Request and review peer opinions on AI diagnostic predictions</p>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem' }}>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          <Send size={16} /> <span>New Request</span>
        </button>
      </div>

      {showForm && (
        <div className="upload-card" style={{ marginBottom: '2rem' }}>
          <h3><Send size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> Request Second Opinion</h3>
          <form onSubmit={handleSend}>
            <div className="form-row">
              <div className="form-group">
                <label>Prediction ID *</label>
                <input type="text" required value={form.prediction_id} onChange={e => setForm({ ...form, prediction_id: e.target.value })} placeholder="From scan history" />
              </div>
              <div className="form-group">
                <label>Recipient Email *</label>
                <input type="text" required value={form.recipient_email} onChange={e => setForm({ ...form, recipient_email: e.target.value })} placeholder="colleague@hospital.com" />
              </div>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label>Message (optional)</label>
              <textarea rows={3} value={form.message} onChange={e => setForm({ ...form, message: e.target.value })} placeholder="Please review this scan result..." />
            </div>
            <button className="btn-analyze" type="submit" disabled={sending}>
              <Send size={18} /> {sending ? 'Sending...' : 'Send Request'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Loading requests...</div>
      ) : requests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <Send size={48} style={{ color: 'var(--gray3)', marginBottom: '1rem' }} />
          <p style={{ color: 'var(--gray)' }}>No second opinion requests yet.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {requests.map((r, i) => (
            <div key={i} className="result-card" style={{ animation: 'none' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '.8rem' }}>
                  {statusIcon(r.status)}
                  <div>
                    <p style={{ fontWeight: 500, color: 'var(--white)', fontSize: '.95rem' }}>
                      To: {r.recipient_email || 'Unknown'}
                    </p>
                    <p style={{ fontSize: '.8rem', color: 'var(--gray)' }}>{r.message || 'No message'}</p>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`status-badge ${r.status === 'completed' ? 'negative' : 'positive'}`} style={{ fontSize: '.8rem' }}>
                    {r.status || 'pending'}
                  </span>
                  {r.created_at && <p style={{ fontSize: '.7rem', color: 'var(--gray3)', marginTop: '.3rem' }}>{new Date(r.created_at).toLocaleDateString()}</p>}
                </div>
              </div>
              {r.review_token && (
                <div style={{ marginTop: '.8rem' }}>
                  <a href={`/review/${r.review_token}`} style={{ fontSize: '.8rem', color: 'var(--crimson-l)', display: 'inline-flex', alignItems: 'center', gap: '.3rem' }}>
                    <ExternalLink size={12} /> Review Link
                  </a>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
