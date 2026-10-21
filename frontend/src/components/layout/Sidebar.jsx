import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import {
  LayoutDashboard,
  Sparkles,
  Activity,
  Library,
  Settings,
  ChevronRight,
  ShieldCheck,
} from 'lucide-react';

export default function Sidebar({ isGenerating = false, isOpen = true, onCloseMobile }) {
  const location = useLocation();

  const navItems = [
    {
      to: '/dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
    },
    {
      to: '/generate',
      label: 'Generate Blog',
      icon: Sparkles,
    },
    {
      to: '/pipeline/live',
      label: 'Live Pipeline',
      icon: Activity,
      badge: isGenerating ? 'Active' : null,
      badgeVariant: 'warning',
    },
    {
      to: '/articles',
      label: 'Articles Library',
      icon: Library,
    },
    {
      to: '/settings',
      label: 'System & Config',
      icon: Settings,
    },
  ];

  return (
    <>
      {isOpen && (
        <div
          className="sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}
      <aside
        className={`app-sidebar no-print ${isOpen ? 'sidebar-open' : ''}`}
        aria-label="Sidebar Navigation"
      >
      {/* Brand & App Title */}
      <div
        style={{
          padding: 'var(--space-5) var(--space-6)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-3)',
        }}
      >
        <div
          style={{
            width: '36px',
            height: '36px',
            borderRadius: 'var(--radius-md)',
            background: 'var(--accent-primary)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#ffffff',
            boxShadow: 'var(--shadow-sm)',
            flexShrink: 0,
          }}
        >
          <Sparkles size={20} />
        </div>
        <div style={{ minWidth: 0 }}>
          <h1
            style={{
              fontSize: 'var(--text-base)',
              fontWeight: 700,
              color: 'var(--text-primary)',
              margin: 0,
              letterSpacing: '-0.01em',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}
          >
            BlogEngine AI
          </h1>
          <p
            style={{
              fontSize: 'var(--text-2xs)',
              color: 'var(--text-tertiary)',
              margin: 0,
              fontWeight: 500,
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
            }}
          >
            LangGraph &bull; FastAPI
          </p>
        </div>
      </div>

      {/* Navigation List */}
      <nav style={{ padding: 'var(--space-4) var(--space-3)', flex: 1, display: 'flex', flexDirection: 'column', gap: 'var(--space-1)' }}>
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.to || (item.to !== '/dashboard' && location.pathname.startsWith(item.to));

          return (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onCloseMobile}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: 'var(--space-3) var(--space-4)',
                borderRadius: 'var(--radius-md)',
                color: isActive ? 'var(--text-primary)' : 'var(--text-secondary)',
                background: isActive ? 'var(--bg-surface-elevated)' : 'transparent',
                fontWeight: isActive ? 600 : 500,
                fontSize: 'var(--text-sm)',
                textDecoration: 'none',
                transition: 'all var(--transition-fast)',
                border: isActive ? '1px solid var(--border-default)' : '1px solid transparent',
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'var(--bg-surface-hover)';
                  e.currentTarget.style.color = 'var(--text-primary)';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <Icon size={18} color={isActive ? 'var(--accent-primary-text)' : 'currentColor'} />
                <span>{item.label}</span>
              </div>

              {item.badge && (
                <span
                  style={{
                    fontSize: 'var(--text-2xs)',
                    fontWeight: 700,
                    padding: '2px var(--space-2)',
                    borderRadius: 'var(--radius-full)',
                    background: 'var(--color-warning-bg)',
                    border: '1px solid var(--color-warning-border)',
                    color: 'var(--color-warning-text)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                  }}
                >
                  <span
                    className="animate-pulse-live"
                    style={{
                      width: '6px',
                      height: '6px',
                      borderRadius: '50%',
                      background: 'var(--color-warning)',
                    }}
                  />
                  {item.badge}
                </span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Bottom Info Card */}
      <div style={{ padding: 'var(--space-4)', borderTop: '1px solid var(--border-subtle)' }}>
        <div
          style={{
            background: 'var(--bg-input)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-md)',
            padding: 'var(--space-3)',
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-3)',
          }}
        >
          <ShieldCheck size={20} color="var(--color-success)" style={{ flexShrink: 0 }} />
          <div style={{ minWidth: 0 }}>
            <div style={{ fontSize: 'var(--text-xs)', fontWeight: 600, color: 'var(--text-primary)' }}>
              Verifier Guard
            </div>
            <div style={{ fontSize: 'var(--text-2xs)', color: 'var(--text-tertiary)' }}>
              Self-correcting DAG loop
            </div>
          </div>
        </div>
      </div>
    </aside>
    </>
  );
}
