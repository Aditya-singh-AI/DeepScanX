import { useState, useRef, useCallback, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Upload, Brain, AlertTriangle, FileText, RotateCcw, Download, Layers } from 'lucide-react';
import api, { API_BASE } from '../api/axios';

export default function ScannerPage({
  title, accent, badgeText, description, formats = '.jpg,.jpeg,.png,.bmp',
  endpoint, moduleIcon = 'fas fa-microscope',
  showEnsemble = false, showPatientLink = false,
  classLabels = [],
}) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dragover, setDragover] = useState(false);
  const [ensemble, setEnsemble] = useState(false);
  const [notes, setNotes] = useState('');
  const fileRef = useRef(null);

  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('none');

  useEffect(() => {
    if (showPatientLink) {
      api.get('/patients/api/react')
        .then(r => setPatients(r.data.patients || []))
        .catch(e => console.error('Failed to load patients for scanner link', e));
    }
  }, [showPatientLink]);

  const handleFile = useCallback((f) => {
    setFile(f);
    setResult(null);
    setError('');
    if (f) {
      const reader = new FileReader();
      reader.onload = (e) => setPreview(e.target.result);
      reader.readAsDataURL(f);
    }
  }, []);

  const onDrop = useCallback((e) => {
    e.preventDefault(); setDragover(false);
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true); setError('');
    const fd = new FormData();
    fd.append('images', file);
    if (ensemble) fd.append('ensemble', 'true');
    if (showPatientLink && selectedPatient !== 'none') {
      fd.append('patient_id', selectedPatient);
    }
    
    try {
      const res = await api.post(endpoint, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setResult(res.data);
    } catch (err) {
      const errMsg = err.response?.data?.error || 'Analysis failed. Please try again.';
      setError(errMsg);
      // Explicitly alert the user of what the backend says
      if (err.response?.status === 401) {
        alert("401 UNAUTHORIZED EXACT REASON: " + errMsg);
      }
    } finally { setLoading(false); }
  };

  const handleDownload = async () => {
    try {
      const downloadEndpoint = endpoint.replace(/\/predict$|\/upload$|\/$/, '') + '/download';
      const res = await api.post(downloadEndpoint, {
        ...result,
        doctor_notes: notes,
      }, { responseType: 'blob' });
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url; a.download = `${title.replace(/\s+/g, '_')}_Report.pdf`;
      a.click(); URL.revokeObjectURL(url);
    } catch {
      setError('Failed to download report.');
    }
  };

  const confidence = result ? parseFloat(result.confidence) : 0;
  const confPercent = (confidence * 100).toFixed(1);
  const isMalignant = result && (
    result.cancer_status?.toLowerCase().includes('malignant') ||
    result.cancer_status?.toLowerCase().includes('positive') ||
    result.cancer_status?.toLowerCase().includes('tumor')
  );

  return (
    <div className="content">
      {/* Header */}
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> {badgeText}</div>
        <h1>{title.split(' ').slice(0, -1).join(' ')} <span className="accent">{title.split(' ').pop()}</span></h1>
        <p>{description}</p>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(231,76,60,.1)', border: '1px solid rgba(231,76,60,.3)', borderRadius: '12px', marginBottom: '1.5rem' }}>
          <p style={{ color: '#ff7675', fontSize: '.9rem' }}>{error}</p>
        </div>
      )}

      {/* Upload */}
      {!result && (
        <div className="upload-card">
          <h3><i className={moduleIcon} style={{ color: 'var(--crimson)', marginRight: '.5rem' }}></i> Upload Image</h3>
          <div
            className={`upload-zone${dragover ? ' dragover' : ''}`}
            onClick={() => fileRef.current?.click()}
            onDragEnter={(e) => { e.preventDefault(); setDragover(true); }}
            onDragOver={(e) => { e.preventDefault(); setDragover(true); }}
            onDragLeave={(e) => { e.preventDefault(); setDragover(false); }}
            onDrop={onDrop}
          >
            {preview ? (
              <img src={preview} alt="Preview" style={{ maxHeight: '200px', borderRadius: '8px', marginBottom: '1rem' }} />
            ) : (
              <Upload size={48} style={{ color: 'var(--crimson)', marginBottom: '1rem' }} />
            )}
            <p>Drag & drop your image here, or <strong style={{ color: 'var(--crimson)' }}>click to browse</strong></p>
            <p className="formats">Supports: {formats.replace(/\./g, '').toUpperCase().replace(/,/g, ', ')}</p>
            {file && <p style={{ color: 'var(--crimson-l)', marginTop: '.5rem', fontWeight: 500 }}>{file.name}</p>}
          </div>
          <input type="file" ref={fileRef} accept={formats} style={{ display: 'none' }} onChange={(e) => e.target.files[0] && handleFile(e.target.files[0])} />

          {showEnsemble && (
            <div className="checkbox-row">
              <input type="checkbox" id="ensemble" checked={ensemble} onChange={(e) => setEnsemble(e.target.checked)} />
              <label htmlFor="ensemble">Enable Model Ensembling (ResNet + EfficientNet + DenseNet)</label>
            </div>
          )}

          {showPatientLink && (
            <div className="checkbox-row" style={{ marginTop: '1rem', flexDirection: 'column', alignItems: 'flex-start', gap: '0.5rem' }}>
              <label htmlFor="patient-select" style={{ color: 'var(--gray)', fontSize: '0.9rem', fontWeight: 500 }}>
                Link to Patient Record
              </label>
              <select
                id="patient-select"
                value={selectedPatient}
                onChange={(e) => setSelectedPatient(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.8rem 1rem',
                  background: 'rgba(255,255,255,.05)',
                  border: '1px solid var(--border2)',
                  borderRadius: '8px',
                  color: 'var(--white)',
                  fontSize: '0.95rem',
                  outline: 'none',
                  cursor: 'pointer'
                }}
              >
                <option value="none" style={{ color: '#000' }}>None (Anonymous Analysis)</option>
                {patients.map(p => (
                  <option key={p._id} value={p._id} style={{ color: '#000' }}>
                    {p.name} {p.medical_record_number ? `(${p.medical_record_number})` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <button className="btn-analyze" disabled={!file || loading} onClick={handleSubmit}>
            <Brain size={18} />
            {loading ? 'Analyzing...' : 'Analyze Image'}
          </button>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="results-section">
          <div className="result-card">
            <div className="result-header">
              <h2><FileText size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> {result.filename || file?.name}</h2>
              <span className={`status-badge ${isMalignant ? 'positive' : 'negative'}`}>
                {result.cancer_status || result.predicted_class}
              </span>
            </div>

            <div className="confidence-bar">
              <div className="label">Model Confidence</div>
              <div className="bar-track"><div className="bar-fill" style={{ width: `${confPercent}%` }}></div></div>
              <div className="confidence-value">{confPercent}%</div>
            </div>

            {result.low_confidence && (
              <div className="low-confidence-warning">
                <AlertTriangle size={18} />
                Low confidence prediction — results may be unreliable. Manual review recommended.
              </div>
            )}

            <div className="plots-grid">
              {result.results_plot && <img src={result.results_plot.startsWith('data:') ? result.results_plot : `${API_BASE}${result.results_plot}`} alt="Grad-CAM Analysis" />}
              {result.prob_plot && <img src={result.prob_plot.startsWith('data:') ? result.prob_plot : `${API_BASE}${result.prob_plot}`} alt="Probability Distribution" />}
            </div>

            {result.ensemble_results && (
              <div className="ensemble-box">
                <h4><Layers size={18} style={{ marginRight: '.5rem' }} /> Ensemble Model Results</h4>
                <div className="ensemble-badge">
                  ✓✓ Agreement: {(result.ensemble_results.agreement_ratio * 100).toFixed(0)}% ({result.ensemble_results.num_models} models)
                </div>
                <p style={{ color: 'var(--white)', marginBottom: '.5rem' }}>
                  <strong>Ensemble Prediction:</strong> {result.ensemble_results.ensemble_prediction} ({(result.ensemble_results.ensemble_confidence * 100).toFixed(1)}%)
                </p>
                {result.ensemble_results.individual?.map((r, i) => (
                  <div className="model-row" key={i}>
                    <span className="model-name">{r.model}</span>
                    <span className="model-pred">{r.predicted_class} ({(r.confidence * 100).toFixed(1)}%)</span>
                  </div>
                ))}
              </div>
            )}

            {result.explanation && (
              <div className="explanation-box">
                <h4><i className="fas fa-stethoscope" style={{ marginRight: '.5rem' }}></i> Clinical Interpretation</h4>
                <p>{result.explanation}</p>
              </div>
            )}

            {/* Probability table */}
            {result.probabilities && result.probabilities.length > 0 && (
              <div style={{ background: 'rgba(255,255,255,.03)', border: '1px solid var(--border2)', borderRadius: '12px', padding: '1.5rem', margin: '1.5rem 0' }}>
                <h4 style={{ color: 'var(--white)', marginBottom: '1rem' }}>Class Probabilities</h4>
                {result.probabilities.map(([cls, prob], i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '.4rem 0', borderBottom: i < result.probabilities.length - 1 ? '1px solid rgba(255,255,255,.05)' : 'none' }}>
                    <span style={{ color: 'var(--gray)', fontSize: '.9rem' }}>{cls}</span>
                    <span style={{ color: 'var(--white)', fontWeight: 500, fontSize: '.9rem' }}>{(parseFloat(prob) * 100).toFixed(2)}%</span>
                  </div>
                ))}
              </div>
            )}

            <div className="notes-section">
              <h4><i className="fas fa-pen-fancy" style={{ color: 'var(--crimson)', marginRight: '.5rem' }}></i> Physician's Notes</h4>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Add your clinical observations, differential diagnosis, or treatment recommendations here..." />
              <p className="hint">These notes will be included in the downloadable PDF report.</p>
            </div>

            <div className="download-section">
              <button className="btn-download primary" onClick={handleDownload}>
                <Download size={16} /> Download Detailed Report (PDF)
              </button>
              <button className="btn-download secondary" onClick={() => { setResult(null); setFile(null); setPreview(null); setNotes(''); }}>
                <RotateCcw size={16} /> Analyze Another Image
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
