import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, X } from 'lucide-react';
import './Navbar.css';

export default function Navbar() {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 60);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  useEffect(() => { setMobileOpen(false); }, [location]);

  const isHome = location.pathname === '/';

  return (
    <nav className={`nav-wrap${scrolled ? ' scrolled' : ''}`}>
      <div className="nav-inner">
        <Link to="/" className="logo">
          <img
            className="logo-icon"
            src="https://img.freepik.com/premium-photo/black-background-with-pink-orange-logo_978914-26588.jpg"
            alt="DeepScanX"
          />
          <span className="logo-text">DeepScanX AI</span>
        </Link>

        <ul className={`nav-links${mobileOpen ? ' open' : ''}`}>
          {isHome ? (
            <>
              <li><a href="#about">About</a></li>
              <li><a href="#features">Features</a></li>
              <li><a href="#how-it-works">How It Works</a></li>
              <li><a href="#why-us">Why Us</a></li>
            </>
          ) : (
            <>
              <li><Link to="/">Dashboard</Link></li>
              <li><Link to="/history">History</Link></li>
              <li><Link to="/patients">Patients</Link></li>
              <li><Link to="/chatbot">AI Chat</Link></li>
            </>
          )}
          {user && (
            <>
              {isHome && <li><Link to="/history">📋 History</Link></li>}
              {isHome && <li><Link to="/chatbot">🩺 AI Assistant</Link></li>}
              {user.role === 'admin' && (
                <li><Link to="/admin" style={{ color: '#ffd32a' }}>🛡️ Admin</Link></li>
              )}
            </>
          )}
        </ul>

        <div className="nav-cta">
          {user ? (
            <>
              <button className="btn-ghost" onClick={logout}>Logout</button>
              <Link to="/lung-colon" className="btn-primary"><span>Start Scan</span></Link>
            </>
          ) : (
            <>
              <Link to="/login" className="btn-ghost">Sign In</Link>
              <Link to="/signup" className="btn-primary"><span>Get Started</span></Link>
            </>
          )}
        </div>

        <button className="mobile-toggle" onClick={() => setMobileOpen(!mobileOpen)}>
          {mobileOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>
    </nav>
  );
}
