import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import Layout from './components/Layout';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AboutPage from './pages/AboutPage';
import AuthCallbackPage from './pages/AuthCallbackPage';
import CareLogPage from './pages/CareLogPage';
import ChatPage from './pages/ChatPage';
import DashboardPage from './pages/DashboardPage';
import DeviceOnboardPage from './pages/DeviceOnboardPage';
import DiagnosePage from './pages/DiagnosePage';
import DiseaseMapPage from './pages/DiseaseMapPage';
import EncyclopediaPage, { EncyclopediaDetailPage } from './pages/EncyclopediaPage';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import PlantsPage from './pages/PlantsPage';

const qc = new QueryClient();

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { session, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center text-leaf-700">
        Loading…
      </div>
    );
  }
  if (!session) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <QueryClientProvider client={qc}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/auth/callback" element={<AuthCallbackPage />} />
            <Route
              element={
                <PrivateRoute>
                  <Layout />
                </PrivateRoute>
              }
            >
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/plants" element={<PlantsPage />} />
              <Route path="/diagnose" element={<DiagnosePage />} />
              <Route path="/encyclopedia" element={<EncyclopediaPage />} />
              <Route path="/encyclopedia/:species" element={<EncyclopediaDetailPage />} />
              <Route path="/care-log/:plantId" element={<CareLogPage />} />
              <Route path="/devices/onboard" element={<DeviceOnboardPage />} />
              <Route path="/disease-map" element={<DiseaseMapPage />} />
              <Route path="/chat" element={<ChatPage />} />
              <Route path="/about" element={<AboutPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
