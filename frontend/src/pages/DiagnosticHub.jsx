import { Outlet, NavLink, useLocation } from 'react-router-dom';
import './DiagnosticHub.css';
import { useEffect } from 'react';

const SCANNERS = [
  { to: '/lung-colon', icon: 'fas fa-lungs', label: 'Lung & Colon' },
  { to: '/breast-cancer', icon: 'fas fa-heart-pulse', label: 'Breast Cancer' },
  { to: '/brain-tumor', icon: 'fas fa-brain', label: 'Brain Tumor' },
  { to: '/skin-cancer', icon: 'fas fa-fingerprint', label: 'Skin Cancer' },
  { to: '/chest-xray', icon: 'fas fa-x-ray', label: 'Chest X-Ray' },
  { to: '/diabetic-retinopathy', icon: 'fas fa-eye', label: 'Retinopathy' },
  { to: '/wsi-viewer', icon: 'fas fa-search-plus', label: 'WSI Viewer' },
];

export default function DiagnosticHub() {
  const location = useLocation();

  // Scroll to top when switching tabs for a clean experience
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [location.pathname]);

  return (
    <div className="hub-layout">
      {/* Top Tab Bar Navigation */}
      <div className="hub-topbar-wrapper">
        <div className="hub-topbar content-width">
          <div className="hub-tabs">
            {SCANNERS.map((s, i) => (
              <NavLink to={s.to} className={({ isActive }) => `hub-tab ${isActive ? 'active' : ''}`} key={i}>
                <i className={s.icon}></i>
                <span>{s.label}</span>
              </NavLink>
            ))}
          </div>
        </div>
      </div>

      {/* Main Scanner Component */}
      <div className="hub-main-content">
        <Outlet />
      </div>
    </div>
  );
}
