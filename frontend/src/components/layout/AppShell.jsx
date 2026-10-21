import React, { useState, useEffect } from 'react';
import { Outlet, useLocation, useNavigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import { checkHealth } from '../../services/api';
import Button from '../common/Button';
import Badge from '../common/Badge';
import { Menu, X, Sparkles, Database, Cpu, CheckCircle2, AlertTriangle, Sun, Moon, BookOpen } from 'lucide-react';
import { useGeneration } from '../../context/GenerationContext';
import { useTheme } from '../../context/ThemeContext';

export default function AppShell() {
  const location = useLocation();
  const navigate = useNavigate();
  const { isGenerating } = useGeneration();
  const { theme, setTheme } = useTheme();

  const [serverStatus, setServerStatus] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    const loadStatus = async () => {
      try {
        const data = await checkHealth();
        if (isMounted) setServerStatus(data);
      } catch (err) {
        if (isMounted) setServerStatus({ status: 'error', message: err.message });
      }
    };
    loadStatus();
    return () => { isMounted = false; };
  }, []);

  // Compute page title based on path
  const getPageInfo = () => {
    const path = location.pathname;
    if (path === '/dashboard') return { title: 'Dashboard Overview', desc: 'System metrics and recent publications' };
    if (path === '/generate') return { title: 'Generate Blog', desc: 'Configure topic, tone, and autonomous agents' };
    if (path.startsWith('/pipeline')) return { title: 'Live Agent Pipeline', desc: 'Real-time multi-agent execution telemetry' };
    if (path === '/articles') return { title: 'Articles Library', desc: 'Browse and manage PostgreSQL blog archive' };
    if (path.includes('/audit')) return { title: 'Fact-Check & Quality Audit', desc: 'Deep-dive verifier analysis and citations' };
    if (path.startsWith('/articles/')) return { title: 'Article Studio & Reader', desc: 'Full-length reading and markdown export' };
    if (path === '/settings') return { title: 'System Configuration', desc: 'FastAPI engine, PostgreSQL, and LLM diagnostics' };
    return { title: 'Autonomous Blog Engine', desc: 'LangGraph & FastAPI' };
  };

  // Close mobile drawer on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const pageInfo = getPageInfo();

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg-canvas)' }}>
      {/* Responsive Sidebar */}
      <Sidebar
        isGenerating={isGenerating}
        isOpen={mobileMenuOpen}
        onCloseMobile={() => setMobileMenuOpen(false)}
      />

      {/* Main Container Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        {/* Top Header Bar */}
        <header
          className="app-header no-print"
          style={{
            height: '64px',
            background: 'var(--bg-surface)',
            borderBottom: '1px solid var(--border-subtle)',
            padding: '0 var(--space-8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 40,
          }}
        >
          {/* Breadcrumb / Page Title + Mobile Menu Trigger */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            <button
              type="button"
              className="mobile-only"
              onClick={() => setMobileMenuOpen((prev) => !prev)}
              aria-label={mobileMenuOpen ? 'Close Navigation Menu' : 'Open Navigation Menu'}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-primary)',
                cursor: 'pointer',
                padding: 'var(--space-1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              {mobileMenuOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
            <div>
              <h2 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--text-primary)', margin: 0 }}>
                {pageInfo.title}
              </h2>
              <p className="hide-on-mobile" style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)', margin: 0 }}>
                {pageInfo.desc}
              </p>
            </div>
          </div>

          {/* Right Header Controls */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
            {/* Theme Selector Pill */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                background: 'var(--bg-surface-elevated)',
                border: '1px solid var(--border-default)',
                borderRadius: 'var(--radius-full)',
                padding: '2px',
                gap: '2px',
              }}
              role="radiogroup"
              aria-label="Theme Selection"
            >
              <button
                type="button"
                onClick={() => setTheme('light')}
                title="Light Theme (Warm Paper)"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: 'none',
                  background: theme === 'light' ? 'var(--bg-surface)' : 'transparent',
                  color: theme === 'light' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-2xs)',
                  fontWeight: 600,
                  boxShadow: theme === 'light' ? 'var(--shadow-sm)' : 'none',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <Sun size={13} />
                <span>Light</span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('sepia')}
                title="Sepia Theme (Parchment)"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: 'none',
                  background: theme === 'sepia' ? 'var(--bg-surface)' : 'transparent',
                  color: theme === 'sepia' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-2xs)',
                  fontWeight: 600,
                  boxShadow: theme === 'sepia' ? 'var(--shadow-sm)' : 'none',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <BookOpen size={13} />
                <span>Sepia</span>
              </button>

              <button
                type="button"
                onClick={() => setTheme('dark')}
                title="Dark Theme (Ink Slate)"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px',
                  padding: '4px 8px',
                  borderRadius: 'var(--radius-full)',
                  border: 'none',
                  background: theme === 'dark' ? 'var(--bg-surface)' : 'transparent',
                  color: theme === 'dark' ? 'var(--text-primary)' : 'var(--text-tertiary)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-2xs)',
                  fontWeight: 600,
                  boxShadow: theme === 'dark' ? 'var(--shadow-sm)' : 'none',
                  transition: 'all var(--transition-fast)',
                }}
              >
                <Moon size={13} />
                <span>Dark</span>
              </button>
            </div>

            {/* Database indicator */}
            <span className="hide-on-mobile">
              <Badge variant="neutral" icon={Database}>
                blog_db
              </Badge>
            </span>

            {/* LLM Model indicator */}
            <span className="hide-on-mobile">
              <Badge variant="neutral" icon={Cpu}>
                {serverStatus?.model_name ? serverStatus.model_name.split('/').pop() : 'Llama 3.3'}
              </Badge>
            </span>

            {/* Health status indicator */}
            <span className="hide-on-mobile">
              <Badge
                variant={serverStatus?.status === 'healthy' ? 'success' : 'danger'}
                icon={serverStatus?.status === 'healthy' ? CheckCircle2 : AlertTriangle}
              >
                {serverStatus?.status === 'healthy' ? 'FastAPI Online' : 'Offline'}
              </Badge>
            </span>

            {/* Quick Action: New Generation (only if not on /generate already) */}
            {location.pathname !== '/generate' && (
              <Button
                variant="primary"
                size="sm"
                leftIcon={Sparkles}
                onClick={() => navigate('/generate')}
              >
                New Article
              </Button>
            )}
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="app-main" style={{ flex: 1, padding: 'var(--space-8)', overflowY: 'auto' }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
