import { useEffect, useRef } from 'react';
import { Auth } from '@supabase/auth-ui-react';
import { ThemeSupa } from '@supabase/auth-ui-shared';
import { supabase } from '../api/supabase';
import { useNavigate } from 'react-router-dom';
import { Activity } from 'lucide-react';
import './Login.css';

export default function Login() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const c = canvasRef.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    let raf;
    const resize = () => { c.width = window.innerWidth; c.height = window.innerHeight; };
    resize();
    window.addEventListener('resize', resize);

    const particles = [];
    const COUNT = Math.min(800, Math.floor((window.innerWidth * window.innerHeight) / 2000));
    for (let i = 0; i < COUNT; i++) {
      particles.push({
        x: Math.random() * c.width, y: Math.random() * c.height,
        vx: (Math.random() - 0.5) * 0.6, vy: (Math.random() - 0.5) * 0.6,
        r: Math.random() * 2 + 0.5,
        seed: Math.random() * 1000,
      });
    }

    let time = 0;
    function draw() {
      time += 0.016;
      ctx.clearRect(0, 0, c.width, c.height);
      particles.forEach((p) => {
        p.x += p.vx + Math.sin(time * 0.8 + p.seed) * 0.3;
        p.y += p.vy + Math.cos(time * 1.0 + p.seed) * 0.2;
        if (p.x < 0) p.x = c.width;
        if (p.x > c.width) p.x = 0;
        if (p.y < 0) p.y = c.height;
        if (p.y > c.height) p.y = 0;

        const pulse = 0.5 + 0.5 * Math.sin(time * 1.2 + p.seed * 4);
        const alpha = pulse * 0.6;
        const mixVal = (p.x / c.width);
        const r = Math.floor(100 + mixVal * 140);
        const g = Math.floor(100 + (1 - mixVal) * 50);
        const b = Math.floor(240 - mixVal * 90);

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r * (0.8 + pulse * 0.4), 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${r},${g},${b},${alpha})`;
        ctx.fill();
      });
      raf = requestAnimationFrame(draw);
    }
    draw();
    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);

  return (
    <div className="login-page">
      <canvas ref={canvasRef} className="glow-canvas"></canvas>
      <div className="login-wrapper" style={{ display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', position: 'relative', zIndex: 10, padding: '20px' }}>
        <div style={{
          background: 'rgba(15, 23, 42, 0.75)',
          backdropFilter: 'blur(24px)',
          WebkitBackdropFilter: 'blur(24px)',
          border: '1px solid rgba(14, 165, 233, 0.2)',
          boxShadow: '0 8px 32px rgba(2, 132, 199, 0.2)',
          borderRadius: '20px',
          width: '100%',
          maxWidth: '420px',
          padding: '40px 30px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <Activity color="#0ea5e9" size={32} />
            <h1 style={{ margin: 0, color: '#f8fafc', fontSize: '24px', fontWeight: '700', letterSpacing: '1px' }}>DeepScanX</h1>
          </div>
          <p style={{ color: '#94a3b8', fontSize: '14px', marginBottom: '32px', textAlign: 'center' }}>Secure Medical Diagnostic Portal</p>

          <div style={{ width: '100%' }}>
            <Auth
              supabaseClient={supabase}
              appearance={{
                theme: ThemeSupa,
                variables: {
                  default: {
                    colors: {
                      brand: '#0ea5e9',
                      brandAccent: '#0284c7',
                    },
                  },
                },
                style: {
                  container: {
                    width: '100%',
                  },
                  button: {
                    background: 'linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%)',
                    border: 'none',
                    boxShadow: '0 4px 15px rgba(14, 165, 233, 0.3)',
                    color: 'white',
                    borderRadius: '8px',
                    fontWeight: '600',
                    letterSpacing: '0.5px'
                  },
                  input: {
                    background: 'rgba(15, 23, 42, 0.5)',
                    color: '#f8fafc',
                    border: '1px solid rgba(14, 165, 233, 0.3)',
                    borderRadius: '8px',
                  },
                  label: {
                    color: '#cbd5e1',
                    fontWeight: '500'
                  },
                  anchor: {
                    color: '#38bdf8'
                  },
                  dividerText: {
                    color: '#64748b'
                  },
                  message: {
                    color: '#f1f5f9'
                  },
                  container: {
                    width: '100%'
                  }
                }
              }}
              providers={['google']}
              redirectTo={`${window.location.origin}/`}
            />
          </div>
          <style>{`
            .supabase-auth-ui * { color: #f8fafc !important; }
            .supabase-auth-ui input, .supabase-auth-ui select { color: #f8fafc !important; background: rgba(15, 23, 42, 0.5) !important; }
            .supabase-auth-ui button { color: #ffffff !important; }
            .supabase-auth-ui a { color: #38bdf8 !important; }
            .supabase-auth-ui p, .supabase-auth-ui span, .supabase-auth-ui label { color: #cbd5e1 !important; }
            .supabase-auth-ui .message-box { background: rgba(15, 23, 42, 0.7) !important; border: 1px solid rgba(14, 165, 233, 0.2) !important; }
          `}</style>
        </div>
      </div>
    </div>
  );
}
