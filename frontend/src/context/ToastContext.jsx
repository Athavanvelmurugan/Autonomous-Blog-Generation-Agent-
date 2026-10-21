import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const addToast = useCallback((message, type = 'info', duration = 3500) => {
    const id = Date.now() + Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    if (duration > 0) {
      setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, duration);
    }
    return id;
  }, []);

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      {/* Toast Notification Container */}
      <div
        role="region"
        aria-live="polite"
        aria-label="Notifications"
        style={{
          position: 'fixed',
          bottom: 'var(--space-6)',
          right: 'var(--space-6)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
          zIndex: 9999,
          pointerEvents: 'none',
        }}
      >
        {toasts.map((toast) => {
          let bg = 'var(--bg-surface-elevated)';
          let border = 'var(--border-default)';
          let color = 'var(--text-primary)';

          if (toast.type === 'success') {
            bg = 'var(--bg-surface-elevated)';
            border = 'var(--color-success-border)';
            color = 'var(--color-success-text)';
          } else if (toast.type === 'error') {
            bg = 'var(--bg-surface-elevated)';
            border = 'var(--color-danger-border)';
            color = 'var(--color-danger-text)';
          } else if (toast.type === 'warning') {
            bg = 'var(--bg-surface-elevated)';
            border = 'var(--color-warning-border)';
            color = 'var(--color-warning-text)';
          }

          return (
            <div
              key={toast.id}
              className="animate-fade-in"
              style={{
                pointerEvents: 'auto',
                background: bg,
                border: `1px solid ${border}`,
                borderRadius: 'var(--radius-md)',
                padding: 'var(--space-3) var(--space-4)',
                boxShadow: 'var(--shadow-lg)',
                color: color,
                fontSize: 'var(--text-sm)',
                fontWeight: 500,
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-3)',
                maxWidth: '420px',
              }}
            >
              <span style={{ flex: 1, color: 'var(--text-primary)' }}>{toast.message}</span>
              <button
                type="button"
                onClick={() => removeToast(toast.id)}
                aria-label="Dismiss notification"
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: 'var(--text-tertiary)',
                  cursor: 'pointer',
                  fontSize: 'var(--text-base)',
                  display: 'flex',
                  alignItems: 'center',
                  padding: 'var(--space-1)',
                  borderRadius: 'var(--radius-xs)',
                }}
              >
                &times;
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
}
