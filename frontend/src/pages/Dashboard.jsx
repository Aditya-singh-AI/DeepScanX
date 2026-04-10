import { useEffect, useRef, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import './Dashboard.css';

const SCAN_CHIPS = [
  { icon: 'fas fa-lungs', label: 'Lung Cancer Detection' },
  { icon: 'fas fa-heartbeat', label: 'Breast IDC Screening' },
  { icon: 'fas fa-brain', label: 'Brain Tumor Analysis' },
  { icon: 'fas fa-fingerprint', label: 'Skin Cancer' },
  { icon: 'fas fa-x-ray', label: 'Chest X-Ray' },
  { icon: 'fas fa-eye', label: 'Diabetic Retinopathy' },
];

const FEATURE_ROWS = [
  { icon: 'fas fa-eye', title: 'Explainable AI with Grad-CAM', desc: 'Visual heatmaps highlight the exact tissue regions that drive each prediction — no black box decisions.' },
  { icon: 'fas fa-chart-bar', title: 'Probability Distribution Reports', desc: 'Every scan returns a full class probability breakdown with confidence scoring and downloadable PDF reports.' },
  { icon: 'fas fa-shield-halved', title: 'Secure & HIPAA-Aligned', desc: 'User-isolated prediction history, JWT-secured sessions, and encrypted data handling throughout.' },
  { icon: 'fas fa-brain', title: 'Multi-Modal Detection', desc: 'Unified pipeline for lung, breast IDC, and brain tumor analysis across different imaging modalities.' },
];

const BENTO_FEATURES = [
  { icon: 'fas fa-lungs', title: 'Lung Cancer Detection', desc: 'Advanced CNN algorithms analyze CT scans and histopathology slides to identify early-stage lung cancer with high precision. Our model achieves 97%+ accuracy on validated datasets, helping radiologists catch what the human eye might miss.', span: true },
  { icon: 'fas fa-heart-pulse', title: 'Breast Cancer Screening', desc: 'Automated IDC detection in histopathology images with detailed probability heatmaps and Grad-CAM overlays.' },
  { icon: 'fas fa-brain', title: 'Brain Tumor Analysis', desc: 'Deep learning classification of brain MRI scans for tumor detection and grading.' },
  { icon: 'fas fa-chart-line', title: 'Real-time Analytics & Reports', desc: 'Instant processing with detailed diagnostic reports, confidence scores, probability distributions, and downloadable clinical PDFs. Every analysis includes Grad-CAM visualizations for full explainability.', span: true },
  { icon: 'fas fa-database', title: 'Secure Data Management', desc: 'HIPAA-compliant storage with encrypted transmission, JWT-secured sessions, and user-isolated data.' },
  { icon: 'fas fa-clock', title: 'Historical Comparison', desc: 'Track and compare predictions over time with full scan history and trend analysis.' },
  { icon: 'fas fa-user-doctor', title: 'Clinical Collaboration', desc: 'Share reports, get second opinions, and collaborate with annotations.' },
];

const STEPS = [
  { icon: 'fas fa-cloud-upload-alt', title: 'Upload Scan', desc: 'Upload CT, MRI or histopathology images in standard formats.' },
  { icon: 'fas fa-microchip', title: 'AI Processing', desc: 'Our CNN models analyze the image across multiple trained pathways.' },
  { icon: 'fas fa-chart-pie', title: 'Get Results', desc: 'Receive confidence scores, probability maps, and Grad-CAM overlays.' },
  { icon: 'fas fa-file-pdf', title: 'Download Report', desc: 'Export a clinical-grade PDF report for records or second opinions.' },
];

const WHY_US = [
  { num: '75%', desc: 'Projected increase in cancer deaths by 2050 — over 18M annually worldwide.' },
  { num: '90%+', desc: 'Survival rate when cancer is detected early, compared to <30% at late stages.' },
  { num: '50%', desc: 'Reduction in diagnostic time, enabling faster treatment decisions.' },
  { num: '24/7', desc: 'Consistent AI analysis regardless of time, fatigue, or case complexity.' },
  { num: '97%', desc: 'Model accuracy on validated lung cancer histopathology datasets.' },
  { num: '1.57M', desc: 'Estimated new cancer cases in India by 2025 — early detection is critical.' },
];

const SCANNERS = [
  { to: '/lung-colon', icon: 'fas fa-lungs', title: 'Lung & Colon', desc: '5-class histopathological analysis for lung and colon tissue classification.', color: null },
  { to: '/breast-cancer', icon: 'fas fa-heart-pulse', title: 'Breast Cancer (IDC)', desc: 'Binary classification of Invasive Ductal Carcinoma in histopathology images.', color: null },
  { to: '/brain-tumor', icon: 'fas fa-brain', title: 'Brain Tumor', desc: 'MRI-based brain tumor detection and classification using deep learning.', color: null },
  { to: '/skin-cancer', icon: 'fas fa-fingerprint', title: 'Skin Cancer', desc: 'Dermoscopy image analysis for benign vs. malignant melanoma detection.', color: '#e91e63', isNew: true },
  { to: '/chest-xray', icon: 'fas fa-x-ray', title: 'Chest X-Ray', desc: 'Detect Pneumonia, COVID-19, and Tuberculosis from standard X-ray images.', color: '#2196f3', isNew: true },
  { to: '/diabetic-retinopathy', icon: 'fas fa-eye', title: 'Diabetic Retinopathy', desc: 'Fundus image analysis for 5-level diabetic retinopathy severity classification.', color: '#4caf50', isNew: true },
  { to: '/wsi-viewer', icon: 'fas fa-search-plus', title: 'WSI Viewer', desc: 'High-resolution whole slide image viewer with click-to-analyze AI patches.', color: '#ff9800', isNew: true },
  { to: '/patients', icon: 'fas fa-users', title: 'Patient Management', desc: 'Create patient profiles and track diagnostic history over time.', color: '#a78bfa', isNew: true },
  { to: '/second-opinions', icon: 'fas fa-user-md', title: 'Second Opinions', desc: 'Request and review peer opinions on AI diagnostic predictions.', color: '#ffd32a', isNew: true },
];

const STATS = [
  { target: 97, suffix: '%', label: 'Model Accuracy' },
  { target: 3, suffix: '+', label: 'Cancer Types' },
  { target: 50, suffix: '%', label: 'Faster Analysis' },
  { target: 24, suffix: '/7', label: 'AI Availability' },
  { target: 10, suffix: 'K+', label: 'Images Trained' },
  { target: 100, suffix: '%', label: 'HIPAA Compliant' },
];

export default function Dashboard() {
  const { user } = useAuth();
  const particleRef = useRef(null);
  const heroRef = useRef(null);

  // Scroll reveal
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e, idx) => {
        if (e.isIntersecting) {
          setTimeout(() => e.target.classList.add('visible'), idx * 80);
          io.unobserve(e.target);
        }
      }),
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );
    document.querySelectorAll('.reveal,.reveal-left,.reveal-right').forEach(el => io.observe(el));
    return () => io.disconnect();
  }, []);

  // Counter animation
  useEffect(() => {
    const cio = new IntersectionObserver(entries => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.querySelectorAll('[data-target]').forEach(n => {
            const t = +n.dataset.target;
            let c = 0;
            const inc = t / 60;
            const timer = setInterval(() => {
              c += inc;
              if (c >= t) { n.textContent = t; clearInterval(timer); }
              else n.textContent = Math.floor(c);
            }, 25);
          });
          cio.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });
    const sb = document.querySelector('.stats-band');
    if (sb) cio.observe(sb);
    return () => cio.disconnect();
  }, []);

  // Bento card mouse glow
  const handleBentoMouseMove = useCallback((e) => {
    const card = e.currentTarget;
    const r = card.getBoundingClientRect();
    card.style.setProperty('--mouse-x', e.clientX - r.left + 'px');
    card.style.setProperty('--mouse-y', e.clientY - r.top + 'px');
  }, []);

  // Particle canvas
  useEffect(() => {
    const c = particleRef.current;
    if (!c) return;
    const ctx = c.getContext('2d');
    const parent = c.parentElement;

    function resize() { c.width = parent.offsetWidth; c.height = parent.offsetHeight; }
    resize();
    window.addEventListener('resize', resize);

    const P = [];
    for (let i = 0; i < 80; i++) {
      P.push({
        x: Math.random() * c.width, y: Math.random() * c.height,
        vx: (Math.random() - .5) * .4, vy: (Math.random() - .5) * .4,
        r: Math.random() * 1.5 + .5
      });
    }

    let raf;
    function draw() {
      ctx.clearRect(0, 0, c.width, c.height);
      P.forEach((p, i) => {
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > c.width) p.vx *= -1;
        if (p.y < 0 || p.y > c.height) p.vy *= -1;
        ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(220,20,60,0.5)'; ctx.fill();
        for (let j = i + 1; j < P.length; j++) {
          const dx = P[j].x - p.x, dy = P[j].y - p.y, d = Math.sqrt(dx * dx + dy * dy);
          if (d < 120) {
            ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(P[j].x, P[j].y);
            ctx.strokeStyle = `rgba(220,20,60,${.15 * (1 - d / 120)})`;
            ctx.lineWidth = .5; ctx.stroke();
          }
        }
      });
      raf = requestAnimationFrame(draw);
    }
    draw();

    return () => { cancelAnimationFrame(raf); window.removeEventListener('resize', resize); };
  }, []);

  // Typewriter
  useEffect(() => {
    const el = document.getElementById('typeTarget');
    if (!el) return;
    const text = 'DeepScanX AI';
    let i = 0, del = false, timeout;
    function tick() {
      if (!del) {
        el.textContent = text.slice(0, ++i);
        if (i === text.length) { del = true; timeout = setTimeout(tick, 2200); return; }
        timeout = setTimeout(tick, 100);
      } else {
        el.textContent = text.slice(0, --i);
        if (i === 0) { del = false; timeout = setTimeout(tick, 500); return; }
        timeout = setTimeout(tick, 55);
      }
    }
    timeout = setTimeout(tick, 600);
    return () => clearTimeout(timeout);
  }, []);

  // Scroll progress
  useEffect(() => {
    const prog = document.getElementById('scroll-progress');
    if (!prog) return;
    const onScroll = () => {
      const h = document.documentElement;
      prog.style.width = ((h.scrollTop) / (h.scrollHeight - h.clientHeight) * 100) + '%';
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <>
      <div id="scroll-progress"></div>

      {/* ═══ HERO ═══ */}
      <section className="hero" id="hero" ref={heroRef}>
        <div className="hero-bg-mesh">
          <div className="orb orb-1"></div>
          <div className="orb orb-2"></div>
          <div className="orb orb-3"></div>
        </div>
        <canvas ref={particleRef} style={{ position: 'absolute', inset: 0, zIndex: 1, pointerEvents: 'none' }}></canvas>
        <div className="hero-content">
          <div className="hero-badge reveal"><span className="pulse-dot"></span> AI-Powered · Research Grade · Multi-Modal</div>
          <h1 className="reveal">
            <span className="white" id="typeTarget"></span>
            <span className="tw-cursor">|</span>
          </h1>
          <p className="hero-desc reveal">
            A next-generation cancer detection platform combining deep learning with
            histopathology analysis — built for radiologists, researchers, and diagnosticians.
          </p>
          <p className="hero-sub reveal">
            <span>Lung Cancer</span> · <span>Breast Cancer (IDC)</span> · <span>Brain Tumors</span> · <span>Skin Cancer</span> · <span>Chest X-Ray</span> · <span>Diabetic Retinopathy</span> — All in one platform.
          </p>
          <div className="hero-actions reveal">
            <Link to="/lung-colon" className="btn-primary" style={{ padding: '.8rem 2.2rem', fontSize: '1rem' }}>
              <span><i className="fas fa-microscope"></i>&nbsp; Start Diagnosis</span>
            </Link>
            <a href="#features" className="btn-outline"><i className="fas fa-play"></i> Explore Features</a>
          </div>
          <div className="scan-chips reveal">
            {SCAN_CHIPS.map((c, i) => (
              <div className="scan-chip" key={i}>
                <span className="chip-dot"></span>
                <i className={`${c.icon} chip-icon`}></i>
                <h4>{c.label}</h4>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ STATS MARQUEE ═══ */}
      <div className="stats-band">
        <div className="stats-track">
          {[...STATS, ...STATS].map((s, i) => (
            <div className="stat-pill" key={i}>
              <span className="num" data-target={i < STATS.length ? s.target : undefined}>
                {i < STATS.length ? 0 : s.target}
              </span>
              <span className="suffix">{s.suffix}</span>
              <span className="label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* ═══ ABOUT ═══ */}
      <section className="section" id="about" style={{ background: 'var(--bg2)' }}>
        <div className="section-inner">
          <div className="about-split">
            <div className="reveal-left">
              <div className="section-tag"><i className="fas fa-dna"></i> About the Platform</div>
              <h2 className="section-title">Built for precision.<br /><span className="accent">Made for tomorrow.</span></h2>
              <p className="section-desc" style={{ marginBottom: '1.5rem' }}>
                DeepScanX AI is an advanced multi-modal cancer detection system that harnesses the power of convolutional neural networks trained on thousands of histopathological images.
              </p>
              <p className="section-desc" style={{ marginBottom: '1.5rem' }}>
                Our platform delivers consistent, explainable AI-driven predictions with Grad-CAM visualizations — giving clinicians and researchers a clear window into what the model sees.
              </p>
              <p className="section-desc" style={{ marginBottom: '2rem' }}>
                Every prediction is research-grade: confidence-scored, probability-mapped, and downloadable as a clinical PDF report.
              </p>
              <Link to="/lung-colon" className="btn-primary">
                <span><i className="fas fa-arrow-right"></i>&nbsp; Try the Scanner</span>
              </Link>
            </div>
            <div className="about-right reveal-right">
              {FEATURE_ROWS.map((f, i) => (
                <div className="feat-row" key={i}>
                  <div className="icon-box"><i className={f.icon}></i></div>
                  <div>
                    <h4>{f.title}</h4>
                    <p>{f.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ═══ FEATURES BENTO ═══ */}
      <section className="section" id="features">
        <div className="section-inner">
          <div style={{ textAlign: 'center', marginBottom: '4rem' }} className="reveal">
            <div className="section-tag" style={{ margin: '0 auto 1.5rem' }}><i className="fas fa-sparkles"></i> Core Capabilities</div>
            <h2 className="section-title">Advanced AI-Powered <span className="accent">Features</span></h2>
            <p className="section-desc" style={{ margin: '0 auto' }}>Comprehensive tools designed to enhance radiological diagnosis and patient care.</p>
          </div>
          <div className="bento">
            {BENTO_FEATURES.map((f, i) => (
              <div className={`bento-card${f.span ? ' span-2' : ''} reveal`} key={i} onMouseMove={handleBentoMouseMove}>
                <div className="bento-icon"><i className={f.icon}></i></div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ HOW IT WORKS ═══ */}
      <section className="section" id="how-it-works" style={{ background: 'var(--bg2)' }}>
        <div className="section-inner">
          <div style={{ textAlign: 'center', marginBottom: '2rem' }} className="reveal">
            <div className="section-tag" style={{ margin: '0 auto 1.5rem' }}><i className="fas fa-route"></i> Workflow</div>
            <h2 className="section-title">How <span className="accent">DeepScanX</span> Works</h2>
            <p className="section-desc" style={{ margin: '0 auto' }}>From upload to diagnosis in under 60 seconds.</p>
          </div>
          <div className="steps-grid">
            {STEPS.map((s, i) => (
              <div className="step-card reveal" key={i}>
                <div className="step-icon"><i className={s.icon}></i></div>
                <h4>{s.title}</h4>
                <p>{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ WHY US ═══ */}
      <section className="section" id="why-us">
        <div className="section-inner">
          <div style={{ textAlign: 'center', marginBottom: '2rem' }} className="reveal">
            <div className="section-tag" style={{ margin: '0 auto 1.5rem' }}><i className="fas fa-bolt"></i> Impact</div>
            <h2 className="section-title">Why DeepScanX AI <span className="accent">Matters</span></h2>
            <p className="section-desc" style={{ margin: '0 auto' }}>Addressing critical challenges in modern radiology and cancer diagnosis.</p>
          </div>
          <div className="why-grid">
            {WHY_US.map((w, i) => (
              <div className="why-card reveal" key={i}>
                <h4>{w.num}</h4>
                <p>{w.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ═══ DIAGNOSTIC HUB ═══ (auth only) */}
      {user && (
        <section className="section" id="scanners" style={{ background: 'var(--bg2)' }}>
          <div className="section-inner">
            <div style={{ textAlign: 'center', marginBottom: '3rem' }} className="reveal">
              <div className="section-tag" style={{ margin: '0 auto 1.5rem' }}><i className="fas fa-microscope"></i> Diagnostic Hub</div>
              <h2 className="section-title">Launch a <span className="accent">Scanner</span></h2>
              <p className="section-desc" style={{ margin: '0 auto' }}>Choose a diagnostic module below to start AI-powered analysis.</p>
            </div>
            <div className="bento" style={{ gridTemplateColumns: 'repeat(3, 1fr)' }}>
              {SCANNERS.map((s, i) => (
                <Link to={s.to} className="bento-card reveal" key={i} style={{ textDecoration: 'none', color: 'inherit', cursor: 'pointer' }} onMouseMove={handleBentoMouseMove}>
                  <div className="bento-icon" style={s.color ? { color: s.color } : {}}>
                    <i className={s.icon}></i>
                  </div>
                  <h3>{s.title}</h3>
                  <p>{s.desc}</p>
                  {s.isNew && (
                    <span style={{
                      fontSize: '.65rem', padding: '.15rem .6rem',
                      background: s.color ? `${s.color}26` : 'rgba(220,20,60,.15)',
                      color: s.color || 'var(--crimson)',
                      borderRadius: '20px', marginTop: '.5rem', display: 'inline-block'
                    }}>NEW</span>
                  )}
                </Link>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ═══ CTA ═══ */}
      <section className="cta-section" id="get-started">
        <div className="cta-inner reveal">
          <h2>Transform Cancer Diagnosis<br />with <span style={{ color: 'var(--crimson-l)' }}>Artificial Intelligence</span></h2>
          <p>Join the next generation of AI-enhanced radiology. Start detecting cancers earlier, faster, and more accurately.</p>
          <Link to="/lung-colon" className="btn-primary" style={{ padding: '.85rem 2.5rem', fontSize: '1rem' }}>
            <span><i className="fas fa-microscope"></i>&nbsp; Start Scanning Now</span>
          </Link>
        </div>
      </section>

      {/* Chatbot FAB */}
      <Link to="/chatbot" className="chat-fab" title="DeepScanX Clinical Assistant">🩺</Link>
    </>
  );
}
