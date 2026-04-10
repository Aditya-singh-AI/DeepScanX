import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/axios';
import './Login.css';

export default function VerifyEmail() {
  const navigate = useNavigate();
  const [otp, setOtp] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault(); setError(''); setLoading(true);
    try {
      await api.post('/app2/verify-otp', new URLSearchParams({ otp }), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      });
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid OTP. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <div className="login-page" style={{ background: '#030305' }}>
      <div className="login-wrapper">
        <div className="login-container">
          <div className="login-logo-text">Verify Email</div>
          <div className="login-subtitle">Enter the OTP sent to your email</div>
          {error && <div className="flash-messages"><p>{error}</p></div>}
          <form onSubmit={handleSubmit}>
            <div className="input-group">
              <input type="text" id="otp" required autoComplete="off" value={otp} onChange={e => setOtp(e.target.value)} />
              <label htmlFor="otp">Enter OTP</label>
            </div>
            <button type="submit" className="btn-submit" disabled={loading}>
              {loading ? 'Verifying...' : 'Verify Email'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
