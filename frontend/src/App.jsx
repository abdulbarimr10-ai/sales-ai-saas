import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import LeadsManagement from './pages/LeadsManagement';
import AIConfiguration from './pages/AIConfiguration';
import History from './pages/History';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import Sessions from './pages/Sessions';
import Jobs from './pages/Jobs';
import { AppProvider, useAppContext } from './context/AppContext';

function ProtectedRoute({ children }) {
  const { isAuthenticated, isInitializing } = useAppContext();
  
  if (isInitializing) {
    return <div className="min-h-screen flex items-center justify-center bg-background text-primary">Loading...</div>;
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
}

function App() {
  return (
    <AppProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/forgot-password" element={<ForgotPassword />} />
          <Route path="/reset-password" element={<ResetPassword />} />
          <Route path="/verify-email" element={<VerifyEmail />} />
          
          <Route element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/leads" element={<LeadsManagement />} />
            <Route path="/config" element={<AIConfiguration />} />
            <Route path="/settings" element={<AIConfiguration />} />
            <Route path="/history" element={<History />} />
            <Route path="/sessions" element={<Sessions />} />
            <Route path="/jobs" element={<Jobs />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
