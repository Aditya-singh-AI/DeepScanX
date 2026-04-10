import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Shield, Users, BarChart3, Activity, Trash2, UserCog } from 'lucide-react';
import api from '../api/axios';

export default function AdminDashboard() {
  const [stats, setStats] = useState({ total_users: 0, total_predictions: 0, recent_users: [] });
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState('overview');

  useEffect(() => {
    Promise.all([
      api.get('/admin/api/stats'),
      api.get('/admin/api/users'),
    ]).then(([sRes, uRes]) => {
      setStats(sRes.data);
      setUsers(uRes.data.users || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  const handleDeleteUser = async (id) => {
    if (!window.confirm('Delete this user? This action cannot be undone.')) return;
    try {
      await api.delete(`/admin/api/users/${id}`);
      setUsers(prev => prev.filter(u => u._id !== id));
    } catch {}
  };

  const handleToggleRole = async (id, currentRole) => {
    const newRole = currentRole === 'admin' ? 'user' : 'admin';
    try {
      await api.patch(`/admin/api/users/${id}`, { role: newRole });
      setUsers(prev => prev.map(u => u._id === id ? { ...u, role: newRole } : u));
    } catch {}
  };

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge" style={{ background: 'rgba(255,211,42,.08)', borderColor: 'rgba(255,211,42,.3)', color: '#ffd32a' }}>
          <span className="pulse" style={{ background: '#ffd32a' }}></span> Admin Panel
        </div>
        <h1><span className="accent">Admin</span> Dashboard</h1>
        <p>Platform management and user administration</p>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '.5rem', marginBottom: '2rem' }}>
        {['overview', 'users'].map(t => (
          <button key={t} onClick={() => setTab(t)} style={{
            padding: '.6rem 1.5rem', borderRadius: '50px', border: '1px solid',
            borderColor: tab === t ? 'var(--crimson)' : 'var(--border2)',
            background: tab === t ? 'rgba(220,20,60,.1)' : 'transparent',
            color: tab === t ? 'var(--crimson-l)' : 'var(--gray)',
            cursor: 'pointer', fontSize: '.9rem', fontFamily: 'var(--font)',
            transition: 'all .3s',
          }}>{t === 'overview' ? 'Overview' : 'Users'}
          </button>
        ))}
      </div>

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Loading admin data...</div>
      ) : tab === 'overview' ? (
        <>
          {/* Stats Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
            {[
              { icon: <Users size={24} />, label: 'Total Users', value: stats.total_users, color: '#6c63ff' },
              { icon: <BarChart3 size={24} />, label: 'Total Predictions', value: stats.total_predictions, color: 'var(--crimson)' },
              { icon: <Activity size={24} />, label: 'Active Today', value: stats.active_today || '—', color: '#55efc4' },
            ].map((s, i) => (
              <div key={i} style={{
                background: 'var(--surface)', border: '1px solid var(--border)',
                borderRadius: 'var(--radius)', padding: '1.5rem',
                transition: 'all .3s',
              }}>
                <div style={{ color: s.color, marginBottom: '.8rem' }}>{s.icon}</div>
                <p style={{ fontFamily: 'var(--font2)', fontSize: '2rem', fontWeight: 700, color: 'var(--white)' }}>{s.value}</p>
                <p style={{ fontSize: '.85rem', color: 'var(--gray)' }}>{s.label}</p>
              </div>
            ))}
          </div>

          {/* Recent Users */}
          <div className="upload-card">
            <h3><Users size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> Recent Users</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '.5rem', marginTop: '1rem' }}>
              {(stats.recent_users || users.slice(0, 5)).map((u, i) => (
                <div key={i} style={{
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                  padding: '.8rem', background: 'rgba(255,255,255,.03)',
                  borderRadius: '8px', border: '1px solid var(--border2)',
                }}>
                  <div>
                    <p style={{ fontWeight: 500, color: 'var(--white)', fontSize: '.9rem' }}>{u.name || 'Unknown'}</p>
                    <p style={{ fontSize: '.8rem', color: 'var(--gray)' }}>{u.email}</p>
                  </div>
                  <span style={{
                    padding: '.2rem .8rem', borderRadius: '50px', fontSize: '.75rem',
                    background: u.role === 'admin' ? 'rgba(255,211,42,.15)' : 'rgba(255,255,255,.05)',
                    color: u.role === 'admin' ? '#ffd32a' : 'var(--gray)',
                    border: `1px solid ${u.role === 'admin' ? 'rgba(255,211,42,.3)' : 'var(--border2)'}`,
                  }}>{u.role || 'user'}</span>
                </div>
              ))}
            </div>
          </div>
        </>
      ) : (
        /* Users Tab */
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {users.map(u => (
            <div key={u._id} className="result-card" style={{ animation: 'none', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem' }}>
              <div>
                <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--white)' }}>{u.name || 'Unknown'}</h4>
                <p style={{ fontSize: '.85rem', color: 'var(--gray)' }}>{u.email}</p>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '.8rem' }}>
                <span style={{
                  padding: '.3rem .8rem', borderRadius: '50px', fontSize: '.8rem',
                  background: u.role === 'admin' ? 'rgba(255,211,42,.15)' : 'rgba(255,255,255,.05)',
                  color: u.role === 'admin' ? '#ffd32a' : 'var(--gray)',
                }}>{u.role || 'user'}</span>
                <button onClick={() => handleToggleRole(u._id, u.role)} style={{
                  background: 'rgba(108,99,255,.1)', border: '1px solid rgba(108,99,255,.2)',
                  borderRadius: '8px', padding: '.4rem .8rem', cursor: 'pointer',
                  color: '#a78bfa', fontSize: '.8rem', fontFamily: 'var(--font)',
                }}>
                  <UserCog size={14} style={{ marginRight: '.3rem', verticalAlign: 'middle' }} />
                  Toggle Role
                </button>
                <button onClick={() => handleDeleteUser(u._id)} style={{
                  background: 'rgba(231,76,60,.1)', border: '1px solid rgba(231,76,60,.2)',
                  borderRadius: '8px', padding: '.4rem', cursor: 'pointer', color: '#ff7675',
                }}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
