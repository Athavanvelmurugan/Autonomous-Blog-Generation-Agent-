import React from 'react';

export function Card({
  children,
  hoverable = false,
  style = {},
  className = '',
  onClick,
  ...props
}) {
  return (
    <div
      onClick={onClick}
      className={className}
      style={{
        background: 'var(--bg-surface)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        boxShadow: 'var(--shadow-sm)',
        transition: 'all var(--transition-fast)',
        cursor: onClick ? 'pointer' : 'default',
        ...(hoverable
          ? {
              ':hover': {
                borderColor: 'var(--border-default)',
                transform: 'translateY(-1px)',
              },
            }
          : {}),
        ...style,
      }}
      onMouseEnter={(e) => {
        if (hoverable || onClick) {
          e.currentTarget.style.borderColor = 'var(--border-default)';
          e.currentTarget.style.background = 'var(--bg-surface-elevated)';
        }
      }}
      onMouseLeave={(e) => {
        if (hoverable || onClick) {
          e.currentTarget.style.borderColor = 'var(--border-subtle)';
          e.currentTarget.style.background = 'var(--bg-surface)';
        }
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({ children, style = {}, ...props }) {
  return (
    <div
      style={{
        padding: 'var(--space-5) var(--space-6)',
        borderBottom: '1px solid var(--border-subtle)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: 'var(--space-3)',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardTitle({ children, style = {}, ...props }) {
  return (
    <h3
      style={{
        fontSize: 'var(--text-lg)',
        fontWeight: 600,
        color: 'var(--text-primary)',
        margin: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-2)',
        ...style,
      }}
      {...props}
    >
      {children}
    </h3>
  );
}

export function CardDescription({ children, style = {}, ...props }) {
  return (
    <p
      style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--text-secondary)',
        margin: 'var(--space-1) 0 0 0',
        ...style,
      }}
      {...props}
    >
      {children}
    </p>
  );
}

export function CardContent({ children, style = {}, ...props }) {
  return (
    <div
      style={{
        padding: 'var(--space-6)',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardFooter({ children, style = {}, ...props }) {
  return (
    <div
      style={{
        padding: 'var(--space-4) var(--space-6)',
        borderTop: '1px solid var(--border-subtle)',
        background: 'rgba(0, 0, 0, 0.15)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: 'var(--space-3)',
        borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
        ...style,
      }}
      {...props}
    >
      {children}
    </div>
  );
}
