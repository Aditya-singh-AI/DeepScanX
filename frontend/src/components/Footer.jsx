import { Link } from 'react-router-dom';
import './Footer.css';

export default function Footer() {
  return (
    <footer className="footer" id="contact">
      <div className="footer-grid">
        <div className="footer-brand">
          <Link to="/" className="logo" style={{ marginBottom: '.5rem' }}>
            <img
              className="logo-icon"
              src="https://img.freepik.com/premium-photo/black-background-with-pink-orange-logo_978914-26588.jpg"
              alt=""
            />
            <span className="logo-text">DeepScanX AI</span>
          </Link>
          <p>Empowering radiologists with AI-driven insights for accurate cancer detection and improved patient care.</p>
          <div className="footer-socials">
            <a href="#"><i className="fab fa-github"></i></a>
            <a href="#"><i className="fab fa-linkedin"></i></a>
            <a href="#"><i className="fab fa-twitter"></i></a>
          </div>
        </div>
        <div className="footer-col">
          <h4>Platform</h4>
          <Link to="/lung-colon">Lung Detection</Link>
          <Link to="/breast-cancer">Breast Screening</Link>
          <Link to="/brain-tumor">Brain Analysis</Link>
          <Link to="/history">Real-time Reports</Link>
        </div>
        <div className="footer-col">
          <h4>Resources</h4>
          <a href="#">Documentation</a>
          <a href="#">Clinical Studies</a>
          <a href="#">Privacy Policy</a>
          <a href="#">Terms of Service</a>
        </div>
        <div className="footer-col">
          <h4>Development Team</h4>
          <a href="#">Aditya Singh</a>
          <a href="#">Abhishek Mewada</a>
        </div>
      </div>
      <div className="footer-bottom">
        &copy; 2026 DeepScanX AI. All rights reserved. | Built with ❤️ for advancing healthcare
      </div>
    </footer>
  );
}
