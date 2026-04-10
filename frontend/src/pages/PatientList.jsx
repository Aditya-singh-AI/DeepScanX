import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Users, Plus, Search, Calendar, FileText, ChevronRight } from 'lucide-react';
import api from '../api/axios';

export default function PatientList() {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name: '', age: '', gender: 'Male', medical_record_number: '', notes: '' });
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.get('/patients/api/react')
      .then(r => setPatients(r.data.patients || []))
      .catch(e => {
        if (e.response?.status === 401) {
          alert('401 UNAUTHORIZED in PatientList GET: ' + (e.response?.data?.error || e.message));
        }
      })
      .finally(() => setLoading(false));
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault(); setSaving(true);
    try {
      const res = await api.post('/patients/api/react', form);
      setPatients(prev => [res.data.patient, ...prev]);
      setShowForm(false);
      setForm({ name: '', age: '', gender: 'Male', medical_record_number: '', notes: '' });
    } catch {} finally { setSaving(false); }
  };

  const filtered = patients.filter(p => p.name?.toLowerCase().includes(search.toLowerCase()) || p.medical_record_number?.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> Patient Registry</div>
        <h1>Patient <span className="accent">Management</span></h1>
        <p>Create and manage patient profiles for diagnostic tracking</p>
      </div>

      <div style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap' }}>
        <div style={{ flex: 1, position: 'relative', minWidth: '200px' }}>
          <Search size={18} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--gray2)' }} />
          <input type="text" placeholder="Search patients..." value={search} onChange={e => setSearch(e.target.value)}
            style={{ width: '100%', padding: '.8rem 1rem .8rem 2.8rem', background: 'rgba(255,255,255,.05)', border: '1px solid var(--border2)', borderRadius: '12px', color: 'var(--white)', fontSize: '.95rem', fontFamily: 'var(--font)', outline: 'none' }} />
        </div>
        <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
          <Plus size={16} /> <span>Add Patient</span>
        </button>
      </div>

      {showForm && (
        <div className="upload-card" style={{ marginBottom: '2rem' }}>
          <h3><Users size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> New Patient</h3>
          <form onSubmit={handleCreate}>
            <div className="form-row">
              <div className="form-group">
                <label>Full Name *</label>
                <input type="text" required value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
              </div>
              <div className="form-group">
                <label>Age</label>
                <input type="text" value={form.age} onChange={e => setForm({ ...form, age: e.target.value })} />
              </div>
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Gender</label>
                <select value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                  <option>Male</option><option>Female</option><option>Other</option>
                </select>
              </div>
              <div className="form-group">
                <label>Medical Record Number</label>
                <input type="text" value={form.medical_record_number} onChange={e => setForm({ ...form, medical_record_number: e.target.value })} />
              </div>
            </div>
            <div className="form-group" style={{ marginBottom: '1rem' }}>
              <label>Notes</label>
              <textarea rows={3} value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} />
            </div>
            <button className="btn-analyze" type="submit" disabled={saving}>
              <Plus size={18} /> {saving ? 'Creating...' : 'Create Patient'}
            </button>
          </form>
        </div>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Loading patients...</div>
      ) : filtered.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '4rem' }}>
          <Users size={48} style={{ color: 'var(--gray3)', marginBottom: '1rem' }} />
          <p style={{ color: 'var(--gray)' }}>No patients found. Add a patient to get started.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filtered.map(p => (
            <Link to={`/patients/${p._id}`} key={p._id} className="result-card" style={{ animation: 'none', textDecoration: 'none', color: 'inherit', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  width: '48px', height: '48px', borderRadius: '50%',
                  background: 'linear-gradient(135deg, var(--crimson), var(--crimson-d))',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#fff', fontWeight: 700, fontSize: '1.1rem',
                }}>{p.name?.charAt(0)?.toUpperCase()}</div>
                <div>
                  <h4 style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--white)' }}>{p.name}</h4>
                  <p style={{ fontSize: '.85rem', color: 'var(--gray)' }}>
                    {p.age && `Age: ${p.age}`}{p.gender && ` · ${p.gender}`}
                    {p.medical_record_number && ` · MRN: ${p.medical_record_number}`}
                  </p>
                </div>
              </div>
              <ChevronRight size={20} style={{ color: 'var(--gray2)' }} />
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
