import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

// Pages
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';
import Signup from './pages/Signup';
import VerifyEmail from './pages/VerifyEmail';
import History from './pages/History';
import Chatbot from './pages/Chatbot';

// Scanners
import DiagnosticHub from './pages/DiagnosticHub';
import LungColon from './pages/LungColon';
import BreastCancer from './pages/BreastCancer';
import BrainTumor from './pages/BrainTumor';
import SkinCancer from './pages/SkinCancer';
import ChestXRay from './pages/ChestXRay';
import DiabeticRetinopathy from './pages/DiabeticRetinopathy';
import WSIViewer from './pages/WSIViewer';

// Clinical
import PatientList from './pages/PatientList';
import PatientDetail from './pages/PatientDetail';
import SecondOpinion from './pages/SecondOpinion';
import Review from './pages/Review';

// Admin
import AdminDashboard from './pages/AdminDashboard';

import './styles/global.css';

function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: 'var(--gray)' }}>Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return children;
}

function AdminRoute({ children }) {
  const { user, loading } = useAuth();
  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', color: 'var(--gray)' }}>Loading...</div>;
  if (!user || user.role !== 'admin') return <Navigate to="/" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public */}
      <Route path="/" element={<><Navbar /><Dashboard /><Footer /></>} />
      <Route path="/login" element={<Login />} />
      <Route path="/signup" element={<Signup />} />
      <Route path="/verify-email" element={<VerifyEmail />} />

      {/* Auth-protected */}
      <Route path="/history" element={<ProtectedRoute><Navbar /><History /><Footer /></ProtectedRoute>} />
      <Route path="/chatbot" element={<ProtectedRoute><Navbar /><Chatbot /></ProtectedRoute>} />

      {/* Scanners (Unified Hub) */}
      <Route element={<ProtectedRoute><Navbar /><DiagnosticHub /><Footer /></ProtectedRoute>}>
        <Route path="/lung-colon" element={<LungColon />} />
        <Route path="/breast-cancer" element={<BreastCancer />} />
        <Route path="/brain-tumor" element={<BrainTumor />} />
        <Route path="/skin-cancer" element={<SkinCancer />} />
        <Route path="/chest-xray" element={<ChestXRay />} />
        <Route path="/diabetic-retinopathy" element={<DiabeticRetinopathy />} />
        <Route path="/wsi-viewer" element={<WSIViewer />} />
      </Route>

      {/* Clinical */}
      <Route path="/patients" element={<ProtectedRoute><Navbar /><PatientList /><Footer /></ProtectedRoute>} />
      <Route path="/patients/:id" element={<ProtectedRoute><Navbar /><PatientDetail /><Footer /></ProtectedRoute>} />
      <Route path="/second-opinions" element={<ProtectedRoute><Navbar /><SecondOpinion /><Footer /></ProtectedRoute>} />
      <Route path="/review/:token" element={<><Navbar /><Review /><Footer /></>} />

      {/* Admin */}
      <Route path="/admin" element={<AdminRoute><Navbar /><AdminDashboard /><Footer /></AdminRoute>} />

      {/* Catch-all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
}
