import { useState, useRef } from 'react';
import { Upload, ZoomIn, Crosshair, Brain } from 'lucide-react';
import api, { API_BASE } from '../api/axios';

export default function WSIViewer() {
  const [file, setFile] = useState(null);
  const [dziUrl, setDziUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [patchResult, setPatchResult] = useState(null);
  const fileRef = useRef(null);

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true); setError('');
    const fd = new FormData();
    fd.append('wsi_file', file);
    try {
      const res = await api.post('/app11/upload', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      setDziUrl(res.data.dzi_url);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to process whole slide image.');
    } finally { setLoading(false); }
  };

  const handlePatchAnalysis = async (x, y) => {
    try {
      const res = await api.post('/app11/analyze_patch', { filename: file.name, x, y, patch_size: 224 });
      setPatchResult(res.data);
    } catch {
      setError('Patch analysis failed.');
    }
  };

  return (
    <div className="content">
      <div className="module-header">
        <div className="module-badge"><span className="pulse"></span> Digital Pathology Module</div>
        <h1>WSI <span className="accent">Viewer</span></h1>
        <p>Upload whole slide images for high-resolution viewing with AI-powered patch analysis</p>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(231,76,60,.1)', border: '1px solid rgba(231,76,60,.3)', borderRadius: '12px', marginBottom: '1.5rem' }}>
          <p style={{ color: '#ff7675', fontSize: '.9rem' }}>{error}</p>
        </div>
      )}

      {!dziUrl ? (
        <div className="upload-card">
          <h3><ZoomIn size={20} style={{ color: 'var(--crimson)', marginRight: '.5rem' }} /> Upload Whole Slide Image</h3>
          <div className="upload-zone" onClick={() => fileRef.current?.click()}>
            <Upload size={48} style={{ color: 'var(--crimson)', marginBottom: '1rem' }} />
            <p>Drag & drop your WSI here, or <strong style={{ color: 'var(--crimson)' }}>click to browse</strong></p>
            <p className="formats">Supports: SVS, TIFF, NDPI, PNG, JPG</p>
            {file && <p style={{ color: 'var(--crimson-l)', marginTop: '.5rem', fontWeight: 500 }}>{file.name}</p>}
          </div>
          <input type="file" ref={fileRef} accept=".svs,.tiff,.tif,.ndpi,.png,.jpg,.jpeg" style={{ display: 'none' }}
            onChange={(e) => e.target.files[0] && setFile(e.target.files[0])} />
          <button className="btn-analyze" disabled={!file || loading} onClick={handleUpload}>
            <Brain size={18} />
            {loading ? 'Processing WSI...' : 'Process & View'}
          </button>
        </div>
      ) : (
        <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3 style={{ color: 'var(--white)' }}>
              <ZoomIn size={20} style={{ marginRight: '.5rem', verticalAlign: 'middle' }} /> Whole Slide Viewer
            </h3>
            <button className="btn-download secondary" onClick={() => { setDziUrl(null); setFile(null); setPatchResult(null); }}>
              Upload New Image
            </button>
          </div>
          <div style={{
            width: '100%', height: '600px', background: '#000',
            borderRadius: '12px', border: '1px solid var(--border2)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'var(--gray)', position: 'relative', overflow: 'hidden',
          }}>
            <div style={{ textAlign: 'center' }}>
              <Crosshair size={48} style={{ color: 'var(--crimson)', marginBottom: '1rem' }} />
              <p>OpenSeadragon viewer loads here</p>
              <p style={{ fontSize: '.8rem', color: 'var(--gray2)', marginTop: '.5rem' }}>Click any region to run AI analysis on that patch</p>
            </div>
          </div>
          {patchResult && (
            <div className="result-card" style={{ marginTop: '1.5rem' }}>
              <h4 style={{ color: 'var(--white)', marginBottom: '.5rem' }}>Patch Analysis Result</h4>
              <p style={{ color: 'var(--gray)' }}>Prediction: <strong style={{ color: 'var(--white)' }}>{patchResult.predicted_class}</strong></p>
              <p style={{ color: 'var(--gray)' }}>Confidence: <strong style={{ color: 'var(--white)' }}>{(patchResult.confidence * 100).toFixed(1)}%</strong></p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
