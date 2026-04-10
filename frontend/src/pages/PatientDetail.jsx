import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ArrowLeft, Calendar, FileText, Clock } from 'lucide-react';
import api from '../api/axios';

export default function PatientDetail() {
  const { id } = useParams();
  const [patient, setPatient] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/patients/api/react/${id}`),
      api.get(`/patients/api/react/${id}/timeline`),
    ]).then(([pRes, tRes]) => {
      setPatient(pRes.data.patient || pRes.data);
      setTimeline(tRes.data.timeline || []);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  if (loading) return <div className="content" style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Loading...</div>;
  if (!patient) return <div className="content" style={{ textAlign: 'center', padding: '4rem', color: 'var(--gray)' }}>Patient not found.</div>;

  return (
    <div className="content">
      <Link to="/patients" className="btn-back" style={{ marginBottom: '1.5rem', display: 'inline-flex' }}>
        <ArrowLeft size={16} /> Back to Patients
      </Link>

      <div className="result-card" style={{ animation: 'none' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', marginBottom: '2rem' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '50%',
            background: 'linear-gradient(135deg, var(--crimson), var(--crimson-d))',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: '#fff', fontWeight: 700, fontSize: '1.5rem',
          }}>{patient.name?.charAt(0)?.toUpperCase()}</div>
          <div>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--white)' }}>{patient.name}</h2>
            <p style={{ color: 'var(--gray)', fontSize: '.95rem' }}>
              {patient.age && `Age: ${patient.age}`}{patient.gender && ` · ${patient.gender}`}
              {patient.medical_record_number && ` · MRN: ${patient.medical_record_number}`}
            </p>
          </div>
        </div>

        {patient.notes && (
          <div style={{ background: 'rgba(255,255,255,.03)', border: '1px solid var(--border2)', borderRadius: '12px', padding: '1.2rem', marginBottom: '2rem' }}>
            <h4 style={{ color: 'var(--white)', marginBottom: '.5rem', fontSize: '.95rem' }}>Notes</h4>
            <p style={{ color: 'var(--gray)', fontSize: '.9rem', lineHeight: 1.7 }}>{patient.notes}</p>
          </div>
        )}
      </div>

      <h3 style={{ fontFamily: 'var(--font2)', fontSize: '1.3rem', fontWeight: 600, color: 'var(--white)', margin: '2rem 0 1rem' }}>
        <Calendar size={20} style={{ marginRight: '.5rem', verticalAlign: 'middle' }} /> Diagnostic Timeline
      </h3>

      {timeline.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--gray)' }}>
          <p>No diagnostic records yet for this patient.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '.8rem' }}>
          {timeline.map((t, i) => (
            <div key={i} className="result-card" style={{ animation: 'none', padding: '1.2rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '.8rem' }}>
                  <FileText size={18} style={{ color: 'var(--crimson)' }} />
                  <div>
                    <p style={{ fontWeight: 500, color: 'var(--white)', fontSize: '.95rem' }}>{t.module?.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                    <p style={{ fontSize: '.8rem', color: 'var(--gray)' }}>{t.predicted_class} · {t.filename}</p>
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <span className={`status-badge ${t.cancer_status?.toLowerCase().includes('malignant') ? 'positive' : 'negative'}`} style={{ fontSize: '.75rem' }}>
                    {t.cancer_status || 'N/A'}
                  </span>
                  {t.timestamp && <p style={{ fontSize: '.7rem', color: 'var(--gray3)', marginTop: '.3rem' }}><Clock size={10} /> {new Date(t.timestamp).toLocaleDateString()}</p>}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
