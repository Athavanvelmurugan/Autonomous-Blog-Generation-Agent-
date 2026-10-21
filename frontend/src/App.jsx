import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ToastProvider } from './context/ToastContext';
import { GenerationProvider } from './context/GenerationContext';
import { ThemeProvider } from './context/ThemeContext';
import ErrorBoundary from './components/common/ErrorBoundary';
import AppShell from './components/layout/AppShell';

import DashboardPage from './pages/DashboardPage';
import GeneratePage from './pages/GeneratePage';
import LivePipelinePage from './pages/LivePipelinePage';
import ArticlesPage from './pages/ArticlesPage';
import ArticleDetailPage from './pages/ArticleDetailPage';
import QualityAuditPage from './pages/QualityAuditPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <GenerationProvider>
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<AppShell />}>
                <Route index element={<Navigate to="/dashboard" replace />} />
                <Route path="dashboard" element={<DashboardPage />} />
                <Route path="generate" element={<GeneratePage />} />
                <Route path="pipeline/live" element={<LivePipelinePage />} />
                <Route path="articles" element={<ArticlesPage />} />
                <Route path="articles/:id" element={<ArticleDetailPage />} />
                <Route path="articles/:id/audit" element={<QualityAuditPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="*" element={<Navigate to="/dashboard" replace />} />
              </Route>
            </Routes>
          </ErrorBoundary>
        </GenerationProvider>
    </ToastProvider>
  </ThemeProvider>
  );
}
